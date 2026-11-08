"""When the filing's XBRL contradicts the LLM evidence, the filing wins.

Previously a consistency conflict fell back to the LLM-only SMT, which stamped the
LLM's (wrong) answer VERIFIED. Now the LLM value assertions for bound facts are
stripped so the claim is checked against the filing's authoritative number, and the
normal answer-repair path recomputes the correct value.
"""
import re
import unittest
from types import SimpleNamespace

from verifiqa.pipeline import (
    _grounding_tier,
    _strip_claim_assertions,
    _strip_llm_evidence_for_bound_facts,
)
from verifiqa.verification.z3_runner import Z3Runner


def _ir(bindings, status="ok", constraints=None):
    return SimpleNamespace(xbrl_calculations={
        "status": status,
        "bindings": bindings,
        "constraints": constraints or [],
    })


# 01328-shaped: the LLM extracted 0, the filing (XBRL) reports 411.
_CONFLICT_SMT = """(set-logic QF_NRA)
(set-option :produce-models true)
(declare-const computed_restructuring Real)
(declare-const restructuring_line Real)
(declare-const xbrl_restructuring Real)
(assert (! (= restructuring_line 0.0) :named evidence_restructuring_line))
(assert (! (= restructuring_line xbrl_restructuring) :named xbrl_bind_restructuring_line_ctx))
(assert (! (= xbrl_restructuring 411.0) :named xbrl_instance_restructuring_line))
(assert (! (= computed_restructuring restructuring_line) :named formula_restructuring))
(assert (! (<= (- computed_restructuring 0.0) 0.5) :named claim_upper))
(assert (! (<= (- 0.0 computed_restructuring) 0.5) :named claim_lower))
(check-sat)
(get-model)"""


class GroundingTierTests(unittest.TestCase):
    def test_linkbase_grounded_when_bindings_and_constraints_present(self):
        ir = _ir(
            [{"fact_name": "restructuring_line"}],
            constraints=[{"parent_variable": "x", "children": []}],
        )
        self.assertEqual(_grounding_tier(ir), "xbrl_linkbase_grounded")

    def test_instance_grounded_when_only_bindings_present(self):
        ir = _ir([{"fact_name": "restructuring_line"}])
        self.assertEqual(_grounding_tier(ir), "xbrl_instance_grounded")

    def test_llm_only_when_no_bindings(self):
        self.assertEqual(_grounding_tier(_ir([])), "llm_only")

    def test_instance_grounded_even_when_status_is_instance_only_reason(self):
        ir = _ir([{"fact_name": "x"}], status="no_constraints_connected_to_formula_facts")
        self.assertEqual(_grounding_tier(ir), "xbrl_instance_grounded")

    def test_table_grounded_when_binding_source_is_finqa_table(self):
        ir = _ir([{"fact_name": "x", "source": "finqa_table"}])
        ir.xbrl_calculations["source"] = "finqa_table"
        self.assertEqual(_grounding_tier(ir), "finqa_table_grounded")


class StripEvidenceTests(unittest.TestCase):
    def test_strips_only_bound_fact_evidence(self):
        ir = _ir([{"fact_name": "restructuring_line"}])
        out = _strip_llm_evidence_for_bound_facts(_CONFLICT_SMT, ir)
        self.assertNotIn("evidence_restructuring_line", out)   # LLM value dropped
        self.assertIn("xbrl_instance_restructuring_line", out)  # filing value kept

    def test_unbound_fact_evidence_is_preserved(self):
        # Safety: stripping an unbound fact would leave it a free variable and let
        # the solver satisfy any claim (false verify). Unbound facts must be kept.
        ir = _ir([])  # nothing bound
        out = _strip_llm_evidence_for_bound_facts(_CONFLICT_SMT, ir)
        self.assertIn("evidence_restructuring_line", out)

    def test_table_binding_strips_llm_evidence(self):
        ir = _ir([{"fact_name": "restructuring_line", "source": "finqa_table"}])
        ir.xbrl_calculations["source"] = "finqa_table"
        out = _strip_llm_evidence_for_bound_facts(_CONFLICT_SMT, ir)
        self.assertNotIn("evidence_restructuring_line", out)
        self.assertIn("xbrl_instance_restructuring_line", out)


class ConflictRecomputeTests(unittest.TestCase):
    def test_filing_wins_claim_is_rejected_then_recomputed(self):
        ir = _ir([{"fact_name": "restructuring_line"}])
        grounded = _strip_llm_evidence_for_bound_facts(_CONFLICT_SMT, ir)

        # The LLM's claim of 0 is now checked against the filing's 411 -> UNSAT.
        self.assertEqual(Z3Runner().run(grounded).solver_status, "UNSAT")

        # Answer-repair: strip the claim and solve for the filing-grounded value.
        no_claim = Z3Runner().run(_strip_claim_assertions(grounded))
        self.assertEqual(no_claim.solver_status, "SAT")
        match = re.search(
            r"computed_restructuring(?: \(\) Real\s+|\s*=\s+)([-\d.]+)",
            no_claim.model or "",
        )
        self.assertIsNotNone(match, no_claim.model)
        self.assertEqual(float(match.group(1)), 411.0)


if __name__ == "__main__":
    unittest.main()
