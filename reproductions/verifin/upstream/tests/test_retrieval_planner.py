import unittest

from verifiqa.generation.llm_client import LlmError
from verifiqa.retrieval.planner import (
    RetrievalPlanner,
    fallback_retrieval_plan,
    retrieval_plan_from_json,
)


class FakePlannerLlm:
    def chat(self, messages, temperature=0.0, stage="unknown"):
        return """{
          "metric": "liquidation_value_per_share",
          "facts": [
            {"name": "total_assets", "aliases": ["Total assets"], "period": "2021 Q1", "statement": "balance sheet"},
            {"name": "shares_outstanding", "aliases": ["Shares outstanding"], "period": "2021 Q1", "statement": "balance sheet"}
          ],
          "reason": "bad decomposition"
        }"""


class FailingPlannerLlm:
    def chat(self, messages, temperature=0.0, stage="unknown"):
        raise LlmError("vLLM request failed: connection refused")


class RetrievalPlannerTests(unittest.TestCase):
    def test_parses_and_deduplicates_llm_plan(self):
        plan = retrieval_plan_from_json({
            "metric": "Fixed Asset Turnover",
            "facts": [
                {
                    "name": "Revenue 2018",
                    "aliases": ["Total revenues", "Total revenues"],
                    "period": "2018",
                    "statement": "income statement",
                },
                {
                    "name": "Revenue 2018",
                    "aliases": ["Net sales"],
                    "period": "2018",
                    "statement": "income statement",
                },
            ],
        })

        self.assertEqual(plan.metric, "fixed_asset_turnover")
        self.assertEqual(len(plan.facts), 1)
        self.assertEqual(plan.facts[0].name, "revenue_2018")
        self.assertEqual(plan.facts[0].aliases, ["Total revenues"])

    def test_fallback_decomposes_formula_question(self):
        plan = fallback_retrieval_plan(
            "What is FY2018 fixed asset turnover, defined as FY2018 revenue / "
            "(average PP&E between FY2017 and FY2018)?"
        )
        names = {fact.name for fact in plan.facts}

        self.assertIn("revenue", names)
        self.assertIn("ppe", names)
        self.assertTrue(any("2018" in fact.period for fact in plan.facts))
        self.assertTrue(any("2017" in fact.period for fact in plan.facts))

    def test_fallback_recognizes_net_ppne_lookup(self):
        plan = fallback_retrieval_plan(
            "What is the year end FY2018 net PPNE for 3M? Answer in USD billions."
        )

        self.assertEqual([fact.name for fact in plan.facts], ["ppe"])
        self.assertEqual(plan.facts[0].statement, "balance sheet")
        self.assertIn("PPNE", plan.facts[0].aliases)
        self.assertIn("property, plant and equipment, net", plan.facts[0].aliases)

    def test_cash_flow_statement_does_not_trigger_cash_balance_fact(self):
        plan = fallback_retrieval_plan(
            "What is the FY2018 capital expenditure amount for 3M? "
            "Rely on the details shown in the cash flow statement."
        )

        self.assertEqual([fact.name for fact in plan.facts], ["capital_expenditure"])
        self.assertEqual(plan.metric, "capital_expenditure")

    def test_fallback_prefers_reported_per_share_equity_for_shareholder_recovery(self):
        plan = fallback_retrieval_plan(
            "If JPM went bankrupted by the end by 2021 Q1 and liquidated all of "
            "its assets to pay its shareholders, how much could each shareholder get?"
        )

        self.assertIn("tangible_book_value_per_share", {fact.name for fact in plan.facts})
        self.assertNotIn("total_assets", {fact.name for fact in plan.facts})
        aliases = {
            alias.lower()
            for fact in plan.facts
            if fact.name == "tangible_book_value_per_share"
            for alias in fact.aliases
        }
        self.assertIn("tangible book value per share", aliases)
        self.assertIn("tbvps", aliases)

    def test_llm_plan_is_normalized_for_shareholder_recovery_questions(self):
        plan = RetrievalPlanner(FakePlannerLlm()).plan(
            "If JPM went bankrupted by the end by 2021 Q1 and liquidated all of "
            "its assets to pay its shareholders, how much could each shareholder get?"
        )

        self.assertEqual(plan.metric, "tangible_book_value_per_share")
        self.assertEqual([fact.name for fact in plan.facts], ["tangible_book_value_per_share"])
        self.assertIn("normalized_shareholder_recovery", plan.reason)

    def test_llm_failure_falls_back_to_deterministic_plan(self):
        plan = RetrievalPlanner(FailingPlannerLlm()).plan(
            "What is FY2020 EBITDA margin using operating income plus depreciation and amortization?"
        )

        names = {fact.name for fact in plan.facts}
        self.assertIn("operating_income", names)
        self.assertIn("depreciation_amortization", names)
        self.assertIn("llm_planning_failed:LlmError", plan.reason)


if __name__ == "__main__":
    unittest.main()
