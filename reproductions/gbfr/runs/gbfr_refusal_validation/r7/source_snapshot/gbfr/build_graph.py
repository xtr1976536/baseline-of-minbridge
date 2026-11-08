"""Deterministic, source-only reconstruction of the paper's metric DAG.

This is a reproducible reconstruction, not the unpublished expert-validated
snapshot. No benchmark, answer or model prediction is an input to this builder.
Whole formulas (never individual operands) are retained or rejected.
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
from .graph import Formula, MetricGraph, Operand
from .graph_recovery import (PAPER_ALIAS_SETS, expanded_abbreviation, bind_reference_code,
                             classify_source_disagreement, compare_bound_expressions)
from .types import AssetError, dumps


POLICY = "paper-method-source-reconstruction-v1"
SOURCE_SHA256 = "67f2ff0393308352992fbef88777275b09adfd26a4042541fc395eed9e4be06a"


def key(text):
    text = unicodedata.normalize("NFKC", text).casefold().replace("’", "'")
    return " ".join(text.split())


def identity(text):
    return re.sub(r"[-\s_'’]+", " ", key(text)).strip()


def spelling_variants(text):
    values = {key(text), key(text).replace("'", ""), key(text).replace("-", " ")}
    return values | {s.replace("'", "").replace("-", " ") for s in values}


class Lexicon:
    """Longest full-name matching; local explicit operand names take priority."""
    def __init__(self, labels):
        self.labels = labels
        self.trie = {}
        for label in labels:
            node = self.trie
            for char in label:
                node = node.setdefault(char, {})
            node[None] = label

    def replace(self, expression, resolve):
        result, offset = [], 0
        while offset < len(expression):
            if offset and (expression[offset-1].isalnum() or expression[offset-1] == "_"):
                result.append(expression[offset]); offset += 1; continue
            node, end, best = self.trie, offset, None
            while end < len(expression) and expression[end] in node:
                node = node[expression[end]]; end += 1
                if None in node and (end == len(expression) or not (expression[end].isalnum() or expression[end] == "_")):
                    best = (end, node[None])
            if best:
                end, label = best
                result.append(resolve(label)); offset = end
            else:
                result.append(expression[offset]); offset += 1
        return "".join(result)


class Builder:
    def __init__(self, records):
        self.records = records
        self.nodes, self.labels = {}, defaultdict(set)
        self.decisions, self.candidates = [], []
        self.canonical = {}
        names = sorted({r['term_en']['name'] for r in records if isinstance(r.get('term_en'), dict)})
        groups = defaultdict(list)
        for name in names:
            groups[identity(expanded_abbreviation(name) or name)].append(name)
        for members in groups.values():
            canonical = min(members, key=lambda n: (bool(expanded_abbreviation(n)), len(n), n))
            for name in members:
                self.canonical[name] = canonical
        # Synonyms expressly given in the paper, plus conventional equity names
        # needed by its Figures 1-2. No unqualified/qualified period names merge.
        synonym_sets = {**PAPER_ALIAS_SETS,
            'Return on Equity': {'Return on Equity', 'Return on Equity (ROE)', 'ROE'},
            'Final Equity': {'Final Equity', 'Total Equity', "Shareholders' Equity", 'Shareholders Equity',
                             "Stockholders' Equity", 'Stockholders Equity'}}
        for canonical, aliases in synonym_sets.items():
            for name in names:
                if identity(expanded_abbreviation(name) or name) in {identity(a) for a in aliases}:
                    old = self.canonical[name]
                    for member in names:
                        if self.canonical[member] == old:
                            self.canonical[member] = canonical
            for alias in aliases:
                self.canonical[alias] = canonical
        for i, record in enumerate(records):
            term = record.get('term_en')
            if not isinstance(term, dict):
                continue
            name = self.canonical[term['name']]
            node = self.ensure(name, record.get('definition_en', ''), source_record=i)
            node['primary_aliases'].add(term['name'])
            aliases = [term['name'], expanded_abbreviation(term['name'])]
            for values in term.get('aliases', {}).values():
                if isinstance(values, list):
                    aliases.extend(values)
            for alias in aliases:
                if isinstance(alias, str) and alias.strip():
                    node['aliases'].add(alias)
                    for label in spelling_variants(alias):
                        self.labels[label].add(name)
        for canonical, aliases in synonym_sets.items():
            node = self.ensure(canonical)
            node['primary_aliases'].update(aliases)
            for alias in aliases:
                node['aliases'].add(alias)
                for label in spelling_variants(alias):
                    self.labels[label].add(canonical)
        # Full canonical names take precedence over collisions of short aliases.
        self.exact = defaultdict(set)
        for name, canonical in self.canonical.items():
            for label in spelling_variants(name):
                self.exact[label].add(canonical)
        formal = defaultdict(set)
        for name in names:
            if expanded_abbreviation(name):
                abbreviation = re.search(r'\(([A-Z]{2,10})\)$', name)[1]
                formal[abbreviation].add(self.canonical[name])
        for abbreviation, choices in formal.items():
            if len(choices) == 1:
                canonical = next(iter(choices))
                self.canonical[abbreviation] = canonical
                self.exact[key(abbreviation)] = {canonical}
                self.nodes[canonical]['aliases'].add(abbreviation)
                # A qualified node can still be found by its full qualified
                # name; it must not hijack an unqualified formal acronym.
                for name, node in self.nodes.items():
                    if name != canonical:
                        node['aliases'] = {a for a in node['aliases'] if key(a) != key(abbreviation)}
        for record in records:
            for related in record.get('related_concepts_en', []):
                name = related.get('concept')
                if isinstance(name, str) and name.strip():
                    canonical = self.resolve_name(name) or name
                    for label in spelling_variants(name):
                        self.labels[label].add(canonical)
        self.lexicon = Lexicon(self.labels)

    def ensure(self, name, definition='', source_record=None):
        if name not in self.nodes:
            self.nodes[name] = {'name': name, 'aliases': set(), 'definition': definition,
                                'primary_aliases':set(),
                                'source_records': set(), 'formulas': []}
        node = self.nodes[name]
        if definition and not node['definition']:
            node['definition'] = definition
        if source_record is not None:
            node['source_records'].add(source_record)
        return node

    def resolve_name(self, text):
        if text in self.canonical:
            return self.canonical[text]
        candidates = self.exact.get(key(text), set()) if hasattr(self, 'exact') else set()
        candidates = candidates or self.labels.get(key(text), set())
        return next(iter(candidates)) if len(candidates) == 1 else None

    def parse(self, i, j, source):
        record = self.records[i]
        target = self.canonical[record['term_en']['name']]
        decision = {'record': i, 'formula_index': j, 'source_formula': source, 'source_target': target}
        try:
            parts = re.split(r'=|≈', source, maxsplit=1)
            if len(parts) != 2:
                raise AssetError('not_an_equation')
            lhs, rhs = (s.strip() for s in parts)
            lhs = re.sub(r'\s*\((?:%|percent|percentage)\)\s*$', '', lhs, flags=re.I)
            own = {key(a) for a in self.nodes[target]['aliases']} | {key(target)}
            if key(lhs) not in own:
                resolved = self.resolve_name(lhs)
                if resolved:
                    target = resolved
                elif re.fullmatch(r'[A-Za-z][A-Za-z0-9 /&\-\'(),.]{2,100}', lhs) and not re.search(r'\b(?:t|i|n)\b$', lhs):
                    # Explicit helper equation: retain its actual LHS, never assign
                    # its result to the enclosing article's different metric.
                    target = lhs
                else:
                    raise AssetError('unresolved_equation_target')
            if target in {'Return on Equity', 'Average Equity', 'Initial Equity', 'Final Equity'}:
                raise AssetError('paper_figure_1_2_definition_takes_precedence')
            local = defaultdict(set)
            for related in record.get('related_concepts_en', []):
                label = related.get('concept')
                if isinstance(label, str) and label.strip():
                    resolved = self.resolve_name(label) or label
                    for variant in spelling_variants(label):
                        local[variant].add(resolved)
            used = {}

            def substitute(label):
                choices = local.get(label) or self.exact.get(label) or self.labels[label]
                if len(choices) != 1:
                    raise AssetError('ambiguous_operand:' + label)
                metric = next(iter(choices))
                if metric == target:
                    raise AssetError('self_dependency_or_unbound_temporal_role')
                if metric not in used:
                    used[metric] = 'x' + str(len(used))
                return used[metric]

            rhs = rhs.replace('²', '**2').replace('³', '**3')
            rhs = key(rhs).replace('×', '*').replace('÷', '/').replace('−', '-').replace('–', '-')
            rhs = rhs.replace('^', '**').replace('[', '(').replace(']', ')')
            percent_output = bool(re.search(r'(?:\*\s*100\s*%?|\(\s*%\s*\))\s*$', rhs) or '%' in lhs)
            # Financial notation "ratio * 100%" is a displayed percent, not a
            # ratio multiplied by the literal value one. Other percentages are literals.
            rhs = re.sub(r'(?<![\d.])100\s*%', '100', rhs)
            rhs = re.sub(r'(\d+(?:\.\d+)?)\s*%', r'(\1/100)', rhs)
            rhs = re.sub(r'√\s*\(', 'sqrt(', rhs)
            rhs = re.sub(r'\b(max|min|abs|sqrt|log|ln|log10|exp)\b', lambda m: m[0].lower(), rhs, flags=re.I)
            expression = self.lexicon.replace(rhs, substitute)
            if not used:
                raise AssetError('no_scalar_metric_operands')
            operands = [{'symbol': symbol, 'metric': metric,
                         'constraints': {'meta': {'currency': None, 'scale': None, 'unit': None}}}
                        for metric, symbol in used.items()]
            formula = Formula('parse', target, expression, [Operand(**o) for o in operands], source)
            symbolic, _ = formula.symbolic()
            if not symbolic.free_symbols or symbolic.has(__import__('sympy').zoo, __import__('sympy').nan):
                raise AssetError('constant_identity_or_undefined_expression')
            meta = {'currency': None, 'scale': None, 'unit': 'percentage'} if percent_output else {}
            if not meta and '/' in expression and re.search(r'ratio|rate|margin|yield|return on|turnover', target, re.I):
                meta = {'currency': None, 'scale': None, 'unit': 'ratio'}
            # Arithmetic source formulas are primary. Code strings are never
            # executed and cannot override the paper/source equation.
            ident = hashlib.sha256(dumps([target, expression, operands, meta]).encode()).hexdigest()[:20]
            candidate = {'id': 'source:' + ident, 'target': target, 'expression': expression,
                         'operands': operands, 'source_formula': source, 'meta': meta,
                         'source_records': [i], 'source_formula_index': j, 'priority': 1}
            # Independently parse the paired code as data, never execute it.
            # Paper/source equations remain primary; disagreeing financial
            # inputs or operators are excluded rather than silently choosing one.
            class Index:
                records = self.records
                def resolve(_, label):
                    metric = self.resolve_name(label)
                    return {'metric': metric, 'candidates': [metric] if metric else []}
            reference = bind_reference_code(Index(), i, j)
            checkable = {**candidate, 'status': 'syntactically_bound'}
            comparison = compare_bound_expressions(checkable, reference)
            if comparison == 'symbolically_equivalent':
                candidate['reference_code_check'] = 'equivalent'
                candidate['priority'] = 3
            elif comparison == 'symbolic_disagreement_requires_review':
                review = classify_source_disagreement(checkable, reference)
                decision['reference_code_review'] = review
                unit_factor = (review['category'] == 'constant_factor_needs_unit_review'
                               and review.get('reference_code_divided_by_formula') in {'100', '1/100'}
                               and meta.get('unit') in {'percentage', 'ratio'})
                if not unit_factor and review['category'] != 'equivalent_under_explicit_paper_aliases':
                    raise AssetError('formula_code_semantic_disagreement')
                candidate['reference_code_check'] = review['category']
                candidate['reference_code_review'] = review
                candidate['priority'] = 2
            else:
                candidate['reference_code_check'] = 'unverifiable_static_code'
            self.candidates.append(candidate)
            decision.update(status='parsed_candidate', target=target, formula_id=candidate['id'])
        except (AssetError, SyntaxError, TypeError, ValueError, RecursionError) as exc:
            decision.update(status='excluded', reason=str(exc)[:240])
        self.decisions.append(decision)

    def paper_formulas(self):
        """Paper Figures 1-2 and 4 are authoritative over conflicting raw entries."""
        specs = [
            ('Initial Equity', 'e', [('e', 'Final Equity', {'temporal_scope': '$year-1'})],
             'Initial Equity = prior-year Final Equity', {}),
            ('Average Equity', '(b+e)/2', [('b', 'Initial Equity', {}), ('e', 'Final Equity', {})],
             'Average Equity = (Initial Equity + Final Equity)/2', {}),
            ('Return on Equity', 'i/a', [('i', 'Net Income', {}), ('a', 'Average Equity', {})],
             'ROE = Net Income / Average Equity', {'currency': None, 'scale': None, 'unit': 'ratio'}),
            ('Cost of Sales', 'b+p-e', [('b', 'Beginning Inventory', {}), ('p', 'Purchases', {}), ('e', 'Ending Inventory', {})],
             'Cost of Sales = Beginning Inventory + Purchases - Ending Inventory', {}),
            ('Cost of Sales', 's*(1-m)', [('s', 'Net Sales', {}), ('m', 'Gross Profit Margin', {'meta': {'currency': None, 'scale': None, 'unit': 'ratio'}})],
             'Cost of Sales = Net Sales * (1 - Gross Profit Margin)', {}),
        ]
        for i, (target, expression, operands, source, meta) in enumerate(specs):
            self.ensure(target)
            self.candidates.append({'id': 'paper:' + str(i), 'target': target, 'expression': expression,
                'operands': [{'symbol': s, 'metric': self.resolve_name(n) or n,
                              'constraints': {'meta': {'currency': None, 'scale': None, 'unit': None}, **c}}
                             for s, n, c in operands],
                'source_formula': source, 'meta': meta, 'priority': 10, 'source_records': [],
                'paper_source': 'Figures 1-2' if i < 3 else 'Appendix A Figure 4'})

    def build(self):
        for i, record in enumerate(self.records):
            if not isinstance(record.get('term_en'), dict):
                self.decisions.append({'record': i, 'status': 'excluded', 'reason': 'failed_source_generation'})
                continue
            for j, source in enumerate(record.get('formula_en', [])):
                if isinstance(source, str):
                    self.parse(i, j, source)
        self.paper_formulas()
        unique = {}
        for f in self.candidates:
            # Duplicate source records and display-unit variants are one path,
            # not independent votes. Preserve temporal/entity roles and distinct
            # required inputs, including syntactically used cancelled operands.
            formula = Formula(f['id'], f['target'], f['expression'], [Operand(**o) for o in f['operands']], f['source_formula'])
            expression, symbols = formula.symbolic()
            identities = {o['symbol']: dumps([o['metric'], {k:v for k,v in o.get('constraints',{}).items() if k!='meta'},
                                              o.get('constraints',{}).get('meta',{}).get('currency')]) for o in f['operands']}
            expression = expression.xreplace({symbols[s]: sp.Symbol('m'+hashlib.sha256(ident.encode()).hexdigest()[:24], real=True)
                                               for s,ident in identities.items()})
            if f['meta'].get('unit') == 'percentage':
                expression /= 100
            expression = sp.cancel(expression) if expression.is_rational_function(*expression.free_symbols) else expression
            signature = dumps([f['target'], sp.srepr(expression), sorted(identities.values())])
            if signature in unique:
                old=unique[signature]
                preferred,other=(f,old) if f['priority']>old['priority'] else (old,f)
                preferred['source_records']=sorted(set(old['source_records']+f['source_records']))
                preferred['supporting_source_formulas']=sorted(set(old.get('supporting_source_formulas',[old['source_formula']])
                                                                 +f.get('supporting_source_formulas',[f['source_formula']])))
                unique[signature]=preferred
            else:
                unique[signature] = f
        candidates = list(unique.values())
        frequency = Counter(f['target'] for f in candidates)

        def foundational_score(name):
            # Financial precedence, independent of benchmarks. Strongly prefer
            # observable prices/balances as leaves over reverse ratio formulas.
            return (4 * bool(re.search(r'ratio|margin|yield|return|duration|volatility|growth|turnover|multiple|index|sensitivity', name, re.I))
                    - 4 * bool(re.search(r'^(?:stock price|share price|market price|price|final equity|beginning |ending |number of |units |quantity |risk.free rate)$', name, re.I)))

        candidates.sort(key=lambda f: (-f['priority'], -foundational_score(f['target']),
                                      len(f['operands']), -frequency[f['target']], f['id']))
        edges = defaultdict(set)
        parents, levels = defaultdict(set), defaultdict(int)

        def reachable(start, target):
            seen, stack = set(), [start]
            while stack:
                node = stack.pop()
                if node == target:
                    return True
                if node not in seen:
                    seen.add(node); stack.extend(edges[node])
            return False

        rejected = []
        for f in candidates:
            target = f['target']
            dependencies = {o['metric'] for o in f['operands']}
            if any(reachable(d, target) for d in dependencies):
                rejected.append({'formula_id': f['id'], 'target': target, 'source_formula': f['source_formula'],
                                 'reason': 'reverse_or_cyclic_dependency', 'operands': f['operands']})
                continue
            # Appendix A.3 reports maximum derivation depth six. Enforce this
            # while constructing the canonical asset, never silently truncate a
            # runtime query. An over-depth equation is retained in the audit.
            changes = {}
            queue = [(target, max((levels[d]+1 for d in dependencies), default=0))]
            while queue:
                name, proposed = queue.pop()
                if proposed > max(levels[name], changes.get(name, 0)):
                    changes[name] = proposed
                    queue.extend((p, proposed+1) for p in parents[name])
            if max(changes.values(), default=0) > 6:
                if f['priority'] == 10:
                    raise AssetError('Paper explicit equation exceeds paper maximum depth')
                rejected.append({'formula_id': f['id'], 'target': target, 'source_formula': f['source_formula'],
                                 'reason': 'exceeds_paper_graph_depth_six', 'operands': f['operands']})
                continue
            node = self.ensure(target)
            for dependency in dependencies:
                self.ensure(dependency)
            edges[target].update(dependencies)
            levels.update(changes)
            for dependency in dependencies:
                parents[dependency].add(target)
            node['formulas'].append({k: v for k, v in f.items() if k not in {'target', 'priority'}})
        nodes = []
        for name, node in sorted(self.nodes.items()):
            node['aliases'] = sorted(node['aliases'] - {name})
            node['primary_aliases']=sorted(node['primary_aliases']-{name})
            node['source_records'] = sorted(node['source_records'])
            node['kind'] = 'derived' if node['formulas'] else 'atomic'
            node['classification_basis'] = 'retained_source_formula' if node['formulas'] else 'direct_evidence_only_in_reconstruction'
            nodes.append(node)
        graph = {'schema_version': 1, 'provenance': {
            'source': 'Author pinned raw FMKG + supplied paper Figures 1-2 and Appendix A Figure 4',
            'source_sha256': SOURCE_SHA256, 'policy': POLICY, 'paper_validated': False,
            'reconstructed': True, 'benchmark_inputs_used': False,
            'validation': 'source equation AST/operand binding, whole-formula DAG selection, paper overrides; no claim of author/expert validation',
        }, 'nodes': nodes}
        checked = MetricGraph.load_object(graph)
        depths = {}
        def depth(name):
            if name not in depths:
                depths[name] = max((1 + depth(o.metric) for f in checked.nodes[name].formulas for o in f.operands), default=0)
            return depths[name]
        report = {'policy': POLICY, 'stats': checked.stats(), 'max_depth': max(map(depth, checked.nodes)),
            'source_records': len(self.records), 'unique_candidates': len(candidates),
            'retained_formulas': sum(len(n['formulas']) for n in nodes),
            'direction_or_depth_exclusions': dict(Counter(d['reason'] for d in rejected)),
            'source_formula_decisions': dict(Counter(d['status'] for d in self.decisions)),
            'retained_reference_code_checks': dict(Counter(f.get('reference_code_check', 'paper_explicit')
                for n in nodes for f in n['formulas'])),
            'paper_snapshot_equivalence_claimed': False, 'benchmark_inputs_used': False,
            'selection_order': 'paper explicit > source equation/code agreement > financial derived-indicator precedence > fewer operands > source formula diversity > stable formula hash',
            'unparsed_formulas': dict(Counter(d['reason'].split(':')[0] for d in self.decisions if d['status']=='excluded'))}
        return graph, report, rejected


def build_graph(source: Path, output: Path, audit_dir: Path):
    if sha256(source) != SOURCE_SHA256:
        raise AssetError('FMKG raw source differs from pinned source')
    builder = Builder(json.loads(source.read_text(encoding='utf-8')))
    graph, report, rejected = builder.build()
    write_json(output, graph)
    report.update(graph_sha256=sha256(output), source_sha256=sha256(source))
    write_json(audit_dir / 'graph_build.json', report)
    write_json(audit_dir / 'graph_formula_decisions.json', builder.decisions)
    write_json(audit_dir / 'graph_direction_exclusions.json', rejected)
    return report
