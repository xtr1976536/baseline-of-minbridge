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


def currency_matches(a,b):
    if not known(a) or not known(b):return True
    if '$' in {a,b}:
        return ({a,b}-{'$'}) <= {'USD','AUD','CAD','HKD','NZD','SGD'}
    return a==b


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
            result.append({'query_mention':text[start:end],'canonical_metric':name,'definition':graph.nodes[name].definition[:600]})
    return result


def numeric_tokens(text: str) -> list[float]:
    return [float(x.replace(",", "")) for x in re.findall(
        r"(?<![\d.])[+-]?(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?|\.\d+)(?!\d|\.\d)", text)]


def verbatim_spans(snippet: str, context: str) -> list[str]:
    from .evidence import copied_span
    span=copied_span(snippet,context)
    if span:return [span]
    spans=[copied_span(s,context) for s in re.split(r'\n|(?<=[.!?。！？])\s+',snippet.strip())]
    if spans and all(spans):return spans
    raise EvidenceError('OES snippet is not a verbatim context span')



def binding_spans(binding: dict, context: str) -> list[str]:
    from .evidence import verified_quotes
    return verified_quotes(binding,context)



def quoted_value(value: float,text: str) -> bool:
    if any(math.isclose(value,n,rel_tol=1e-12,abs_tol=1e-12) for n in numeric_tokens(text)):
        return True
    return value<0 and any(any(math.isclose(-value,n,rel_tol=1e-12,abs_tol=1e-12) for n in numeric_tokens(s))
                           for s in re.findall(r'\([^()]+\)',text))


def header_cell_grounding(spans: list[str], labels: list[str], value: float, context: str,
                          constraints: Constraints) -> dict | None:
    from .evidence import table_support
    return table_support(context,labels,value,constraints)



