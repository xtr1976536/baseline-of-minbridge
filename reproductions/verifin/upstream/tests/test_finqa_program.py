"""FinQA program-authority fixes.

Cells holding the same value are not ambiguous (pick one). Genuine FinQA program
grounding failures are solver-enforced proof failures, while missing FinanceBench
registry policies still block strong verification without force-violating.
"""
import unittest
from collections import Counter, defaultdict

from verifiqa.pipeline import _authority_failure_forces_violation
from verifiqa.verification.finqa_program import (
    FinqaProgramError,
    _FinqaProgramResolver,
    _Operand,
    _SourceCandidate,
    _candidates_share_value,
    _literal_key,
)


class DoubleFormatNegativeTests(unittest.TestCase):
    def test_row_cells_take_one_value_per_cell(self):
        # FinQA writes negatives as "-13 ( 13 )"; parsing yields -13 and +13. A row cell
        # is a single value, so the row expansion must emit one (signed) value per cell,
        # else table_average/table_sum cancels the magnitude to ~0.
        r = object.__new__(_FinqaProgramResolver)
        r.table = [
            ["december 31,", "2016", "2015", "2014"],
            ["settlements", "-13 ( 13 )", "-19 ( 19 )", "-2 ( 2 )"],
        ]
        cells = r._table_row_numeric_cells("settlements")
        values = [c.canonical_value for c in cells]
        self.assertEqual(values, [-13.0, -19.0, -2.0])
        self.assertAlmostEqual(sum(values) / len(values), -11.33333, places=4)


def _cand(context_id, canonical, raw=None):
    return _SourceCandidate(
        source="table", source_label="table_1", context_id=context_id,
        row_idx=1, col_idx=1, row_label="r", column="c", quote="",
        raw_token=str(raw if raw is not None else canonical),
        raw_value=raw if raw is not None else canonical,
        canonical_value=canonical, has_percent=False, fallback=False,
    )


def _resolver(candidates, literal_text):
    r = object.__new__(_FinqaProgramResolver)
    r.candidates = candidates
    r.used_candidates = set()
    r.literal_counts = Counter({_literal_key(literal_text): 1})
    r.literal_seen = defaultdict(int)
    return r


class ShareValueTests(unittest.TestCase):
    def test_same_value(self):
        self.assertTrue(_candidates_share_value([_cand("a", 51.2), _cand("b", 51.2)]))

    def test_different_value(self):
        self.assertFalse(_candidates_share_value([_cand("a", 51.2), _cand("b", 0.512)]))

    def test_empty(self):
        self.assertFalse(_candidates_share_value([]))


class SelectCandidateTests(unittest.TestCase):
    def test_same_value_candidates_pick_one_no_raise(self):
        # 51.2 appears in two cells with the same value -> the bound value is identical,
        # so pick one instead of raising ambiguous_program_operand.
        cands = [_cand("a", 51.2), _cand("b", 51.2)]
        r = _resolver(cands, "51.2")
        op = _Operand(raw_text="51.2", raw_value=51.2, value=51.2, has_percent=False)
        selected = r._select_candidate(op)
        self.assertEqual(selected.canonical_value, 51.2)
        self.assertIn(selected.context_id, {"a", "b"})
        self.assertIn(selected.context_id, r.used_candidates)

    def test_genuinely_different_values_still_raise(self):
        # Same raw token (both match the operand) but different canonical values (e.g. a
        # percent-scaled cell) -> truly ambiguous -> raise.
        cands = [_cand("a", 51.2, raw=51.2), _cand("b", 0.512, raw=51.2)]
        r = _resolver(cands, "51.2")
        op = _Operand(raw_text="51.2", raw_value=51.2, value=51.2, has_percent=False)
        with self.assertRaises(FinqaProgramError) as ctx:
            r._select_candidate(op)
        self.assertIn("ambiguous_program_operand", str(ctx.exception))


class AuthorityFailureFallbackTests(unittest.TestCase):
    def test_missing_financebench_policy_does_not_force_violation(self):
        for reason in (
            "no_policy_for_metric",
            "policy_templates_unresolved",
            "policy_role_ambiguous:assets",
            # Ambiguous program operand is a soft failure: the program (oracle)
            # couldn't be grounded unambiguously, so abstain rather than force a
            # (possibly false) violation.
            "ambiguous_program_operand:51.2:2",
            "",
        ):
            self.assertFalse(_authority_failure_forces_violation(reason), reason)

    def test_finqa_program_grounding_failures_are_solver_enforced(self):
        for reason in (
            "program_operand_reuse_exhausted:23",
            "program_operand_not_grounded:377.0",
            "unsupported_program_operation:foo",
        ):
            self.assertTrue(_authority_failure_forces_violation(reason), reason)

    def test_hard_proof_failures_are_solver_enforced(self):
        for reason in (
            "absence_fact_not_grounded:source_quote",
            "monetary_claim_unit_is_ratio",
            "policy_role_constraints_failed:adjusted_ebit",
        ):
            self.assertTrue(_authority_failure_forces_violation(reason), reason)


if __name__ == "__main__":
    unittest.main()
