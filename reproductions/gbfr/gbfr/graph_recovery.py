"""Lossless source inventory and conservative formula recovery for FMKG.

This module never invents a term, chooses between competing definitions, removes
a cycle, or reads benchmark questions/answers. Its candidates are review inputs,
not a replacement for the paper's final expert-validated graph.
"""
from __future__ import annotations

import ast
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import unicodedata

import sympy as sp

from .data import sha256, write_json
from .graph import Formula, Operand
from .types import AssetError, dumps


# Only synonym sets explicitly printed in the supplied paper. Do not expand this
# from benchmark labels or treat qualified/time-specific names as equivalent.
PAPER_ALIAS_SETS = {
    "Net Income": {"Net Income", "Net Profit", "Net Earnings"},
    "Cost of Sales": {"Cost of Sales", "Cost of Goods Sold", "Cost of Products Sold", "COGS"},
}
PAPER_ALIAS_SOURCES = {"Net Income": "Section 3.2 alias mapping",
                       "Cost of Sales": "Appendix A, Figure 4"}


def name_key(name: str) -> str:
    # Do not erase division signs, hyphens or digits: these can change a metric.
    return " ".join(unicodedata.normalize("NFKC", name).casefold().split())


def expanded_abbreviation(name: str) -> str | None:
    """Recognize a spelling expansion, without deleting accounting qualifiers."""
    match = re.fullmatch(r"(.+?)\s+\(([A-Z]{2,10})\)", name)
    if not match:
        return None
    base, abbreviation = match.groups()
    words = re.findall(r"[A-Za-z]+", base)
    initials = "".join(word[0].upper() for word in words)
    without_connectors = "".join(word[0].upper() for word in words
                                 if word.casefold() not in {"and", "of", "the", "to", "for", "in"})
    return base if abbreviation in {initials, without_connectors} else None


def strongly_connected(nodes, edges) -> list[list[str]]:
    """Iterative Kosaraju; safe on large raw graphs with no assumed depth bound."""
    forward, reverse = {n: set() for n in nodes}, {n: set() for n in nodes}
    for a, b in edges:
        forward[a].add(b)
        reverse[b].add(a)
    seen, order = set(), []
    for start in sorted(forward):
        if start in seen:
            continue
        seen.add(start)
        stack = [(start, iter(sorted(forward[start])))]
        while stack:
            node, children = stack[-1]
            child = next(children, None)
            if child is None:
                order.append(node)
                stack.pop()
            elif child not in seen:
                seen.add(child)
                stack.append((child, iter(sorted(forward[child]))))
    seen, components = set(), []
    for start in reversed(order):
        if start in seen:
            continue
        component, stack = [], [start]
        seen.add(start)
        while stack:
            node = stack.pop()
            component.append(node)
            for child in sorted(reverse[node]):
                if child not in seen:
                    seen.add(child)
                    stack.append(child)
        if len(component) > 1 or (start, start) in edges:
            components.append(sorted(component))
    return sorted(components, key=lambda c: (-len(c), c))


class SourceIndex:
    def __init__(self, records: list[dict]):
        self.records = records
        self.groups = defaultdict(list)
        self.names = defaultdict(set)
        self.aliases = defaultdict(set)
        self.abbreviation_expansions = defaultdict(set)
        for i, record in enumerate(records):
            term = record.get("term_en")
            if not isinstance(term, dict) or not isinstance(term.get("name"), str):
                continue
            name = term["name"]
            self.groups[name].append(i)
            self.names[name_key(name)].add(name)
            expansion = expanded_abbreviation(name)
            if expansion:
                self.abbreviation_expansions[name_key(expansion)].add(name)
            for values in term.get("aliases", {}).values():
                if not isinstance(values, list):
                    continue
                for alias in values:
                    if isinstance(alias, str) and alias.strip():
                        self.aliases[name_key(alias)].add(name)

    def resolve(self, text: str) -> dict:
        if text in self.groups:
            return {"status": "canonical_exact", "metric": text, "candidates": [text]}
        names = self.names.get(name_key(text), set())
        if len(names) == 1:
            return {"status": "canonical_case_space", "metric": next(iter(names)), "candidates": sorted(names)}
        registered = self.aliases.get(name_key(text), set())
        aliases = names | registered | self.abbreviation_expansions.get(name_key(text), set())
        if len(aliases) == 1:
            return {"status": "registered_alias" if registered else "name_abbreviation_expansion",
                    "metric": next(iter(aliases)), "candidates": sorted(aliases)}
        return {"status": "ambiguous" if aliases else "unresolved", "metric": None, "candidates": sorted(aliases)}


