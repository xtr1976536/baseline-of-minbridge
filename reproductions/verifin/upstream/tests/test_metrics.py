import unittest

from verifiqa.eval.metrics import numeric_answer_accuracy, summarize_results
from verifiqa.types import RavResult


class MetricsTests(unittest.TestCase):
    def test_numeric_accuracy_ignores_trailing_fiscal_years(self):
        self.assertTrue(numeric_answer_accuracy(
            "The verified effective tax rate change is -3%. Calculation: 21.6 - 24.6 = -3.0.",
            "The effective tax rate dropped from 24.6% in FY 2021 to 21.6% in FY 2022.",
        ))

    def test_numeric_accuracy_understands_money_scale_words(self):
        self.assertTrue(numeric_answer_accuracy("20000 USD millions", "$20 billion"))
        self.assertTrue(numeric_answer_accuracy("400 USD millions", "$400,000,000 increase"))
        self.assertTrue(numeric_answer_accuracy("8400 USD millions", "$8,400,000,000"))

    def test_numeric_accuracy_understands_compact_money_suffixes(self):
        self.assertTrue(numeric_answer_accuracy(
            "2,018 million dollars",
            "AMCOR's Adj. EBITDA was $2,018mn in FY 2023",
        ))
        self.assertTrue(numeric_answer_accuracy("2018 USD millions", "$2.018bn"))
        self.assertTrue(numeric_answer_accuracy("500 USD millions", "$500mm"))

    def test_refusal_text_is_not_a_numeric_answer(self):
        self.assertFalse(numeric_answer_accuracy(
            "The claimed value was not verified: Z3 found a counterexample outside tolerance.",
            "The effective tax rate changed from 24.6% to 21.6%.",
        ))

    def test_embedded_digits_are_not_numbers(self):
        self.assertFalse(numeric_answer_accuracy("Z3", "3"))
        self.assertFalse(numeric_answer_accuracy("FY2022", "2022"))

    def test_verification_precision_uses_verified_denominator(self):
        results = [
            RavResult(
                financebench_id="ok",
                question="q",
                answer="1.00",
                gold_answer="1.00",
                final_status="VERIFIED",
                first_pass_solver_status="UNSAT",
                verified=True,
            ),
            RavResult(
                financebench_id="false_positive",
                question="q",
                answer="2.00",
                gold_answer="3.00",
                final_status="VERIFIED",
                first_pass_solver_status="UNSAT",
                verified=True,
            ),
            RavResult(
                financebench_id="abstain",
                question="q",
                answer="abstain",
                gold_answer="4.00",
                final_status="ABSTAIN",
                first_pass_solver_status="SAT",
                abstained=True,
            ),
        ]
        summary = summarize_results(results)
        self.assertEqual(summary["verified_coverage"], 2 / 3)
        self.assertEqual(summary["verification_precision"], 0.5)
        self.assertEqual(summary["false_positive_rate"], 0.5)
        self.assertNotIn("verified_accuracy", summary)


if __name__ == "__main__":
    unittest.main()
