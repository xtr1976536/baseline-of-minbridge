"""Main-model path: question-only plan/authority/facts fixed before claim parsing."""
from __future__ import annotations
from dataclasses import asdict,replace
from decimal import Decimal
import json
import re
from verifiqa.agent.claim_classifier import parse_claimed_answer
from .planning import decompose_question
from verifiqa.agent.fact_extractor import extract_facts_parallel
from verifiqa.agent.agent import _quote_grounded, _normalize_text
from verifiqa.formulas.evaluator import formula_variables
from .authority import authorize
from .grounding import Filing, Unresolved, conversion, reporting_tolerance, unit, validate_dimensions
from .solver import verify, Unsupported
from .semantics import normalize_plan,role_measure


def validate_explicit_statement_line(question,bindings,filing):
    """An allocation/note fact does not prove an explicitly reported income row."""
    if not (re.search(r'\b(?:directly|explicitly)\s+(?:outlined|reported|disclosed|listed)\b',question,re.I) and
            re.search(r'income statements?|statements? of (?:income|operations|earnings)',question,re.I)):
        return
    reported=set()
    for group in filing.data.get('calculations',[]):
        role=re.sub('[^a-z]','',group['role'].rsplit('/',1)[-1].lower())
        if re.fullmatch(r'(?:consolidated)?statements?of(?:income|operations|earnings)',role):
            reported.add(group['parent']);reported.update(c['concept'] for c in group['children'])
    if any(b['concept'] not in reported for b in bindings):
        raise Unresolved('requested_income_statement_line_not_established')

class PaperVerifier:
    def __init__(self, client, *, workers=4):
        self.client, self.workers = client, workers

    def verify(self, question, answer, evidence, filing):
        audit = {'repair_attempts':0, 'candidate_independent_authority':True}
        try:
            try:spec=decompose_question(question,self.client,evidence_text=evidence)
            except (json.JSONDecodeError,KeyError,TypeError,ValueError) as exc:
                raise Unresolved('unusable_verification_plan:'+type(exc).__name__) from exc
            spec,adjustments=normalize_plan(spec,question,evidence,filing)
            audit.update(plan=asdict(spec),plan_adjustments=adjustments)
            if not spec.roles: raise Unresolved('verification_plan_has_no_roles')
            if not spec.claim_unit: raise Unresolved('verification_plan_has_no_unit')
            # Exact linkbase and registry bindings do not need model-proposed
            # numbers (§3.5). Extraction is used only where source labels or
            # missing structural information are needed, before claim parsing.
            extracted={}
            try:spec,authority=authorize(spec,question,evidence,filing,{})
            except Unresolved as exc:
                if str(exc)=='unparsed_explicit_question_definition':raise
                authority=None
            if not authority:
                # Extracted values are proposals only, never admitted as facts.
                extracted=extract_facts_parallel(spec,evidence,self.client,self.workers)
                spec,authority=authorize(spec,question,evidence,filing,extracted)
            if not formula_variables(spec.formula) <= {r.name for r in spec.roles}:
                raise Unresolved('formula_role_mismatch')
            required=formula_variables(spec.formula)
            spec=replace(spec,roles=[r for r in spec.roles if r.name in required])
            norm = _normalize_text(evidence)
            audit.update(plan=asdict(spec),formula_authority=authority)
            bindings,need_proposals = [],[]
            for role in spec.roles:
                proposed = extracted.get(role.name)
                if proposed and proposed.source_quote and not _quote_grounded(proposed.source_quote, norm):
                    raise Unresolved('extraction_quote_not_in_evidence:'+role.name)
                role_unit=role_measure(role,spec.claim_unit,filing,proposed)
                try:bindings.append(filing.bind(role,role_unit,spec.period,proposed))
                except Unresolved as exc:
                    if role.name in extracted or str(exc).startswith(('missing_reporting_period:','quarter_requires_','ambiguous_role_period:')):raise
                    need_proposals.append(role)
            if need_proposals:
                extracted.update(extract_facts_parallel(replace(spec,roles=need_proposals),evidence,self.client,self.workers))
                for role in need_proposals:
                    proposed=extracted.get(role.name)
                    if proposed and proposed.source_quote and not _quote_grounded(proposed.source_quote,norm):
                        raise Unresolved('extraction_quote_not_in_evidence:'+role.name)
                    bindings.append(filing.bind(role,role_measure(role,spec.claim_unit,filing,proposed),spec.period,proposed))
            # Stable ordering makes the admitted plan independent of scheduling.
            by_role={b['role']:b for b in bindings};bindings=[by_role[r.name] for r in spec.roles]
            audit['bindings']=bindings
            validate_explicit_statement_line(question,bindings,filing)
            validate_dimensions(spec.formula,bindings,spec.claim_unit)
            tau, tau_source = reporting_tolerance(question, spec.claim_unit, bindings, evidence)
            audit.update(plan=asdict(spec), formula_authority=authority, bindings=bindings,
                         tolerance=tau, tolerance_source=tau_source)
            # First and only candidate-aware call. No answer is visible upstream.
            try:claimed=parse_claimed_answer(question,answer,spec,self.client)
            except (json.JSONDecodeError,KeyError,TypeError,ValueError) as exc:
                raise Unresolved('unusable_numeric_claim:'+type(exc).__name__) from exc
            if claimed.value is None: raise Unresolved('no_usable_numeric_claim')
            claim_unit=claimed.unit or spec.claim_unit
            if claim_unit.lower()=='other' and spec.claim_unit=='days':claim_unit='days'
            scale = conversion(claim_unit, spec.claim_unit)
            candidate = Decimal(str(claimed.value))*scale
            facts = {b['role']: b['value'] for b in bindings}
            result = verify(spec.formula, facts, candidate, tau)
            result.update(claimed_value=str(candidate), claimed_unit=spec.claim_unit, audit=audit)
            return result
        except (Unresolved, Unsupported) as exc:
            return {'status':'ABSTAIN', 'reason':str(exc), 'audit':audit}