def bind_formula(index: SourceIndex, record_index: int, formula_index: int) -> dict:
    record = index.records[record_index]
    target = record["term_en"]["name"]
    source = record["formula_en"][formula_index]
    result = {"source_record": record_index, "source_formula_index": formula_index,
              "target": target, "source_formula": source, "status": "requires_review"}
    parts = re.split(r"=|≈", source, maxsplit=1)
    if len(parts) != 2:
        result["reason"] = "no_equation_separator"
        return result
    lhs, rhs = (part.strip() for part in parts)
    alignment = index.resolve(lhs)
    own_aliases = [target, expanded_abbreviation(target)]
    for values in record["term_en"].get("aliases", {}).values():
        own_aliases.extend(values if isinstance(values, list) else [])
    if alignment["metric"] != target and any(isinstance(a, str) and name_key(lhs) == name_key(a) for a in own_aliases):
        alignment = {"status": "source_registered_alias", "metric": target,
                     "other_global_candidates": alignment["candidates"], "candidates": [target]}
    result["lhs_alignment"] = alignment
    if alignment["metric"] != target:
        result["reason"] = "lhs_not_explicitly_aligned_to_target"
        return result
    # Available labels come from THIS record's explicit calculation concepts.
    # Non-calculation labels may still be real operands; only an actual occurrence
    # in the equation can make them a syntactic candidate.
    label_targets = defaultdict(set)
    for related in record.get("related_concepts_en", []):
        label = related.get("concept")
        if not isinstance(label, str) or not label.strip():
            continue
        resolution = index.resolve(label)
        if resolution["metric"]:
            metric = resolution["metric"]
            label_targets[label].add(metric)
            label_targets[metric].add(metric)
            for i in index.groups[metric]:
                for values in index.records[i]["term_en"].get("aliases", {}).values():
                    for alias in values if isinstance(values, list) else []:
                        if isinstance(alias, str) and alias.strip():
                            label_targets[alias].add(metric)
    if not label_targets:
        result["reason"] = "no_explicit_resolved_operand_labels"
        return result
    labels = sorted(label_targets, key=lambda s: (-len(s), s))
    # Keep complete metric names intact, including internal hyphens and brackets.
    pattern = re.compile(r"(?<![A-Za-z0-9_])(?:" + "|".join(re.escape(s) for s in labels) + r")(?![A-Za-z0-9_])", re.I)
    by_fold = defaultdict(set)
    for label, metrics in label_targets.items():
        by_fold[name_key(label)].update(metrics)
    used, ambiguous = {}, []

    def substitute(match):
        text = match[0]
        # An exact canonical name wins over an alias collision, as in SourceIndex.
        direct = index.resolve(text)
        candidates = by_fold[name_key(text)]
        if direct["status"] == "canonical_exact" and direct["metric"] in candidates:
            candidates = {direct["metric"]}
        if len(candidates) != 1:
            ambiguous.append({"label": text, "candidates": sorted(candidates)})
            return text
        metric = next(iter(candidates))
        if metric not in used:
            used[metric] = "x" + str(len(used))
        return used[metric]

    expression = pattern.sub(substitute, rhs)
    if ambiguous:
        result.update(reason="ambiguous_operand_alias", ambiguities=ambiguous)
        return result
    expression = (expression.replace("×", "*").replace("÷", "/").replace("−", "-")
                  .replace("–", "-").replace("^", "**").replace("[", "(").replace("]", ")"))
    expression = re.sub(r"(?<=\d)\s*%", "/100", expression)
    expression = re.sub(r"√\s*\(", "sqrt(", expression)
    operands = [Operand(symbol, metric) for metric, symbol in used.items()]
    f = Formula(f"raw:{record_index}:{formula_index}", target, expression, operands, source)
    try:
        if not operands:
            raise AssetError("No financial operand")
        f.symbolic()
    except (AssetError, TypeError, ValueError, SyntaxError, RecursionError) as exc:
        result.update(reason="unsupported_or_unbound_expression", expression=expression,
                      resolved_operands=[{"symbol": o.symbol, "metric": o.metric} for o in operands])
        return result
    # Mechanical binding is not financial validation, temporal role inference, or
    # a choice of canonical direction. Preserve those as outstanding requirements.
    result.update(status="syntactically_bound", expression=expression,
                  operands=[{"symbol": o.symbol, "metric": o.metric} for o in operands],
                  canonical_direction_verified=False, semantic_validation="pending")
    return result


