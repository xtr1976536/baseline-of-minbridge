import unittest

from verifiqa.types import VerificationFact, VerificationIR
from verifiqa.verification.generic_ops import (
    classify_operation,
    resolve_generic_operation,
)


def _ir(facts: dict[str, float], metric="metric", formula="", claimed=0.0, unit="USD millions"):
    return VerificationIR(
        metric=metric,
        formula=formula,
        facts={k: VerificationFact(k, v, unit) for k, v in facts.items()},
        claimed_value=claimed,
        claim_unit=unit,
        tolerance=0.5,
    )


def _ir_labeled(facts: dict[str, tuple[float, str]], metric="metric"):
    """facts: name -> (value, row_label)."""
    return VerificationIR(
        metric=metric,
        formula="",
        facts={k: VerificationFact(k, v, "", row_label=lbl) for k, (v, lbl) in facts.items()},
        claimed_value=0.0,
        claim_unit="",
        tolerance=0.5,
    )


class ClassifyTests(unittest.TestCase):
    def test_percent_change_wins_over_change(self):
        self.assertEqual(
            classify_operation("What was the percentage change in revenue from 2018 to 2019?"),
            "percent_change",
        )
        self.assertEqual(classify_operation("what was the percent change in net sales?"), "percent_change")
        self.assertEqual(classify_operation("growth rate of revenue?"), "percent_change")

    def test_absolute_change(self):
        self.assertEqual(classify_operation("What was the change in revenue from 2018 to 2019?"), "period_change")
        self.assertEqual(classify_operation("How much did revenue increase?"), "period_change")
        self.assertEqual(classify_operation("the difference in operating income"), "period_change")

    def test_proportion(self):
        self.assertEqual(
            classify_operation("what percentage of the total oil and gas mmboe comes from canada?"),
            "proportion",
        )
        self.assertEqual(classify_operation("what portion of total debt is due after 2014?"), "proportion")
        self.assertEqual(classify_operation("canada as a percentage of total mmboe?"), "proportion")

    def test_percent_change_beats_proportion(self):
        # has 'percent' but is a change question -> percent_change, not proportion.
        self.assertEqual(
            classify_operation("what was the percentage change in revenue from 2018 to 2019?"),
            "percent_change",
        )

    def test_non_operation_is_none(self):
        self.assertIsNone(classify_operation("What was revenue in 2019?"))
        self.assertEqual(classify_operation("what was the ratio of debt to equity?"), "generic_ratio")


class ProportionTests(unittest.TestCase):
    def test_dvn_percent_of_total_binds_base_by_total_label(self):
        # Real DVN/2007 case: canada=60, total=243 -> 60/243*100 = 24.69.
        ir = _ir_labeled({
            "finqa_operand_0": (60.0, "canada"),
            "finqa_operand_1": (243.0, "total"),
        })
        res = resolve_generic_operation(
            ir, "what percentage of the total oil and gas mmboe comes from canada?"
        )
        self.assertIsNotNone(res)
        self.assertEqual(res["operation"], "proportion")
        self.assertEqual(res["base"], "finqa_operand_1")
        self.assertEqual(res["part"], "finqa_operand_0")
        self.assertAlmostEqual(res["computed_value"], 60.0 / 243.0 * 100.0)
        self.assertTrue(res["source_refs"])  # cited

    def test_base_by_grammar_when_no_total_label(self):
        # No "total" label; the base is the noun after "of" (net sales).
        ir = _ir_labeled({
            "rd_expense": (100.0, "research and development"),
            "net_sales": (1000.0, "net sales"),
        })
        res = resolve_generic_operation(
            ir, "what percent of net sales was research and development?"
        )
        self.assertIsNotNone(res)
        self.assertEqual(res["base"], "net_sales")
        self.assertAlmostEqual(res["computed_value"], 10.0)

    def test_abstains_when_base_ambiguous(self):
        # Neither fact labeled total, grammar can't disambiguate -> abstain.
        ir = _ir_labeled({"a": (60.0, "alpha"), "b": (243.0, "beta")})
        self.assertIsNone(resolve_generic_operation(ir, "what percentage is one of the other?"))

    def test_abstains_when_two_totals(self):
        ir = _ir_labeled({"a": (60.0, "total segment"), "b": (243.0, "total company")})
        self.assertIsNone(
            resolve_generic_operation(ir, "what percentage of the total is the segment?")
        )

    def test_abstains_without_exactly_two_facts(self):
        ir = _ir_labeled({"a": (1.0, "total")})
        self.assertIsNone(resolve_generic_operation(ir, "what percent of total is a?"))

    def test_abstains_on_zero_base(self):
        ir = _ir_labeled({"part": (5.0, "segment"), "base": (0.0, "total")})
        self.assertIsNone(resolve_generic_operation(ir, "what percent of total is the segment?"))

    def test_label_and_grammar_disagreement_abstains(self):
        # "total" label points to b, but grammar ("of segment_a") points to a -> abstain.
        ir = _ir_labeled({"segment_a": (60.0, "segment a"), "b": (243.0, "total")})
        self.assertIsNone(
            resolve_generic_operation(ir, "what percentage of segment a is b?")
        )


