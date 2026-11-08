"""Authorize formulas from question, linkbase, registry, then disclosure text."""
from __future__ import annotations
from dataclasses import replace
import ast
import re
import sympy
from verifiqa.agent.types import RoleSpec
from verifiqa.formulas.evaluator import formula_variables
from verifiqa.policy.registry import DEFAULT_POLICY_REGISTRY as REGISTRY
from verifiqa.types import VerificationFact, VerificationIR
from verifiqa.verification.generic_ops import resolve_generic_operation, classify_operation
from verifiqa.verification.policy_formula import _resolve_roles, _substitute_template, _identifiers
from .grounding import Unresolved, tokens,unit
from .semantics import role_measure,question_equation

def structural_ir(spec, extracted,filing):
    # Dummy values deliberately prevent arithmetic or candidate values from selecting authority.
    facts = {r.name: VerificationFact(name=r.name, value=1, unit=role_measure(r,spec.claim_unit,filing,extracted.get(r.name)),
             period=r.period or spec.period, row_label=(extracted[r.name].row_label if extracted.get(r.name) else (r.aliases[0] if r.aliases else r.name))) for r in spec.roles}
    return VerificationIR(metric=spec.metric, formula=spec.formula, facts=facts, claimed_value=0,
                          claim_unit=spec.claim_unit, computed_unit=spec.claim_unit, period=spec.period, tolerance=0)

def signature(formula):
    from .solver import formula_names
    names = formula_names(formula)
    symbols = {x: sympy.Symbol(x) for x in names}
    def walk(n):
        if isinstance(n,ast.Name):return symbols[n.id]
        if isinstance(n,ast.Constant):return sympy.Rational(str(n.value))
        if isinstance(n,ast.UnaryOp):return -walk(n.operand) if isinstance(n.op,ast.USub) else walk(n.operand)
        if isinstance(n,ast.BinOp):
            a,b=walk(n.left),walk(n.right)
            if isinstance(n.op,ast.Add):return a+b
            if isinstance(n.op,ast.Sub):return a-b
            if isinstance(n.op,ast.Mult):return a*b
            if isinstance(n.op,ast.Div):return a/b
            return a**b
        funcs={'abs':sympy.Abs,'min':sympy.Min,'max':sympy.Max}
        return funcs.get(n.func.id,sympy.Function(n.func.id))(*[walk(a) for a in n.args])
    return str(sympy.cancel(walk(ast.parse(formula,mode='eval').body)))

def without_redundant_display_scaling(candidates,output_unit):
    kind,_=unit(output_unit)
    if kind in {'pure','shares'}:return candidates
    # Runtime binds monetary operands in output units. A source template that
    # only wraps another allowed template in a thousands/millions conversion
    # would apply the same display conversion twice.
    allowed={signature(f) for f,_ in candidates}
    kept=[]
    for formula,template in candidates:
        node=ast.parse(formula,mode='eval').body
        inner=None
        if isinstance(node,ast.BinOp) and isinstance(node.op,(ast.Div,ast.Mult)):
            if isinstance(node.right,ast.Constant) and node.right.value in {1000,1000000,1000000000,.001,.000001,.000000001}:
                inner=node.left
            elif isinstance(node.op,ast.Mult) and isinstance(node.left,ast.Constant) and node.left.value in {1000,1000000,1000000000,.001,.000001,.000000001}:
                inner=node.right
        if inner is not None and signature(ast.unparse(inner)) in allowed:continue
        kept.append((formula,template))
    return kept