def reciprocal_equation_families(candidates: list[dict], canonical_names) -> dict:
    """Find algebraically identical rational equations with different targets.

    This identifies source-supported reverse-use candidates. It deliberately does
    not choose which direction is canonical, or assume equal temporal/unit scope.
    """
    global_symbols = {name: sp.Symbol("g" + str(i), real=True)
                      for i, name in enumerate(sorted(canonical_names))}
    equations = defaultdict(list)
    cache = {}
    skipped = Counter()
    for candidate in candidates:
        if candidate["status"] != "syntactically_bound":
            continue
        ident = dumps([candidate["target"], candidate["expression"], candidate["operands"]])
        if ident not in cache:
            try:
                formula = Formula("recovery", candidate["target"], candidate["expression"],
                                  [Operand(**o) for o in candidate["operands"]], candidate["source_formula"])
                rhs, symbols = formula.symbolic()
                rhs = rhs.subs({symbols[o["symbol"]]: global_symbols[o["metric"]] for o in candidate["operands"]})
                relation = global_symbols[candidate["target"]] - rhs
                numerator, _ = sp.together(relation).as_numer_denom()
                variables = sorted(numerator.free_symbols, key=str)
                if not variables:
                    raise ValueError("identity_without_variables")
                polynomial = sp.Poly(numerator, *variables)
                cache[ident] = sp.srepr(polynomial.monic().as_expr())
            except (ValueError, TypeError, sp.PolynomialError, NotImplementedError):
                cache[ident] = None
                skipped["non_rational_polynomial_or_identity"] += 1
        key = cache[ident]
        if key is not None:
            equations[key].append({"target": candidate["target"],
                                   "source_record": candidate["source_record"],
                                   "source_formula_index": candidate["source_formula_index"],
                                   "source_formula": candidate["source_formula"]})
    families = []
    for equation, members in equations.items():
        targets = sorted({m["target"] for m in members})
        if len(targets) > 1:
            families.append({"equation_hash": hashlib.sha256(equation.encode()).hexdigest(),
                             "targets": targets, "source_formulas": members,
                             "canonical_direction": None, "temporal_and_unit_equivalence_verified": False})
    families.sort(key=lambda f: (f["targets"], f["equation_hash"]))
    return {"families": families, "skipped": dict(skipped),
            "note": "Algebraic relation only; no automatic edge deletion, partition change, or scope assumption"}


def _record_parameter_labels(index, record):
    """Explicit input labels within one source record, not global synonyms.

    A Python formal such as ``assets`` is local to its function. If that
    record declares Total Assets as an input and the source vocabulary
    explicitly registers Assets as its alias, that local binding may override
    an unrelated global node named Assets. No qualifier is inferred or removed.
    """
    source_index=getattr(index,'source_index',None)
    if source_index is None:
        source_index=index if isinstance(index,SourceIndex) else SourceIndex(index.records)
    labels=defaultdict(set);evidence=defaultdict(list)
    for related in record.get('related_concepts_en',[]):
        label=related.get('concept')
        if not isinstance(label,str) or not label.strip():continue
        resolution=index.resolve(label);metric=resolution.get('metric')
        if not metric:continue
        explicit=[(label,None,'declared_related_concept'),(metric,None,'resolved_declared_concept')]
        source_resolution=source_index.resolve(label)
        source_metric=source_resolution.get('metric')
        for source_record in source_index.groups.get(source_metric,[]):
            term=source_index.records[source_record]['term_en']
            explicit.append((term['name'],source_record,'source_term_name'))
            expansion=expanded_abbreviation(term['name'])
            if expansion:explicit.append((expansion,source_record,'source_abbreviation_expansion'))
            for aliases in term.get('aliases',{}).values():
                if isinstance(aliases,list):
                    explicit.extend((a,source_record,'source_registered_alias') for a in aliases if isinstance(a,str) and a.strip())
        for text,source_record,kind in explicit:
            key=name_key(text)
            labels[key].add(metric)
            proof={'declared_related_concept':label,'label':text,'evidence_kind':kind}
            if source_record is not None:proof['alias_source_record']=source_record
            if proof not in evidence[(key,metric)]:evidence[(key,metric)].append(proof)
    return labels,evidence