def grounded(binding: dict, goal: Goal, context: str, aliases: list[str], notes=None, proof=None):
    from .evidence import key,support
    value=finite(binding['value'])
    if not isinstance(binding.get('metric'),str):raise ProtocolError('Missing binding metric')
    names={key(n) for n in [goal.metric,*aliases]}
    source_label=binding.get('source_label') or (binding.get('label_alignment') or {}).get('source_label')
    if source_label and notes:names.add(key(source_label))
    if key(binding['metric']) not in names:
        raise EvidenceError('OES changed the requested metric or constraints')
    requested=Constraints.parse(asdict(goal.constraints));claimed=Constraints.parse(binding['constraints'])
    scope_key=lambda v:re.sub(r'\s+',' ',dumps(v).casefold()).strip()
    for field in ('temporal_scope','entity_scope'):
        a,b=getattr(requested,field),getattr(claimed,field)
        if known(a) and known(b) and scope_key(a)!=scope_key(b):raise EvidenceError('OES changed the requested metric or constraints')
    a,b=requested.meta,claimed.meta
    if not currency_matches(a['currency'],b['currency']):
        raise EvidenceError('OES changed the requested metric or constraints')
    unit=lambda u:'ratio' if u=='percentage' else u
    if known(a['unit']) and known(b['unit']) and unit(a['unit'])!=unit(b['unit']):
        raise EvidenceError('OES changed the requested metric or constraints')
    if 'confidence' in binding:
        confidence=finite(binding['confidence'])
        if not 0<=confidence<=1:raise ProtocolError('Invalid evidence confidence')
    if proof is None:support(binding,goal,context,aliases,notes)
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
    def __init__(self, graph: MetricGraph, client, execution_timeout: float = 5, *, evidence_policy='strict'):
        if evidence_policy not in {'paper','strict'}:raise ValueError('Unknown evidence policy')
        self.graph, self.client, self.execution_timeout = graph, client, execution_timeout
        self.evidence_policy=evidence_policy

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
        return await asyncio.shield(self.directs[key])

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
        normalizations=[]
        if isinstance(bindings,list) and len(bindings)==1 and isinstance(bindings[0],dict):
            candidate=bindings[0]
            if candidate.get('var_name','v1')=='v1':bindings={'v1':candidate};normalizations.append('sole_named_binding')
        if not isinstance(bindings, dict) or not isinstance(missing, list):
            raise ProtocolError("Invalid OES bindings")
        if not bindings:
            if response["found"] is not False:
                raise ProtocolError("OES must explicitly report v1 missing")
            if not isinstance(response["notes"], str) or not response["notes"].strip():
                raise ProtocolError("OES must explain missing evidence in notes")
            return Resolution(None, reason=response.get("notes") or "No matching direct evidence")
        if set(bindings) != {"v1"} or missing or response["found"] is not True:
            raise ProtocolError("OES returned contradictory evidence state")
        if not isinstance(bindings['v1'],dict):raise ProtocolError('A variable binding must be an object')
        binding = dict(bindings["v1"])
        binding.setdefault('metric',goal.metric)
        binding.setdefault('constraints',asdict(goal.constraints))
        if isinstance(binding.get('value'),str):
            from .metrics import parse_number
            parsed=parse_number(binding['value'])
            if parsed is not None:
                binding['value']=float(parsed.value)
                binding['observed_meta']={**parsed.meta,**{k:v for k,v in binding.get('observed_meta',{}).items() if known(v)}}
                normalizations.append('numeric_text_scalar')
            else:
                from .evidence import interval_numbers
                interval=interval_numbers(binding['value'])
                if interval is None:raise ProtocolError('OES value is not a scalar number')
                binding['value']=interval
        if isinstance(binding.get('value'),(list,dict)):
            from .evidence import support
            candidates=list(binding['value'].values()) if isinstance(binding['value'],dict) else binding['value']
            supported={}
            for candidate in candidates:
                if type(candidate) not in {int,float}:continue
                try:
                    support({**binding,'value':candidate},goal,self.context,aliases,response['notes'])
                    supported[finite(candidate)]=candidate
                except EvidenceError:continue
            if len(supported)!=1:raise ProtocolError('Structured evidence does not identify one source-grounded scalar under the requested constraints')
            binding['value']=next(iter(supported.values()))
            normalizations.append('unique_source_coordinate_selection')
        binding['value']=finite(binding.get('value'))
        bindings={'v1':binding}
        audit={'status':'supported'}
        try:
            from .evidence import support
            proof=support(binding,goal,self.context,aliases,response['notes'])
            value = grounded(binding, goal, self.context, aliases,response['notes'],proof)
        except EvidenceError as exc:
            if self.model.evidence_policy=='strict':
                self.events.append({'operator':'evidence_rejected','goal':asdict(goal),'reason':str(exc)})
                return Resolution(None,reason=str(exc))
            # Section 4.1 uses the LLM's semantic evidence decision. Algorithm
            # 1 returns an OES value directly, without a second lexical gate.
            # Preserve our supplementary checker as an audit, not an invented
            # model decision. The unmodified OES response remains in the trace.
            audit={'status':'warning','reason':str(exc),'policy':'paper-oes-semantic-decision'}
            self.events.append({'operator':'evidence_audit','goal':asdict(goal),**audit})
            proof={'spans':[],'table_coordinate_support':None}
            value=finite(binding['value'])
        meta = dict(goal.constraints.meta)
        if 'observed_meta' in binding:
            observed = binding['observed_meta']
            if not isinstance(observed, dict):
                raise ProtocolError('Invalid observed evidence units')
            from .units import normalize_meta
            from .metrics import canonical
            from decimal import Decimal
            try:
                observed=normalize_meta(observed)
                canonical(Decimal(1), observed)
            except ValueError as exc:
                raise ProtocolError('Unsupported observed evidence units') from exc
            requested_currency = goal.constraints.meta.get('currency')
            if known(requested_currency) and known(observed.get('currency')):
                if not currency_matches(requested_currency,observed['currency']):
                    if self.model.evidence_policy=='strict':
                        self.events.append({'operator':'evidence_rejected','goal':asdict(goal),'reason':'Evidence currency contradicts requested constraint'})
                        return Resolution(None,reason='Evidence currency contradicts requested constraint')
                    audit={'status':'warning','reason':'Evidence currency contradicts requested constraint','policy':'paper-oes-semantic-decision'}
                    self.events.append({'operator':'evidence_audit','goal':asdict(goal),**audit})
            for k, v in observed.items():
                if known(v):
                    meta[k] = v
        spans=proof['spans']
        alignment=binding.get('label_alignment') or {}
        alignment_note=response['notes'] or alignment.get('explanation')
        matched_aliases=[a for a in aliases if norm(a) in norm(' '.join(spans))]
        if not alignment_note and matched_aliases:
            alignment_note='Registered FMKG aliases matched verbatim: '+dumps(matched_aliases)
        path = {"path_id": "direct:" + self.key(goal), "subgoals": [asdict(goal)],
                "evidence": bindings, "computation": {"kind": "direct extraction"},
                'alias_mapping':{'canonical_metric':goal.metric,
                    'matched_registered_aliases':matched_aliases,
                    'source':'FMKG aliases or OES source-label explanation','operator_notes':alignment_note,
                    'explicit_label_alignment':alignment or None},
                'verified_evidence_spans':spans,
                'table_coordinate_support':proof['table_coordinate_support'],
                'protocol_normalizations':normalizations,
                'supplementary_evidence_audit':audit,
                "value": value, "meta": meta}
        return Resolution(value, meta, [path])

    async def resolve(self, goal: Goal) -> Resolution:
        goal = self.canonical(goal)
        key = self.key(goal)
        if key not in self.resolutions:
            self.resolutions[key] = asyncio.create_task(self._resolve(goal))
        return await asyncio.shield(self.resolutions[key])

    async def _resolve(self, goal: Goal) -> Resolution:
        direct = await self.direct(goal)
        if direct.value is not None:
            return direct
        node = self.graph.find(goal.metric)
        # Algorithm 1 lines 10--14: an unresolved atomic node terminates the path.
        if node is None or node.kind == "atomic":
            return direct
        event={"operator":"OMD","goal":asdict(goal),'paths':[{'id':f.id,'direction':f.direction,'formula':f.source_formula} for f in node.formulas]}
        self.events.append(event)
        async def upward():
            parents=self.graph.inverse_parents(node.name)
            constraints=[Constraints.parse({**asdict(goal.constraints),'meta':{'currency':None,'scale':None,'unit':None,**f.meta}}) for _,f in parents]
            values=await asyncio.gather(*(self.direct(Goal(p,c)) for (p,_),c in zip(parents,constraints)))
            available={p for (p,_),v in zip(parents,values) if v.value is not None}
            if not available:return []
            inverses=await self.graph.inverses_for(node.name,available)
            event['paths'].extend({'id':f.id,'direction':f.direction,'formula':f.source_formula} for f in inverses)
            return await asyncio.gather(*(self.compute_path(goal,f) for f in inverses))
        branches=await asyncio.gather(*(self.compute_path(goal,f) for f in node.formulas),upward())
        candidates=[*branches[:-1],*branches[-1]]
        candidates = [c for c in candidates if c is not None]
        if not candidates:
            return Resolution(None, reason="All graph-grounded derivations have missing operands or undefined values")
        decisions = await self.client.json("Verify", render(
            'verification',query=('Verify ONLY the current metric subgoal: '+dumps(asdict(goal))
                +'. This is an intermediate resolution, not a complete answer to the original question. '
                 'Check its supplied formula, evidence and constraints. Percentage and ratio are explicitly convertible display forms. '
                 'Original question for background only: '+self.question), context=self.context,
            candidate_paths=dumps(candidates), format=dumps({'path_decisions':[{'path_id':c['path_id'],'decision':'VALID or INVALID','justification':'short reason'} for c in candidates]})
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
            if not isinstance(d,dict):raise ProtocolError('A path decision must be an object')
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
        async def required(goals):
            # All operands start in parallel. A missing required operand is
            # already a proof that this path cannot produce a value. Stop
            # waiting for that path's remaining operands, without cancelling
            # shared resolutions needed by other candidate paths.
            tasks=[asyncio.create_task(resolver(g)) for g in goals]
            indices={task:i for i,task in enumerate(tasks)}
            pending=set(tasks);values=[None]*len(tasks)
            try:
                while pending:
                    done,pending=await asyncio.wait(pending,return_when=asyncio.FIRST_COMPLETED)
                    completed=[(task,task.result()) for task in done]
                    for task,value in completed:values[indices[task]]=value
                    if any(value.value is None for _,value in completed):return None
                return values
            finally:
                for task in pending:task.cancel()
                if pending:await asyncio.gather(*pending,return_exceptions=True)
        if formula.direction=='up' and formula.operands and formula.operands[0].symbol=='parent_value':
            parent=await self.direct(goals[0])
            if parent.value is None:
                self.events.append({'operator':'path_pruned','path_id':formula.id,'reason':'missing_inverse_parent','goals':[asdict(goals[0])]})
                return None
            rest=await required(goals[1:])
            children=[parent,*rest] if rest is not None else None
        else:
            children = await required(goals)
        if children is None or any(c.value is None for c in children):
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
              'Explicit formula result units (when provided) take priority over a requested display preference: '+dumps(formula.meta)+'. '
              'Return the result in the target\'s reporting scale when specified; otherwise preserve the source reporting unit. '
              'Record currency, scale and unit in trace.output_meta. Python unknowns are None, never JSON null. '
              'Use scale="ones" only when the number is in unscaled base units.')
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
        from .units import result_meta
        normalized_meta=result_meta(meta)
        if normalized_meta!=meta:result['trace']['effective_output_meta']=normalized_meta
        meta=normalized_meta
        return {"path_id": formula.id, "direction": formula.direction,
                'goal':asdict(goal),
                "subgoals": [asdict(g) for g in goals],
                "evidence": {o.symbol: c.paths for o, c in zip(formula.operands, children)},
                "computation": {"formula": formula.source_formula, "symbolic_rhs": formula.expression,
                                "program": program, "inputs": values, "trace": result["trace"]},
                "value": result["value"], "meta": meta}

    async def run(self) -> Prediction:
        routing=('Graph routing: extract the required operands of the outer arithmetic as instructed below. '
              'Preserve a specific financial derived metric such as Return on Equity, EBITDA, or Enterprise Value as a subgoal; its financial formula belongs to OMD, not OQA. '
              'For a question asking for one such specific financial metric, use that metric as one subgoal and sum as the identity operator. '
              'Generic phrases such as total value, total amount, average amount or net position describe outer arithmetic, not a distinct financial formula node. '
              'For the total value of a transaction or securities, retrieve the matching quantity and per-unit price as product operands. '
              'For an outer comparison or change, keep the named metric at each requested entity/period as separate subgoals; do not inline its financial formula. '
              'Use BOTH the question and the table to identify the task: a return on an investment described by two dated stock/index values is an outer change ratio over those observed values, not a request for corporate Return on Investment from accounting profits/assets. '
              'Do not reinterpret an ordinary sum, balance difference, net position, or table-index comparison as an unrelated named corporate ratio. '
              'Canonical-name hints are optional: use them only when their financial definition matches the context. A product category called Equity is not balance-sheet shareholders equity. '
              'Dimensionless financial ratios, rates and percentages have no currency or monetary scale: use null for currency and scale, even if their monetary operands are in USD millions. '
              'For a known metric use its canonical name exactly, without appending method wording such as "using average equity" or a year. '
              'These hints only align known names; do not discard a meaningful adjusted/entity/period qualifier to force a match. '
              'Missing evidence is decided by OES, not by deleting subgoals. A numerical question MUST have at least one subgoal even when its value is absent. '
              'Return subgoals as objects with metric and constraints, not bare strings. '
              'For change, difference, percentage change, averages or comparisons of a metric, use the required period/entity values as separate subgoals. '
              'Each subgoal must resolve ONE scalar for ONE period/entity. Expand an enumerated list of years into separate subgoals. '
              'For a sum/average across named people or table rows, enumerate their individual values as subgoals, even if there is no printed total. '
              'The requested final percentage is not the unit of its monetary/count operands. Use the actual operand units from the document. '
              'Keep row/category restrictions (approved plans, subsidiaries, ratings, etc.) in entity_scope or metric qualifiers for EVERY relevant operand, never in unit. '
              'Use currency=$ when only a dollar sign is printed; USD requires explicit U.S./USD identification. '
              'Compare dates with the source table: OCR strings such as 2013 between two mm/dd/yy dates may encode a dash, not an additional requested year. '
              'If an explicit interval is an operand, request its lower and upper endpoints as separate scalar subgoals when both are needed. '
              'An interval is not a scalar: for its average or width, create lower-bound and upper-bound operand metrics, retaining the same period/entity. '
              'Preserve meaningful qualifiers, but do not embed period words or the outer operation into a metric name. '
              'Query-only canonical-name hints: '+dumps(metric_hints(self.graph,self.question)))
        from .prompts import QUERY_EXAMPLES
        prompt=render('query_analysis',query=self.question,context=self.context,example=QUERY_EXAMPLES)
        marker='=== Subgoals (very important) ==='
        prompt=prompt.replace(marker,routing+'\n\n'+marker,1)
        prompt+=('\nPlan contract check: subgoals MUST contain at least one metric/constraints object. '
                 'Missing values belong to the later Evidence Finder and do not make this plan empty. '
                 'List all required scalar operands; do not return an empty DirectRetrieval plan. '
                 'Retain all requested financial/category qualifiers in the metric or entity_scope. Return the four-key JSON object only.')
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
            + " Return a single scalar. Return the numeric display unit asked for in the question; if unspecified, preserve the document's reporting scale."
              " Record output_meta with currency, scale and unit; use Python None for unknowns, never JSON null."
              " If you convert to unscaled base units, explicitly set scale='ones'."
              " Do not round intermediate values; evaluation applies the requested precision."
              " For operator='change ratio', use (new - old) / old, preserving the signed base; never abs(old) unless explicitly requested."
              " A question asking the decrease by how much expects old - new; a signed change expects new - old."
              " Return percentages in percent units when the question asks a percentage, with output_meta.unit='percentage'."
              " vars is an ordinary dictionary; use only the supplied keys." + EXECUTION_ENVIRONMENT))
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
        from .units import result_meta
        effective_meta=result_meta(meta,plan.operator)
        if effective_meta!=meta:result['trace']['effective_output_meta']=effective_meta
        meta=effective_meta
        return Prediction("answered", result["value"], meta, plan.precision,
                          {"events": self.events, "evidence": evidence})
