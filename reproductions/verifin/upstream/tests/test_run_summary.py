import unittest

from verifiqa.eval.run_summary import (
    _clean_gold_number,
    _gold_targets,
    _question_decimals,
    _verdict_vs_gold,
)


class CleanGoldNumberTests(unittest.TestCase):
    def test_parses_clean_numeric_golds(self):
        self.assertEqual(_clean_gold_number("$1,577.00"), 1577.0)
        self.assertEqual(_clean_gold_number("30.8%"), 30.8)
        self.assertEqual(_clean_gold_number("-0.02"), -0.02)
        self.assertEqual(_clean_gold_number("0"), 0.0)
        self.assertEqual(_clean_gold_number("(505)"), -505.0)

    def test_scientific_notation_gold(self):
        # gold "1e-05" (per-share price) must parse as 0.00001, not split into 1 and 05.
        self.assertAlmostEqual(_clean_gold_number("1e-05"), 1e-5)
        self.assertAlmostEqual(_clean_gold_number("9.7e-6"), 9.7e-6)

    def test_money_value_that_looks_like_a_year_is_kept(self):
        # Regression: "$2,018mn" must not be dropped as a calendar year.
        self.assertEqual(_clean_gold_number("$2,018mn"), 2018.0)

    def test_prose_gold_is_ungradeable(self):
        self.assertIsNone(
            _clean_gold_number("AMCOR's Adj. EBITDA was $2,018mn in FY 2023")
        )
        self.assertIsNone(
            _clean_gold_number(
                "The effective tax rate changed from 24.6% in FY2021 to 21.6% in FY2022."
            )
        )

    def test_multiple_distinct_numbers_are_ungradeable(self):
        self.assertIsNone(_clean_gold_number("24.6% to 21.6%"))


class QuestionDecimalsTests(unittest.TestCase):
    def test_extracts_mandated_precision(self):
        self.assertEqual(_question_decimals("... round to one decimal place?"), 1)
        self.assertEqual(_question_decimals("Round your answer to 2 decimal places."), 2)
        self.assertIsNone(_question_decimals("What is the FY2018 capex in USD millions?"))


class GoldTargetsTests(unittest.TestCase):
    def test_clean_number(self):
        self.assertEqual(_gold_targets("30.8%"), {30.8})

    def test_single_unit_tagged_value_in_prose(self):
        # "$2,018mn" is the answer; "FY 2023" is a year (no value marker) -> ignored.
        self.assertEqual(
            _gold_targets("AMCOR's Adj. EBITDA was $2,018mn in FY 2023", "what was adj ebitda?"),
            {2018.0},
        )

    def test_from_x_to_y_change(self):
        targets = _gold_targets(
            "the effective tax rate changed from 24.6% in FY2021 to 21.6% in FY2022",
            "How much has the effective tax rate changed?",
        )
        self.assertIn(-3.0, targets)  # 21.6 - 24.6, sign-agnostic

    def test_from_to_only_fires_on_change_questions(self):
        # Same prose but a non-change question must NOT compute a delta.
        targets = _gold_targets(
            "revenue grew from 100 to 120 over the period",
            "what was revenue?",  # no change hint
        )
        self.assertNotIn(20.0, targets)

    def test_genuinely_ambiguous_prose_stays_empty(self):
        self.assertEqual(_gold_targets("see the discussion in the MD&A section", "what?"), set())

    def test_total_question_sums_two_component_gold(self):
        gold = ("The estimated pension benefits were $1097 million, and the estimated "
                "health care and life insurance benefits were $862 million.")
        targets = _gold_targets(gold, "how much did Verizon expect to pay for its retirees in 2024?")
        self.assertIn(1959.0, targets)  # 1097 + 862
        self.assertIn(1097.0, targets)

    def test_two_component_gold_not_summed_without_total_hint(self):
        gold = "Pension was $1097 million; healthcare was $862 million."
        # No total/combined/how-much hint -> stays ambiguous (not summed).
        self.assertNotIn(1959.0, _gold_targets(gold, "what was the pension benefit?"))

    def test_textual_zero(self):
        self.assertEqual(_gold_targets("The Real Growth was flat in FY 2023", "growth?"), {0.0})
        self.assertEqual(_gold_targets("As adjusted EBIT is negative, coverage ratio is zero", "?"), {0.0})


class VerdictTests(unittest.TestCase):
    def test_precision_aware_reject_is_correct(self):
        # Reject grades the claim. Question mandates 1 decimal: 31.0 != 30.8.
        verdict = _verdict_vs_gold(
            "VIOLATED", accepted=False, accept_values=[], reject_value=31.0,
            gold_targets={30.8}, decimals=1,
        )
        self.assertEqual(verdict, "true_reject")

    def test_accept_grades_final_answer(self):
        verdict = _verdict_vs_gold(
            "VERIFIED", accepted=True, accept_values=[1577.0], reject_value=None,
            gold_targets={1577.0}, decimals=None,
        )
        self.assertEqual(verdict, "true_accept")

    def test_percent_ratio_equivalence(self):
        # Answer 93.5 (percent) vs gold 0.935 (ratio) -> same value, accepted.
        verdict = _verdict_vs_gold(
            "VERIFIED", accepted=True, accept_values=[93.5], reject_value=None,
            gold_targets={0.935}, decimals=None,
        )
        self.assertEqual(verdict, "true_accept")

    def test_precise_value_matches_coarse_gold_rounding(self):
        verdict = _verdict_vs_gold(
            "VERIFIED", accepted=True, accept_values=[0.389], reject_value=None,
            gold_targets={0.40}, decimals=None,
        )
        self.assertEqual(verdict, "true_accept")

    def test_materially_wrong_accept_is_false_accept(self):
        verdict = _verdict_vs_gold(
            "VERIFIED", accepted=True, accept_values=[0.36], reject_value=None,
            gold_targets={0.40}, decimals=None,
        )
        self.assertEqual(verdict, "false_accept")

    def test_empty_targets_is_ungradeable(self):
        verdict = _verdict_vs_gold(
            "VERIFIED", accepted=True, accept_values=[2018.0], reject_value=None,
            gold_targets=set(), decimals=None,
        )
        self.assertEqual(verdict, "ungradeable")

    def test_reject_anchored_on_computed_value(self):
        # ebitda: claim 16.8, computed 16.52, gold 16.5% (1 decimal). The model's
        # 16.8 is genuinely wrong, so VIOLATED is a true_reject — even though 16.8
        # is within 5% of gold. Anchoring on the computed value at gold's precision
        # gets this right.
        verdict = _verdict_vs_gold(
            "VIOLATED", accepted=False, accept_values=[], reject_value=16.8,
            gold_targets={16.5}, decimals=None, computed_value=16.52, gold_decimals=1,
        )
        self.assertEqual(verdict, "true_reject")

    def test_reject_of_claim_matching_computed_is_false_reject(self):
        # If the rejected claim actually equals the grounded computed value at the
        # mandated precision, the rejection was wrong.
        verdict = _verdict_vs_gold(
            "VIOLATED", accepted=False, accept_values=[], reject_value=0.0143,
            gold_targets={0.01}, decimals=2, computed_value=0.014249, gold_decimals=2,
        )
        self.assertEqual(verdict, "false_reject")

    def test_non_decision_is_abstain(self):
        verdict = _verdict_vs_gold(
            "UNVERIFIED_FORMULA", accepted=False, accept_values=[], reject_value=3.1,
            gold_targets={2.8}, decimals=None,
        )
        self.assertEqual(verdict, "abstain")


if __name__ == "__main__":
    unittest.main()