def _documented_parameter_metrics(fn,parameter,labels):
    """Read only an explicit parameter-description prefix from a docstring.

    No free semantic matching: e.g. 'Total liabilities of the company' can
    name the declared Total Liabilities input. 'Current liabilities' cannot
    silently mean Total Liabilities, and formulas/positions are not evidence.
    """
    doc=ast.get_docstring(fn,clean=False) or '';descriptions=[]
    escaped=re.escape(parameter)
    patterns=[r'^\s*'+escaped+r'(?:\s*\([^\n)]*\))?\s*:\s*(.+)$',
              r'^\s*:param(?:\s+\w+)?\s+'+escaped+r'\s*:\s*(.+)$']
    for line in doc.splitlines():
        for pattern in patterns:
            match=re.match(pattern,line)
            if match:descriptions.append(match[1])
    hits=[]
    for description in descriptions:
        text=re.sub(r'^(?:the|a|an)\s+','',name_key(description))
        if re.search(r'\b(?:19|20)\d{2}\b',text):continue
        for label,metrics in labels.items():
            if text.startswith(label):
                tail=text[len(label):]
                if re.match(r'^(?:$|[.,;:(]|\s+(?:of|in|expressed|denominated)\b)',tail):
                    hits.append((len(label),label,metrics,description))
    if not hits:return set(),[]
    longest=max(h[0] for h in hits);metrics=set();proof=[]
    for length,label,choices,description in hits:
        if length==longest:
            metrics.update(choices);proof.append({'parameter_description':description,'matched_explicit_label':label})
    return metrics,proof


