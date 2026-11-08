from __future__ import annotations

import asyncio
from dataclasses import asdict
import math
import re

from .executor import clean_program, execute
from .graph import Formula, MetricGraph, operand_goal, norm
from .prompts import EVIDENCE_FORMAT, VERIFY_FORMAT, render
from .types import AssetError, Constraints, EvidenceError, Goal, Plan, Prediction, ProtocolError, Resolution, dumps, finite


EXECUTION_ENVIRONMENT = (
    "\nThe arithmetic environment supplies sqrt, log/ln (natural log), log10 and exp as functions."
    " They require no imports. Use only functions needed by the supplied formula/operator."
)


def known(value) -> bool:
    return value is not None and str(value).lower() not in {"unknown", "null", "none", ""}


def metric_hints(graph: MetricGraph, question: str) -> list[dict]:
    """Query-only canonical-name hints; no gold, new formula or forced mapping."""
    text=norm(question)
    if not hasattr(graph,'_mention_keys'):
        graph._mention_keys=tuple(sorted(set(graph.primary_names)|set(graph.aliases)))
    matches=[]
    for alias in graph._mention_keys:
        if len(alias)<3 or alias in {'percentage','percent','fiscal year','year','currency','million','usd'} or alias not in text:
            continue
        metric=graph.find(alias)
        if metric is None:
            continue
        pattern=re.escape(alias)
        if re.search('[a-z]',alias):
            pattern=r'(?<![a-z0-9_])'+pattern+r'(?![a-z0-9_])'
        for match in re.finditer(pattern,text):
            # A known subphrase must not erase an unknown qualifier, e.g.
            # suggesting corporate "Revenue" for "Fiscal Revenue".
            prefix=text[:match.start()]
            previous=re.search(r"([a-z][a-z'’-]*)\s+$",prefix)
            connectors={'a','an','the','compute','calculate','find','compare','use','using','of','to','for','and','or','is','was','are','were','in','its','their','what'}
            if previous and len(previous[1])>1 and previous[1] not in connectors and not previous[1].endswith(("'s",'’s')):
                continue
            if re.search(r'[\u3400-\u9fff]',alias):
                adjacent=text[max(0,match.start()-1):match.start()]+text[match.end():match.end()+1]
                if re.search(r'[\u3400-\u9fff]',adjacent):continue
            matches.append((match.start(),match.end(),metric.name,question))
    selected=[]
    for start,end,name,_ in sorted(matches,key=lambda x:(-(x[1]-x[0]),x[0],x[2])):
        if not any(start>=a and end<=b for a,b,_ in selected):
            selected.append((start,end,name))
    result=[]
    for start,end,name in sorted(selected):
        if name not in {x['canonical_metric'] for x in result}:
            result.append({'query_mention':text[start:end],'canonical_metric':name})
    return result


def numeric_tokens(text: str) -> list[float]:
    return [float(x.replace(",", "")) for x in re.findall(
        r"(?<![\d.])[+-]?(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?|\.\d+)(?!\d|\.\d)", text)]


def verbatim_spans(snippet: str, context: str) -> list[str]:
    squash=lambda s:' '.join(s.casefold().split())
    if squash(snippet) in squash(context):
        return [snippet]
    # Table headers and the labelled numeric row may be separate quotations.
    # Accept only complete copied sentences, never fuzzy paraphrases or invented
    # connective text, and retain the individual spans in the audit trace.
    spans=re.split(r'(?<=[.!?。！？])\s+',snippet.strip())
    if len(spans)>1 and all(squash(s) in squash(context) for s in spans):
        return spans
    raise EvidenceError('OES snippet is not a verbatim context span')


def binding_spans(binding: dict, context: str) -> list[str]:
    extra=binding.get('context_spans',[])
    if extra is None:extra=[]
    if not isinstance(extra,list) or any(not isinstance(s,str) or not s.strip() for s in extra):
        raise ProtocolError('Invalid evidence span list')
    if any(norm(s) not in norm(context) for s in extra):
        raise EvidenceError('OES supplied a non-verbatim evidence span')
    try:
        spans=verbatim_spans(binding['context'],context)
    except ProtocolError:
        if not extra or norm(binding['context'])!=norm(' '.join(extra)):
            raise
        spans=[]
    return list(dict.fromkeys([*spans,*extra]))