def authorize(spec, question, evidence, filing, extracted):
    ir = structural_ir(spec, extracted,filing)
    # §3.4 precedence: explicit operation > linkbase > registry > disclosure.
    equation=question_equation(question,spec)
    if equation:
        return replace(spec,formula=equation,formula_source='generic_operation'),{
            'kind':'question_definition','source_id':'explicit_question_equation',
            'question':question,'equation':equation}
    nested_definition=bool(re.search(r'\bdefined?\b[^.]*?\bas\b',question,re.I))
    if nested_definition:raise Unresolved('unparsed_explicit_question_definition')
    operation = classify_operation(question)
    # A nested average is already a registered multi-step metric. Averaging all
    # its monetary leaves would erase the authorized inner ratios.
    policy = REGISTRY.find_policy(spec.metric)
    composite_average=bool(operation=='average' and policy and re.search(r'3yr|3_year|three_year',policy.metric))
    if operation and not composite_average and not nested_definition:
        resolved = resolve_generic_operation(ir, question)
        if resolved:
            return replace(spec, formula=resolved['formula'], formula_source='generic_operation'), {
                'kind': 'question_operation', 'source_id': resolved.get('operation', operation),
                'question': question, 'equation': resolved['formula'], 'source_note': resolved.get('source_note')}
    target_names = {spec.metric}
    for cid in REGISTRY.infer_concepts(spec.metric).values():
        target_names.update(REGISTRY.concepts[cid].xbrl_concepts)
    matching = []
    for group in filing.data.get('calculations', []):
        names = [group['parent'], group['parent'].split(':')[-1], *filing.data.get('labels', {}).get(group['parent'], [])]
        if any(tokens(t) == tokens(n) for t in target_names for n in names):
            matching.append(group)
    if matching:
        equations = {tuple(sorted((c['concept'], str(c['weight'])) for c in g['children'])) for g in matching}
        if len(equations) != 1: raise Unresolved('ambiguous_calculation_linkbase')
        group = matching[0]
        roles, pieces = [], []
        for i, child in enumerate(group['children']):
            if str(child['weight']) not in {'1', '-1', '1.0', '-1.0'}:
                raise Unresolved('unsupported_linkbase_arc_weight')
            name = 'child_'+str(i)
            labels = filing.data.get('labels', {}).get(child['concept'], [])
            roles.append(RoleSpec(name=name, concept=child['concept'], aliases=labels or [child['concept'].split(':')[-1]], period=spec.period))
            pieces.append('('+str(child['weight'])+' * '+name+')')
        formula = ' + '.join(pieces)
        return replace(spec, roles=roles, formula=formula, formula_source='xbrl_linkbase'), {
            'kind': 'filing_calculation_linkbase', 'source_id': group['role'], 'equation': formula,
            'source_sha256': filing.data.get('calculation_sha256'), 'parent': group['parent'], 'children': group['children']}
    if policy:
        role_map, issues = _resolve_roles(policy, ir, REGISTRY)
        candidates = []
        for template in policy.formula_templates:
            if not _identifiers(template) <= set(role_map): continue
            formula = _substitute_template(template, role_map)
            if formula:
                candidates.append((formula, template))
        # Explicit output units disambiguate ratio vs percent representation.
        percent = bool(re.search(r'percent|%', spec.claim_unit, re.I))
        ratio = bool(re.search(r'ratio|times|multiple', spec.claim_unit, re.I))
        if percent and any(re.search(r'\*\s*100\b', f) for f, _ in candidates):
            candidates = [(f,t) for f,t in candidates if re.search(r'\*\s*100\b', f)]
        elif ratio:
            candidates = [(f,t) for f,t in candidates if not re.search(r'\*\s*100\b', f)]
        candidates=without_redundant_display_scaling(candidates,spec.claim_unit)
        canonical = {}
        for f, t in candidates:
            try: canonical.setdefault(signature(f), (f,t))
            except (ValueError, TypeError): continue
        if len(canonical) == 1:
            formula, template = next(iter(canonical.values()))
            names = formula_variables(formula)
            return replace(spec, formula=formula, roles=[r for r in spec.roles if r.name in names], formula_source='policy_registry'), {
                'kind': 'curated_metric_registry', 'source_id': policy.policy_id, 'equation': formula,
                'template': template, 'role_map': role_map, 'source_refs': policy.source_refs,
                'question_composition':'average_of_authorized_period_metrics' if composite_average else None}
        raise Unresolved('ambiguous_or_unresolved_registry_formula:'+policy.policy_id)
    # Direct extraction is an explicit identity operation; still needs XBRL grounding.
    if len(spec.roles) == 1 and spec.formula.strip() == spec.roles[0].name and not operation:
        return replace(spec, formula_source='generic_operation'), {'kind': 'question_identity', 'source_id': 'direct_numerical_lookup', 'equation': spec.formula, 'question': question}
    # Do not trust formula_source='document_derived' as proof. An explicit equation
    # has to occur in the disclosure and name the exact metric and operands.
    for line in evidence.splitlines():
        if '=' not in line: continue
        left, right = line.split('=', 1)
        if tokens(left) != tokens(spec.metric): continue
        replaced = right.strip()
        for r in sorted(spec.roles, key=lambda r: -max(map(len, r.aliases or [r.name]))):
            for label in sorted([r.name, *r.aliases], key=len, reverse=True):
                replaced = re.sub(r'(?<!\w)'+re.escape(label)+r'(?!\w)', r.name, replaced, flags=re.I)
        try:
            if signature(replaced) != signature(spec.formula): continue
        except (ValueError, TypeError): continue
        return replace(spec, formula=replaced, formula_source='document_derived'), {
            'kind': 'disclosure_equation', 'source_id': filing.data['doc_name'], 'source_quote': line, 'equation': replaced}
    raise Unresolved('formula_authority_not_established')