def bind_reference_code(index: SourceIndex, record_index: int, formula_index: int) -> dict:
    """Analyze a straight-line reference function without executing source code.

    Prefer an unambiguous record-local declared input/registered alias, or an
    explicit parameter documentation label, before global name resolution.
    Conditions, loops, opaque helper calls and unresolved inputs remain review
    items. This can recover dependencies omitted from related_concepts.
    """
    record = index.records[record_index]
    result = {"source_record": record_index, "source_formula_index": formula_index,
              "target": record["term_en"]["name"], "status": "requires_review"}
    codes = record.get("code", [])
    if formula_index >= len(codes) or not isinstance(codes[formula_index], str):
        return {**result, "reason": "no_corresponding_reference_code"}
    source = codes[formula_index].strip()
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return {**result, "reason": "reference_code_syntax"}
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    if len(functions) != 1:
        return {**result, "reason": "not_one_reference_function"}
    fn = functions[0]
    if (fn.args.defaults or fn.args.kw_defaults or fn.args.kwonlyargs or fn.args.vararg or fn.args.kwarg
            or fn.decorator_list or fn.args.posonlyargs):
        return {**result, "reason": "reference_function_signature_needs_review"}
    local_labels,local_evidence=_record_parameter_labels(index,record)
    resolutions=[];local_bindings=[]
    for argument in fn.args.args:
        label=argument.arg.replace('_',' ');global_resolution=index.resolve(label)
        choices=local_labels.get(name_key(label),set());proof=[];kind='record_local_explicit_alias'
        if not choices:
            choices,proof=_documented_parameter_metrics(fn,argument.arg,local_labels);kind='explicit_parameter_documentation'
        metric=next(iter(choices)) if len(choices)==1 else global_resolution.get('metric')
        resolutions.append((argument,label,metric,global_resolution))
        if len(choices)==1 and metric!=global_resolution.get('metric'):
            if not proof:proof=local_evidence[(name_key(label),metric)]
            local_bindings.append({'parameter':argument.arg,'metric':metric,'global_metric':global_resolution.get('metric'),
                                   'binding_source':kind,'evidence':proof})
    # Do not collapse two local roles (e.g. current/prior amounts) into a
    # single source input. Keep the previous global binding in that case,
    # rather than making a previously comparable source silently unverifiable.
    chosen=[m for _,_,m,_ in resolutions if m]
    if local_bindings and len(chosen)!=len(set(chosen)):
        resolutions=[(a,label,r.get('metric'),r) for a,label,_,r in resolutions]
        local_bindings=[]
    environment, operands = {}, []
    for argument,label,metric,resolution in resolutions:
        if not metric:
            return {**result, "reason": "unresolved_code_parameter", "parameter": argument.arg,
                    "alignment": resolution}
        symbol = "x" + str(len(operands))
        if any(o.metric == metric for o in operands):
            return {**result, "reason": "multiple_code_parameters_share_metric_without_roles"}
        operands.append(Operand(symbol, metric))
        environment[argument.arg] = ast.Name(id=symbol, ctx=ast.Load())
    math_names = {"sqrt", "log", "ln", "log10", "exp", "abs", "min", "max"}

    def substitute(node):
        if isinstance(node, ast.Name) and node.id in environment:
            return environment[node.id]
        if isinstance(node, ast.Constant) and type(node.value) in {int, float}:
            return node
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)):
            return ast.BinOp(left=substitute(node.left), op=node.op, right=substitute(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            return ast.UnaryOp(op=node.op, operand=substitute(node.operand))
        if isinstance(node, ast.Call) and not node.keywords:
            name = node.func.id if isinstance(node.func, ast.Name) else (
                node.func.attr if isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name) and node.func.value.id == "math" else None)
            if name in math_names:
                return ast.Call(func=ast.Name(id=name, ctx=ast.Load()), args=[substitute(a) for a in node.args], keywords=[])
        raise AssetError("Unsupported reference expression")

    expression = None
    try:
        for statement in fn.body:
            if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant) and isinstance(statement.value.value, str):
                continue  # Docstrings are evidence, never executed.
            if isinstance(statement, ast.Import) and all(a.name == "math" and not a.asname for a in statement.names):
                continue  # Only translate approved math intrinsics; no import is executed.
            if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name):
                environment[statement.targets[0].id] = substitute(statement.value)
            elif isinstance(statement, ast.Return):
                expression = ast.unparse(substitute(statement.value))
                break
            else:
                raise AssetError("Control flow or non-scalar reference function")
        if expression is None:
            raise AssetError("No scalar return")
        used = {n.id for n in ast.walk(ast.parse(expression)) if isinstance(n, ast.Name)}
        operands = [o for o in operands if o.symbol in used]
        if not operands:
            raise AssetError("No resolved numeric inputs")
        formula = Formula("reference-recovery", result["target"], expression, operands,
                          record["formula_en"][formula_index])
        formula.symbolic()
    except (AssetError, SyntaxError, TypeError, ValueError):
        return {**result, "reason": "reference_control_flow_or_unsupported_expression"}
    return {**result, "status": "syntactically_bound", "expression": expression,
            "operands": [{"symbol": o.symbol, "metric": o.metric} for o in operands],
            "source_code_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "source_formula": record["formula_en"][formula_index],
            "semantic_validation": "pending", "canonical_direction_verified": False,
            'record_local_parameter_bindings':local_bindings}


def compare_bound_expressions(first: dict, second: dict) -> str:
    if first["status"] != "syntactically_bound" or second["status"] != "syntactically_bound":
        return "not_verifiable_from_both_sources"
    metrics = sorted({o["metric"] for candidate in [first, second] for o in candidate["operands"]})
    globals_ = {name: sp.Symbol("g"+str(i), real=True) for i, name in enumerate(metrics)}
    expressions = []
    try:
        for candidate in [first, second]:
            f = Formula("compare", candidate["target"], candidate["expression"],
                        [Operand(**o) for o in candidate["operands"]], candidate["source_formula"])
            rhs, symbols = f.symbolic()
            expressions.append(rhs.subs({symbols[o["symbol"]]: globals_[o["metric"]] for o in candidate["operands"]}))
        difference = sp.cancel(sp.together(expressions[0]-expressions[1]))
    except (TypeError, ValueError, NotImplementedError, sp.PolynomialError):
        return "not_verifiable_from_both_sources"
    return "symbolically_equivalent" if difference == 0 else "symbolic_disagreement_requires_review"