def quoted_value(value: float,text: str) -> bool:
    if any(math.isclose(value,n,rel_tol=1e-12,abs_tol=1e-12) for n in numeric_tokens(text)):
        return True
    return value<0 and any(any(math.isclose(-value,n,rel_tol=1e-12,abs_tol=1e-12) for n in numeric_tokens(s))
                           for s in re.findall(r'\([^()]+\)',text))


def header_cell_grounding(spans: list[str],labels: list[str],value: float,context: str,
                          constraints: Constraints) -> dict | None:
    """Anchor partial verbatim quotations to one original Markdown table cell.

    Headers and rows must belong to the SAME source table. No new value is
    calculated or substituted; ambiguous coordinate matches remain unsupported.
    """
    groups=[];group=[]
    for line in [*context.splitlines(),'']:
        if line.count('|')>=2:group.append(line)
        elif group:groups.append(group);group=[]
    cells=lambda line:[c.strip() for c in line.strip().strip('|').split('|')]
    numeric_quotes=[line.strip() for span in spans for line in span.splitlines() if quoted_value(value,line)]
    years=re.findall(r'(?<!\d)(?:19|20)\d{2}(?!\d)',str(constraints.temporal_scope or ''))
    year=years[0] if len(set(years))==1 else None
    matches={}
    for table in groups:
        if len(table)<3:continue
        header=cells(table[0]);separator=cells(table[1])
        if len(separator)!=len(header) or not all(re.fullmatch(r':?-+:?',c) for c in separator):continue
        data=[(line,cells(line)) for line in table[2:] if len(cells(line))==len(header)]
        timecols=[i for i,h in enumerate(header) if norm(h) in {'year','fiscal year','date','period','年份','年度','日期','时间','报告期'}]
        entitycols=[i for i,h in enumerate(header) if norm(h) in {'company','entity','公司','公司名称','企业','主体'}]
        scope=norm(str(constraints.entity_scope or ''))
        exact_entity_cols=[i for i in entitycols if any(norm(row[i])==scope for _,row in data)]
        for line,row in data:
            if not any(norm(q) in norm(line) for q in numeric_quotes):continue
            if any(norm(row[i])!=scope for i in exact_entity_cols):continue
            if year and any((ys:=re.findall(r'(?<!\d)(?:19|20)\d{2}(?!\d)',row[i])) and year not in ys for i in timecols):continue
            for column,cell in enumerate(row):
                if column in timecols or not quoted_value(value,cell):continue
                column_label=any(norm(label) in norm(header[column]) for label in labels if label)
                row_label=any(any(norm(label) in norm(c) for label in labels if label) for c in row)
                column_years=re.findall(r'(?<!\d)(?:19|20)\d{2}(?!\d)',header[column])
                if not column_label and not (row_label and (not year or not column_years or year in column_years)):continue
                proof={'header':table[0],'row':line,'column_index':column,'value':value}
                matches[(table[0],line,column)]=proof
    return next(iter(matches.values())) if len(matches)==1 else None


