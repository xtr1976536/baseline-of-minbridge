import unittest

from verifiqa.formalization.formalizer import Formalizer
from verifiqa.generation.answer_generator import AnswerGenerator
from verifiqa.types import EvidenceChunk, RetrievalFact, RetrievalPlan


class RecordingLlm:
    def __init__(self, response):
        self.response = response
        self.messages = []

    def chat(self, messages, temperature=0.0, stage="unknown", max_tokens=None, output_config=None):
        self.messages.append((stage, messages))
        return self.response


class GenerationPromptTests(unittest.TestCase):
    def test_answer_prompt_includes_retrieval_plan_aliases(self):
        llm = RecordingLlm('{"answer": "Fixed asset turnover is 24.26."}')
        plan = RetrievalPlan(
            metric="fixed_asset_turnover_ratio",
            facts=[
                RetrievalFact(
                    name="ppe_2019",
                    aliases=["Property and equipment, net", "PP&E"],
                    period="2019",
                    statement="balance sheet",
                )
            ],
        )

        answer = AnswerGenerator(llm).generate(
            "What is fixed asset turnover?",
            [EvidenceChunk("chunk", "doc", 1, "Property and equipment, net 253")],
            retrieval_plan=plan,
        )

        prompt = llm.messages[0][1][0].content
        self.assertEqual(answer, "Fixed asset turnover is 24.26.")
        self.assertIn("ppe_2019", prompt)
        self.assertIn("Property and equipment, net", prompt)
        self.assertIn("matches an alias", prompt)

    def test_formalizer_prompt_includes_retrieval_plan_aliases(self):
        llm = RecordingLlm(
            """{
              "verifiable": true,
              "claim": {
                "metric": "fixed_asset_turnover_ratio",
                "claimed_value": 24.26,
                "unit": "ratio",
                "period": "FY2019",
                "reported_value": 24.26
              },
              "facts": [
                {
                  "name": "revenue_2019",
                  "raw_value": 6489,
                  "raw_unit": "USD",
                  "source_scale": "millions",
                  "source_scale_quote": "Amounts in millions",
                  "value": 6489,
                  "unit": "USD millions",
                  "source_quote": "Total net revenues 6,489",
                  "chunk_id": "chunk",
                  "period": "2019",
                  "row_label": "Total net revenues",
                  "column": "2019"
                }
              ],
              "formula": "revenue_2019",
              "calculation": "6489",
              "tolerance": 0.005
            }"""
        )
        plan = RetrievalPlan(
            metric="fixed_asset_turnover_ratio",
            facts=[
                RetrievalFact(
                    name="revenue_2019",
                    aliases=["Total net revenues"],
                    period="2019",
                    statement="income statement",
                )
            ],
        )

        Formalizer(llm).formalize(
            "What is fixed asset turnover?",
            [EvidenceChunk("chunk", "doc", 1, "Total net revenues 6,489")],
            "Fixed asset turnover is 24.26.",
            retrieval_plan=plan,
        )

        prompt = llm.messages[0][1][0].content
        self.assertIn("revenue_2019", prompt)
        self.assertIn("Total net revenues", prompt)
        self.assertIn("acceptable aliases", prompt)


if __name__ == "__main__":
    unittest.main()