def classify_source_disagreement(first: dict, second: dict) -> dict:
    """Separate paper-explicit synonyms, representation factors and real unknowns.

    A constant factor is a diagnostic, never permission to multiply a graph value
    by 100 without unit evidence. No canonical edge direction or type is chosen.
    """
    if first["status"] != "syntactically_bound" or second["status"] != "syntactically_bound":
        return {"category": "source_not_comparable"}
    aliases = {name_key(alias): canonical for canonical, members in PAPER_ALIAS_SETS.items() for alias in members}
    canonical = lambda metric: aliases.get(name_key(metric), metric)
    canonical_metrics = sorted({canonical(o["metric"]) for c in [first, second] for o in c["operands"]})
    globals_ = {metric: sp.Symbol("g"+str(i), real=True) for i, metric in enumerate(canonical_metrics)}
    expressions, metric_sets, used_aliases = [], [], {}
    for candidate in [first, second]:
        members = [canonical(o["metric"]) for o in candidate["operands"]]
        if len(members) != len(set(members)):
            return {"category": "alias_roles_need_scope_review"}
        metric_sets.append(set(members))
        f = Formula("source-review", candidate["target"], candidate["expression"],
                    [Operand(**o) for o in candidate["operands"]], candidate["source_formula"])
        rhs, symbols = f.symbolic()
        for operand in candidate["operands"]:
            metric = operand["metric"]
            if canonical(metric) != metric:
                used_aliases[metric] = {"canonical": canonical(metric), "paper_source": PAPER_ALIAS_SOURCES[canonical(metric)]}
        expressions.append(rhs.subs({symbols[o["symbol"]]: globals_[canonical(o["metric"])] for o in candidate["operands"]}))
    try:
        difference = sp.cancel(sp.together(expressions[0]-expressions[1]))
        if difference == 0:
            return {"category": "equivalent_under_explicit_paper_aliases", "paper_alias_bindings": used_aliases,
                    "financial_definition_validation": "not_asserted_by_algebra_only"}
        if expressions[0] != 0:
            factor = sp.cancel(sp.together(expressions[1]/expressions[0]))
            if not factor.free_symbols and factor.is_finite and factor.is_real:
                return {"category": "constant_sign_difference" if factor == -1 else "constant_factor_needs_unit_review",
                        "reference_code_divided_by_formula": str(factor), "paper_alias_bindings": used_aliases,
                        "automatic_conversion_applied": False}
    except (TypeError, ValueError, NotImplementedError, sp.PolynomialError):
        return {"category": "symbolic_review_not_decidable"}
    return {"category": "input_metric_identity_needs_review" if metric_sets[0] != metric_sets[1]
            else "same_inputs_different_expression", "paper_alias_bindings": used_aliases}