class ResolveTests(unittest.TestCase):
    def test_percent_change_resolves_period_ordered(self):
        res = resolve_generic_operation(
            _ir({"revenue_2018": 100.0, "revenue_2019": 120.0}),
            "What was the percentage change in revenue from 2018 to 2019?",
        )
        self.assertIsNotNone(res)
        self.assertEqual(res["operation"], "percent_change")
        self.assertEqual(res["start"], "revenue_2018")
        self.assertEqual(res["end"], "revenue_2019")
        self.assertAlmostEqual(res["computed_value"], 20.0)
        self.assertIn("revenue_2019", res["formula"])

    def test_absolute_change_resolves(self):
        res = resolve_generic_operation(
            _ir({"opinc_2020": 50.0, "opinc_2021": 65.0}),
            "What was the change in operating income from 2020 to 2021?",
        )
        self.assertEqual(res["operation"], "period_change")
        self.assertAlmostEqual(res["computed_value"], 15.0)

    def test_decline_resolves_as_prior_minus_current(self):
        res = resolve_generic_operation(
            _ir({"gross_margin_2003": 27.5, "gross_margin_2004": 27.3}),
            "what was the gross margin decline in fiscal 2004 from 2003?",
        )

        self.assertIsNotNone(res)
        self.assertEqual(res["operation"], "period_change")
        self.assertEqual(res["formula"], "gross_margin_2003 - gross_margin_2004")
        self.assertAlmostEqual(res["computed_value"], 0.2)

    def test_order_independent_of_dict_order(self):
        # later year listed first must still bind start=earlier.
        res = resolve_generic_operation(
            _ir({"revenue_2021": 120.0, "revenue_2019": 100.0}),
            "percentage change in revenue?",
        )
        self.assertEqual(res["start"], "revenue_2019")
        self.assertEqual(res["end"], "revenue_2021")
        self.assertAlmostEqual(res["computed_value"], 20.0)

    def test_abstains_without_two_dated_facts(self):
        # only one fact -> abstain
        self.assertIsNone(
            resolve_generic_operation(_ir({"revenue_2019": 100.0}), "percent change in revenue?")
        )
        # three facts -> ambiguous -> abstain
        self.assertIsNone(
            resolve_generic_operation(
                _ir({"r_2018": 1.0, "r_2019": 2.0, "r_2020": 3.0}),
                "percent change in revenue?",
            )
        )

    def test_abstains_when_facts_lack_period(self):
        self.assertIsNone(
            resolve_generic_operation(
                _ir({"revenue_current": 120.0, "revenue_prior": 100.0}),
                "percent change in revenue?",
            )
        )

    def test_abstains_on_same_year(self):
        self.assertIsNone(
            resolve_generic_operation(
                _ir({"revenue_2019_a": 120.0, "revenue_2019_b": 100.0}),
                "percent change in revenue?",
            )
        )

    def test_abstains_on_non_operation_question(self):
        self.assertIsNone(
            resolve_generic_operation(
                _ir({"revenue_2018": 100.0, "revenue_2019": 120.0}),
                "What was revenue in 2019?",
            )
        )

    def test_percent_change_zero_base_abstains(self):
        self.assertIsNone(
            resolve_generic_operation(
                _ir({"revenue_2018": 0.0, "revenue_2019": 120.0}),
                "percent change in revenue?",
            )
        )

    def test_average_resolves_year_span(self):
        res = resolve_generic_operation(
            _ir({
                "backlog_2013": 21400.0,
                "backlog_2014": 20300.0,
                "backlog_2015": 17400.0,
            }),
            "what was the average backlog at year-end from 2013 to 2015?",
        )

        self.assertIsNotNone(res)
        self.assertEqual(res["operation"], "average")
        self.assertEqual(
            res["formula"],
            "(backlog_2013 + backlog_2014 + backlog_2015) / 3",
        )
        self.assertAlmostEqual(res["computed_value"], 19700.0)

    def test_average_abstains_when_year_span_missing_fact(self):
        self.assertIsNone(
            resolve_generic_operation(
                _ir({"backlog_2013": 21400.0, "backlog_2015": 17400.0}),
                "what was the average backlog at year-end from 2013 to 2015?",
            )
        )

    def test_generic_ratio_binds_direction_from_question_grammar(self):
        ir = _ir_labeled({
            "accrued_interest": (1.2, "accrued interest"),
            "recognized_interest_liability": (17.0, "recognized interest liability"),
        })

        res = resolve_generic_operation(
            ir,
            "what was the ratio of accrued interest to recognized interest liability?",
        )

        self.assertIsNotNone(res)
        self.assertEqual(res["operation"], "generic_ratio")
        self.assertEqual(res["numerator"], "accrued_interest")
        self.assertEqual(res["denominator"], "recognized_interest_liability")
        self.assertEqual(res["formula"], "accrued_interest / recognized_interest_liability")
        self.assertAlmostEqual(res["computed_value"], 1.2 / 17.0)


if __name__ == "__main__":
    unittest.main()