def grounded(binding: dict, goal: Goal, context: str, aliases: list[str]):
    value = finite(binding["value"])
    if not isinstance(binding.get('metric'),str):raise ProtocolError('Missing binding metric')
    if norm(binding['metric']) != norm(goal.metric) or Constraints.parse(binding["constraints"]) != goal.constraints:
        raise EvidenceError("OES changed the requested metric or constraints")
    confidence = finite(binding["confidence"])
    if not 0 <= confidence <= 1:
        raise ProtocolError("Invalid evidence confidence")
    snippet = binding.get("context")
    if not isinstance(snippet, str) or not snippet.strip():
        raise ProtocolError("OES omitted the evidence snippet")
    squash = lambda s: " ".join(s.casefold().split())
    spans=binding_spans(binding,context)
    names=[goal.metric,*aliases]
    alignment=binding.get('label_alignment')
    if alignment is not None:
        if not isinstance(alignment,dict):raise ProtocolError('Invalid label alignment')
        if alignment.get('kind') in {'translation','semantic_alias'}:
            label=alignment.get('source_label')
            explanation=alignment.get('explanation')
            if not isinstance(label,str) or not label.strip() or not isinstance(explanation,str) or not explanation.strip():
                raise ProtocolError('Translation requires an explicit quoted source label and explanation')
            if not any(norm(label) in norm(s) for s in spans):
                raise EvidenceError('Translation requires an explicit quoted source label and explanation')
            cjk=lambda s:bool(re.search(r'[\u3400-\u9fff]',s))
            latin=lambda s:bool(re.search(r'[A-Za-z]',s))
            if alignment.get('kind')=='translation' and not ((cjk(label) and latin(goal.metric) and not cjk(goal.metric))
                    or (cjk(goal.metric) and latin(label) and not cjk(label))):
                raise ProtocolError('Unregistered same-language aliases are not translations')
            names.append(label)
    labelled=[s for s in spans if any(squash(a) in squash(s) for a in names if a)]
    if not labelled:
        raise EvidenceError('Evidence snippet has no metric label or registered alias')
    if not (any(quoted_value(value,s) for s in labelled) or header_cell_grounding(spans,names,value,context,goal.constraints)):
        raise EvidenceError('OES returned a computed or unquoted number')
    return value


def vote(candidates: list[dict]) -> dict | None:
    """Unique plurality of VALID paths, with explicit unit normalization and no averaging.

    Ties abstain. The paper does not state tie handling or a numerical tolerance;
    the 1e-9 floating-point tolerance is an implementation choice, not answer tolerance.
    """
    from .metrics import normalized
    groups: list[list[dict]] = []
    for candidate in candidates:
        value, dimension = normalized(candidate["value"], candidate["meta"])
        for group in groups:
            other, other_dimension = normalized(group[0]["value"], group[0]["meta"])
            if dimension == other_dimension and math.isclose(value, other, rel_tol=1e-9, abs_tol=1e-12):
                group.append(candidate)
                break
        else:
            groups.append([candidate])
    if not groups:
        return None
    groups.sort(key=lambda g: (-len(g), g[0]["path_id"]))
    if len(groups) > 1 and len(groups[0]) == len(groups[1]):
        return None
    return groups[0][0]


class GBFR:
    def __init__(self, graph: MetricGraph, client, execution_timeout: float = 5):
        self.graph, self.client, self.execution_timeout = graph, client, execution_timeout

    async def predict(self, question: str, context: str) -> Prediction:
        # All memoization, including negative results, is scoped to THIS document/query.
        session = _Query(self, question, context)
        try:
            return await session.run()
        except Exception as exc:
            exc.gbfr_trace = {"events": session.events}
            raise
        finally:
            pending = [t for t in [*session.resolutions.values(), *session.directs.values()] if not t.done()]
            for task in pending:
                task.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)


