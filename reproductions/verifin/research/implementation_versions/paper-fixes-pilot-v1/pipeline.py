"""Main-model path: question-only plan/authority/facts fixed before claim parsing."""
from __future__ import annotations
from dataclasses import asdict
from decimal import Decimal
import json
from verifiqa.agent.claim_classifier import decompose_question, parse_claimed_answer
from verifiqa.agent.fact_extractor import extract_facts_parallel
from verifiqa.agent.agent import _quote_grounded, _normalize_text
from verifiqa.formulas.evaluator import formula_variables
from .authority import authorize
from .grounding import Filing, Unresolved, conversion, reporting_tolerance, unit, validate_dimensions
from .solver import verify, Unsupported

class PaperVerifier:
    def __init__(self, client, *, workers=4):
        self.client, self.workers = client, workers

    def verify(self, question, answer, evidence, filing):
        audit = {'repair_attempts':0, 'candidate_independent_authority':True}
        try:
            try:spec=decompose_question(question,self.client,evidence_text=evidence)
            except (json.JSONDecodeError,KeyError,TypeError,ValueError) as exc:
                raise Unresolved('unusable_verification_plan:'+type(exc).__name__) from exc
            if not spec.roles: raise Unresolved('verification_plan_has_no_roles')
            if not spec.claim_unit: raise Unresolved('verification_plan_has_no_unit')
            # Exact linkbase children bind directly (§3.5), without asking an LLM
            # to read values we already have in authoritative tagged facts.
            initial_spec=spec
            try:spec,authority=authorize(spec,question,evidence,filing,{})
            except Unresolved:authority=None
            if authority and authority['kind']=='filing_calculation_linkbase':
                extracted={}
            else:
                # Extracted values are proposals only, never admitted as facts.
                spec=initial_spec
                extracted=extract_facts_parallel(spec,evidence,self.client,self.workers)
                spec,authority=authorize(spec,question,evidence,filing,extracted)
            if not formula_variables(spec.formula) <= {r.name for r in spec.roles}:
                raise Unresolved('formula_role_mismatch')
            norm = _normalize_text(evidence)
            bindings = []
            for role in spec.roles:
                proposed = extracted.get(role.name)
                if proposed and proposed.source_quote and not _quote_grounded(proposed.source_quote, norm):
                    raise Unresolved('extraction_quote_not_in_evidence:'+role.name)
                role_unit = proposed.unit if proposed else spec.claim_unit
                # Registry roles can have different measures (USD/shares, etc.).
                if authority['kind'] == 'filing_calculation_linkbase': role_unit = spec.claim_unit
                kind, _ = unit(role_unit)
                output_kind, _ = unit(spec.claim_unit)
                if kind not in {'pure','shares'}:
                    role_unit = spec.claim_unit if kind == output_kind else kind.upper()
                elif kind == 'shares': role_unit = 'shares'
                bindings.append(filing.bind(role, role_unit, spec.period, proposed))
            validate_dimensions(spec.formula,bindings,spec.claim_unit)
            tau, tau_source = reporting_tolerance(question, spec.claim_unit, bindings, evidence)
            audit.update(plan=asdict(spec), formula_authority=authority, bindings=bindings,
                         tolerance=tau, tolerance_source=tau_source)
            # First and only candidate-aware call. No answer is visible upstream.
            try:claimed=parse_claimed_answer(question,answer,spec,self.client)
            except (json.JSONDecodeError,KeyError,TypeError,ValueError) as exc:
                raise Unresolved('unusable_numeric_claim:'+type(exc).__name__) from exc
            if claimed.value is None: raise Unresolved('no_usable_numeric_claim')
            scale = conversion(claimed.unit or spec.claim_unit, spec.claim_unit)
            candidate = Decimal(str(claimed.value))*scale
            facts = {b['role']: b['value'] for b in bindings}
            result = verify(spec.formula, facts, candidate, tau)
            result.update(claimed_value=str(candidate), claimed_unit=spec.claim_unit, audit=audit)
            return result
        except (Unresolved, Unsupported) as exc:
            return {'status':'ABSTAIN', 'reason':str(exc), 'audit':audit}