def inventory_graph(source: Path, output: Path, report_path: Path) -> dict:
    records = json.loads(source.read_text(encoding="utf-8"))
    index = SourceIndex(records)
    relation_counts, resolution_counts = Counter(), Counter()
    all_edges, calculation_edges, bound_edges = set(), set(), set()
    unresolved = defaultdict(list)
    conflicts = []
    definitions = []
    for name, indices in sorted(index.groups.items()):
        states = {bool(records[i].get("formula_en")) for i in indices}
        if len(states) > 1:
            conflicts.append({"metric": name, "source_records": indices,
                              "issue": "formula_presence_varies_between_source_records",
                              "explicit_atomic_derived_claim": False,
                              "note": "An empty formula field may be incomplete; raw records have no explicit kind field"})
        # Exact same names are grouped losslessly. Do not choose one definition.
        definitions.append({"name": name, "source_records": indices,
                            "definitions": list(dict.fromkeys(records[i].get("definition_en", "") for i in indices)),
                            "formula_presence_variation": len(states) > 1,
                            "source_type_explicitly_encoded": False})
    for i, record in enumerate(records):
        if not isinstance(record.get("term_en"), dict):
            continue
        name = record["term_en"]["name"]
        for j, related in enumerate(record.get("related_concepts_en", [])):
            relation = related.get("relation", "Calculation")
            relation_counts[relation] += 1
            resolution = index.resolve(related.get("concept", ""))
            resolution_counts[resolution["status"]] += 1
            if resolution["metric"]:
                edge = (name, resolution["metric"])
                all_edges.add(edge)
                if relation == "Calculation":
                    calculation_edges.add(edge)
            else:
                unresolved[related.get("concept", "")].append({"record": i, "relation_index": j,
                    "relation": relation, **resolution})
    formulas, code_candidates = [], []
    for i, record in enumerate(records):
        if not isinstance(record.get("term_en"), dict):
            continue
        for j in range(len(record.get("formula_en", []))):
            candidate = bind_formula(index, i, j)
            formulas.append(candidate)
            code = bind_reference_code(index, i, j)
            code["formula_code_alignment"] = compare_bound_expressions(candidate, code)
            code_candidates.append(code)
            if candidate["status"] == "syntactically_bound":
                bound_edges.update((candidate["target"], o["metric"]) for o in candidate["operands"])
    views = {}
    for name, edges in [("all_resolved_related_links", all_edges),
                        ("calculation_only_resolved_links", calculation_edges),
                        ("syntactically_bound_formula_dependencies", bound_edges)]:
        components = strongly_connected(set(index.groups), edges)
        views[name] = {"nodes": len(index.groups), "edges": len(edges),
                       "cyclic_components": len(components), "nodes_in_cycles": sum(map(len, components)),
                       "is_dag": not components, "components": components}
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "canonical_name_groups.json", definitions)
    write_json(output / "partition_conflicts.json", conflicts)
    write_json(output / "field_completeness_variations.json", conflicts)
    write_json(output / "unresolved_dependencies.json", dict(sorted(unresolved.items())))
    write_json(output / "cycle_views.json", views)
    reciprocal = reciprocal_equation_families(formulas, index.groups)
    write_json(output / "reciprocal_equation_families.json", reciprocal)
    (output / "formula_candidates.jsonl").write_text("".join(dumps(f)+"\n" for f in formulas), encoding="utf-8")
    (output / "reference_code_candidates.jsonl").write_text("".join(dumps(f)+"\n" for f in code_candidates), encoding="utf-8")
    reviews = []
    for formula, code in zip(formulas, code_candidates):
        if code["formula_code_alignment"] != "symbolic_disagreement_requires_review":
            continue
        reviews.append({"source_record": formula["source_record"], "source_formula_index": formula["source_formula_index"],
                        "target": formula["target"], "source_formula": formula["source_formula"],
                        "formula_expression": formula["expression"], "code_expression": code["expression"],
                        **classify_source_disagreement(formula, code)})
    write_json(output / "formula_code_review.json", {"paper_alias_sets": {k: sorted(v) for k, v in PAPER_ALIAS_SETS.items()},
               "paper_alias_sources": PAPER_ALIAS_SOURCES, "reviews": reviews,
               "automatic_graph_or_unit_changes_applied": False})
    write_json(output / "failed_records.json", [{"record_index": i, "source_id": r.get("_source_id"),
               "source": r.get("source"), "issue": "generation_failed"}
               for i, r in enumerate(records) if not isinstance(r.get("term_en"), dict)])
    summary = {"schema_version": 1, "source_sha256": sha256(source), "raw_records": len(records),
               "canonical_exact_name_groups": len(index.groups), "formula_presence_variations": len(conflicts),
               "explicit_source_type_claims": False,
               "partition_conflicts_legacy_count": len(conflicts),
               "related_relation_types": dict(relation_counts), "dependency_resolution": dict(resolution_counts),
               "unresolved_or_ambiguous_dependency_labels": len(unresolved),
               "formula_candidates": len(formulas),
               "formula_status": dict(Counter(f["status"] for f in formulas)),
               "reference_code_status": dict(Counter(f["status"] for f in code_candidates)),
               "formula_code_alignment": dict(Counter(f["formula_code_alignment"] for f in code_candidates)),
               "formula_code_review_categories": dict(Counter(r["category"] for r in reviews)),
               "reciprocal_equation_families": len(reciprocal["families"]),
               "formula_review_reasons": dict(Counter(f.get("reason") for f in formulas if f["status"] != "syntactically_bound")),
               "graph_views": {name: {k: v for k, v in info.items() if k != "components"} for name, info in views.items()},
               "paper_expected": {"nodes": 7521, "atomic": 3318, "derived": 4203, "edges": 20152},
               "benchmark_data_used": False, "paper_ready": False,
               "status": "lossless recovery candidates; canonical direction and expert semantic validation unresolved"}
    write_json(report_path, summary)
    return summary