class _Query:
    def __init__(self, model: GBFR, question: str, context: str):
        self.model, self.question, self.context = model, question, context
        self.graph, self.client = model.graph, model.client
        self.resolutions: dict[str, asyncio.Task] = {}
        self.directs: dict[str, asyncio.Task] = {}
        self.events: list[dict] = []

    def canonical(self, goal: Goal) -> Goal:
        node = self.graph.find(goal.metric)
        return Goal(node.name, goal.constraints) if node else goal

    def key(self, goal: Goal) -> str:
        return dumps({"metric": goal.metric, "constraints": asdict(goal.constraints)})

    async def direct(self, goal: Goal) -> Resolution:
        goal = self.canonical(goal)
        key = self.key(goal)
        if key not in self.directs:
            self.directs[key] = asyncio.create_task(self._direct(goal))
        return await self.directs[key]

    async def _direct(self, goal: Goal) -> Resolution:
        node = self.graph.find(goal.metric)
        aliases = node.aliases if node else []
        var = {"var_name": "v1", **asdict(goal), "aliases": aliases,
               "definition": node.definition if node else ""}
        response = await self.client.json("OES", render(
            "evidence_seeking", context=self.context, var_list=dumps([var]), format=EVIDENCE_FORMAT))
        self.events.append({"operator": "OES", "goal": asdict(goal), "response": response})
        if not {"found", "var_bindings", "missing_vars", "notes"} <= response.keys():
            raise ProtocolError("Missing OES fields")
        bindings, missing = response["var_bindings"], response["missing_vars"]
        if not isinstance(bindings, dict) or not isinstance(missing, list):
            raise ProtocolError("Invalid OES bindings")
        if not bindings:
            if response["found"] is not False or missing != ["v1"]:
                raise ProtocolError("OES must explicitly report v1 missing")
            if not isinstance(response["notes"], str) or not response["notes"].strip():
                raise ProtocolError("OES must explain missing evidence in notes")
            return Resolution(None, reason=response.get("notes") or "No matching direct evidence")
        if set(bindings) != {"v1"} or missing or response["found"] is not True:
            raise ProtocolError("OES returned contradictory evidence state")
        binding = bindings["v1"]
        try:
            alignment=binding.get('label_alignment') or {}
            if alignment.get('kind')=='semantic_alias':
                source_node=self.graph.find(alignment.get('source_label',''))
                declared={norm(a) for a in [goal.metric,*aliases]}
                if node and source_node and node.name!=source_node.name and norm(alignment.get('source_label','')) not in declared:
                    raise EvidenceError('Source label resolves to a different FMKG concept')
            value = grounded(binding, goal, self.context, aliases)
        except EvidenceError as exc:
            self.events.append({'operator':'evidence_rejected','goal':asdict(goal),'reason':str(exc)})
            return Resolution(None,reason=str(exc))
        meta = dict(goal.constraints.meta)
        if 'observed_meta' in binding:
            observed = binding['observed_meta']
            if not isinstance(observed, dict) or set(observed) != {'currency', 'scale', 'unit'}:
                raise ProtocolError('Invalid observed evidence units')
            from .metrics import canonical
            from decimal import Decimal
            try:
                canonical(Decimal(1), observed)
            except ValueError as exc:
                raise ProtocolError('Unsupported observed evidence units') from exc
            requested_currency = goal.constraints.meta.get('currency')
            if known(requested_currency) and known(observed.get('currency')):
                requested = canonical(Decimal(1), {'currency': requested_currency})[1][0]
                actual = canonical(Decimal(1), {'currency': observed['currency']})[1][0]
                if requested != actual:
                    self.events.append({'operator':'evidence_rejected','goal':asdict(goal),'reason':'Evidence currency contradicts requested constraint'})
                    return Resolution(None,reason='Evidence currency contradicts requested constraint')
            for k, v in observed.items():
                if known(v):
                    meta[k] = v
        spans=binding_spans(binding,self.context)
        alignment=binding.get('label_alignment') or {}
        alignment_note=response['notes'] or alignment.get('explanation')
        matched_aliases=[a for a in aliases if norm(a) in norm(' '.join(spans))]
        if not alignment_note and matched_aliases:
            alignment_note='Registered FMKG aliases matched verbatim: '+dumps(matched_aliases)
        if norm(goal.metric) not in norm(' '.join(spans)):
            if not isinstance(alignment_note,str) or not alignment_note.strip():
                raise ProtocolError("OES must explain its alias mapping in notes")
        path = {"path_id": "direct:" + self.key(goal), "subgoals": [asdict(goal)],
                "evidence": bindings, "computation": {"kind": "direct extraction"},
                'alias_mapping':{'canonical_metric':goal.metric,
                    'matched_registered_aliases':matched_aliases,
                    'source':'FMKG registered aliases','operator_notes':alignment_note,
                    'explicit_label_alignment':alignment or None},
                'verified_evidence_spans':spans,
                'table_coordinate_support':header_cell_grounding(spans,[goal.metric,*aliases,alignment.get('source_label','')],value,self.context,goal.constraints),
                "value": value, "meta": meta}
        return Resolution(value, meta, [path])

    async def resolve(self, goal: Goal) -> Resolution:
        goal = self.canonical(goal)
        key = self.key(goal)
        if key not in self.resolutions:
            self.resolutions[key] = asyncio.create_task(self._resolve(goal))
        return await self.resolutions[key]

    async def _resolve(self, goal: Goal) -> Resolution:
        direct = await self.direct(goal)
        if direct.value is not None:
            return direct
        node = self.graph.find(goal.metric)
        # Algorithm 1 lines 10--14: an unresolved atomic node terminates the path.
        if node is None or node.kind == "atomic":
            return direct
        formulas = [*node.formulas, *self.graph.inverses(node.name)]
        self.events.append({"operator": "OMD", "goal": asdict(goal),
                            "paths": [{"id": f.id, "direction": f.direction,
                                       "formula": f.source_formula} for f in formulas]})
        candidates = await asyncio.gather(*(self.compute_path(goal, f) for f in formulas))
        candidates = [c for c in candidates if c is not None]
        if not candidates:
            return Resolution(None, reason="All graph-grounded derivations have missing operands or undefined values")
        decisions = await self.client.json("Verify", render(
            'verification',query=('Verify ONLY the current metric subgoal: '+dumps(asdict(goal))
                +'. This is an intermediate resolution, not a complete answer to the original question. '
                 'Check its supplied formula, evidence and constraints. Percentage and ratio are explicitly convertible display forms. '
                 'Original question for background only: '+self.question), context=self.context,
            candidate_paths=dumps(candidates), format=VERIFY_FORMAT
            +'\nThe exact top-level path_id strings to decide are: '+dumps([c['path_id'] for c in candidates])
            +'. Copy these strings exactly; nested evidence path IDs are not additional decisions.'))
        self.events.append({"operator": "Verify", "goal": asdict(goal), "candidate_paths": candidates,
                            "response": decisions})
        ds = decisions.get("path_decisions")
        if not isinstance(ds, list) or len(ds) != len(candidates):
            raise ProtocolError("Verify must decide every candidate in one call")
        by_id = {c["path_id"]: c for c in candidates}
        seen, valid = set(), []
        for d in ds:
            if d.get('path_id') is None and len(candidates)==1:
                # The sole decision has one possible recipient. This repairs
                # only our bookkeeping ID, never the model's decision/value.
                # The raw response remains unchanged in the trace and cache.
                d={**d,'path_id':candidates[0]['path_id'],'id_assignment':'sole_candidate'}
            ident = d.get("path_id")
            if ident not in by_id or ident in seen or d.get("decision") not in {"VALID", "INVALID"}:
                raise ProtocolError("Invalid or duplicated verification decision")
            if not isinstance(d.get("justification"), str) or not d["justification"].strip():
                raise ProtocolError("Verify omitted its justification")
            seen.add(ident)
            by_id[ident]["verification"] = d
            if d["decision"] == "VALID":
                valid.append(by_id[ident])
        chosen = vote(valid)
        if chosen is None:
            return Resolution(None, paths=candidates, reason="No validated consensus")
        return Resolution(chosen["value"], chosen["meta"], [chosen])

    async def compute_path(self, goal: Goal, formula: Formula) -> dict | None:
        try:
            goals = [operand_goal(o, goal.constraints) for o in formula.operands]
        except AssetError as exc:
            self.events.append({'operator': 'path_pruned', 'path_id': formula.id, 'reason': str(exc)})
            return None
        # Limited 1-hop upward search: parent and siblings must be in the context.
        resolver = self.direct if formula.direction == "up" else self.resolve
        if formula.direction=='up' and formula.operands and formula.operands[0].symbol=='parent_value':
            parent=await self.direct(goals[0])
            if parent.value is None:
                self.events.append({'operator':'path_pruned','path_id':formula.id,'reason':'missing_inverse_parent','goals':[asdict(goals[0])]})
                return None
            children=[parent,*await asyncio.gather(*(self.direct(g) for g in goals[1:]))]
        else:
            children = await asyncio.gather(*(resolver(g) for g in goals))
        if any(c.value is None for c in children):
            self.events.append({"operator": "path_pruned", "path_id": formula.id,
                                "reason": "missing_operand", "goals": [asdict(g) for g in goals]})
            return None
        values = {o.metric: c.value for o, c in zip(formula.operands, children)}
        requirements = [{"key": o.metric, "symbol": o.symbol, "metric": o.metric, "constraints": asdict(g.constraints),
                         "value": c.value, "meta": c.meta} for o, g, c in zip(formula.operands, goals, children)]
        program = await self.client.complete("OPE.metric", render(
            "metric_program", indicator_name=goal.metric,
            formula_expr=formula.source_formula + "\nExact symbolic RHS: " + formula.expression,
            required_vars=dumps(requirements)) + EXECUTION_ENVIRONMENT
            + '\nApply the supplied symbolic expression. Normalize compatible inputs using their explicit meta before arithmetic; never invent an exchange rate. '
              'Record currency, scale and unit of the result in trace.output_meta; use null when unknown.')
        program = clean_program(program)
        result = await execute(program, values, self.model.execution_timeout)
        self.events.append({"operator": "OPE.metric", "path_id": formula.id,
                            "program": program, "inputs": values, "execution": result})
        if result is None:
            return None
        output_meta = result['trace'].get('output_meta', {})
        if not isinstance(output_meta, dict):
            raise ProtocolError('Invalid metric output_meta')
        meta = {**goal.constraints.meta, **output_meta, **formula.meta}
        return {"path_id": formula.id, "direction": formula.direction,
                'goal':asdict(goal),
                "subgoals": [asdict(g) for g in goals],
                "evidence": {o.symbol: c.paths for o, c in zip(formula.operands, children)},
                "computation": {"formula": formula.source_formula, "symbolic_rhs": formula.expression,
                                "program": program, "inputs": values, "trace": result["trace"]},
                "value": result["value"], "meta": meta}

    async def run(self) -> Prediction:
        routing=('Graph routing: preserve requested named financial metrics as subgoals. Expanding a metric into its formula components belongs to OMD, not OQA. '
              'For a question asking for one named financial metric, use that metric as one subgoal and sum as the identity operator. '
              'For an outer comparison or change, keep the named metric at each requested entity/period as separate subgoals; do not inline its financial formula. '
              'Dimensionless financial ratios, rates and percentages have no currency or monetary scale: use null for currency and scale, even if their monetary operands are in USD millions. '
              'For a known metric use its canonical name exactly, without appending method wording such as "using average equity" or a year. '
              'These hints only align known names; do not discard a meaningful adjusted/entity/period qualifier to force a match. '
              'Query-only canonical-name hints: '+dumps(metric_hints(self.graph,self.question)))
        prompt=render('query_analysis',query=self.question,context=self.context,example='')
        marker='=== Subgoals (very important) ==='
        prompt=prompt.replace(marker,routing+'\n\n'+marker,1)
        response = await self.client.json('OQA',prompt)
        self.events.append({"operator": "OQA", "response": response})
        plan = Plan.parse(response)
        values = await asyncio.gather(*(self.resolve(g) for g in plan.subgoals))
        if any(v.value is None for v in values):
            return Prediction("abstained", None, {}, plan.precision,
                              {"events": self.events, "subgoal_results": [asdict(v) for v in values]},
                              "At least one required subgoal could not be grounded")
        evidence = [{"var_name": f"v{i+1}", **asdict(g), "value": v.value,
                     "meta": v.meta, "paths": v.paths} for i, (g, v) in enumerate(zip(plan.subgoals, values))]
        program = clean_program(await self.client.complete("OPE.final", render(
            "final_program", query=self.question, context=self.context,
            reasoning_type=plan.reasoning_type + "; apply ONLY operator=" + plan.operator,
            evidences=dumps(evidence)) + "\nOutput precision requirement: " + str(plan.precision)
            + "\nInclude output_meta in trace with currency, scale and unit of the returned value."
            + " Use only supported attributes; use null when unknown." + EXECUTION_ENVIRONMENT))
        inputs = {e["var_name"]: e["value"] for e in evidence}
        result = await execute(program, inputs, self.model.execution_timeout,
                               allow_boolean_result=plan.operator == "compare")
        self.events.append({"operator": "OPE.final", "program": program, "inputs": inputs, "execution": result})
        if result is None:
            return Prediction("abstained", None, {}, plan.precision, {"events": self.events}, "Undefined final calculation")
        # Final unit metadata has its own explicit slot in trace. Never infer it from gold.
        meta = result["trace"].get("output_meta", {})
        if not isinstance(meta, dict):
            raise ProtocolError("Invalid output_meta")
        return Prediction("answered", result["value"], meta, plan.precision,
                          {"events": self.events, "evidence": evidence})
