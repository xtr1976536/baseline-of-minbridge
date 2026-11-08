import unittest

from verifiqa.formulas.evaluator import (
    evaluate_formula,
    formula_assertion_smt,
    formula_domain_constraints_smt,
    formula_variables,
    normalize_formula,
    result_is_money,
)


class ResultIsMoneyTests(unittest.TestCase):
    def test_money_dimensions(self):
        money = {"net_income", "avg_assets", "revenue", "op_income", "proceeds", "a", "b"}
        # money pass-through and money +/- money stay money
        self.assertTrue(result_is_money("proceeds", money))
        self.assertTrue(result_is_money("a + b", money))
        self.assertTrue(result_is_money("a - b", money))
        self.assertTrue(result_is_money("proceeds * 2", money))
        # money / money cancels to a ratio; *100 makes percent — not money
        self.assertFalse(result_is_money("net_income / avg_assets", money))
        self.assertFalse(result_is_money("op_income / revenue * 100", money))
        # non-money variable -> unknown, not money
        self.assertFalse(result_is_money("shares", money))


class FormulaEvaluatorTests(unittest.TestCase):
    def test_cagr_notation_normalizes_to_percent_function(self):
        formula = "(revenue_2022 / revenue_2020) ^ (1 / 2) - 1"

        normalized = normalize_formula(formula, "percent")

        self.assertEqual(normalized, "cagr_percent(revenue_2022, revenue_2020, 2)")
        self.assertEqual(formula_variables(normalized), {"revenue_2022", "revenue_2020"})
        self.assertAlmostEqual(
            evaluate_formula(normalized, {"revenue_2022": 65984.0, "revenue_2020": 65398.0}),
            0.4470267688544194,
        )

    def test_cagr_smt_uses_algebraic_constraint_and_domain(self):
        formula = "cagr_percent(revenue_2022, revenue_2020, 2)"

        self.assertEqual(
            formula_assertion_smt("computed_revenue_cagr", formula, "percent"),
            "(= (* revenue_2020 (+ 1 (/ computed_revenue_cagr 100)) (+ 1 (/ computed_revenue_cagr 100))) revenue_2022)",
        )
        self.assertEqual(
            formula_domain_constraints_smt("computed_revenue_cagr", formula, "percent"),
            ["(> computed_revenue_cagr -100)"],
        )

    def test_coverage_ratio_floors_non_positive_numerator(self):
        formula = "coverage_ratio(adjusted_ebit, interest_expense)"

        self.assertEqual(
            formula_variables(formula),
            {"adjusted_ebit", "interest_expense"},
        )
        self.assertAlmostEqual(
            evaluate_formula(formula, {"adjusted_ebit": -10.0, "interest_expense": 5.0}),
            0.0,
        )
        self.assertEqual(
            formula_assertion_smt("computed_interest_coverage_ratio", formula, "ratio"),
            "(and (=> (<= adjusted_ebit 0) (= computed_interest_coverage_ratio 0)) "
            "(=> (> adjusted_ebit 0) (= computed_interest_coverage_ratio (/ adjusted_ebit interest_expense))))",
        )
        self.assertEqual(
            formula_domain_constraints_smt("computed_interest_coverage_ratio", formula, "ratio"),
            ["(or (> interest_expense 0) (< interest_expense 0))"],
        )


if __name__ == "__main__":
    unittest.main()
