import unittest

from verifiqa.formalization.formalizer import (
    FormalizationError,
    Formalizer,
    certificate_from_json,
    certificate_from_text,
    certificate_to_claim_schema,
)
from verifiqa.types import EvidenceChunk


class SequencedLlm:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def chat(self, messages, temperature=0.0, stage="unknown", max_tokens=None, output_config=None):
        self.calls.append((stage, messages))
        if not self.responses:
            raise AssertionError("unexpected_llm_call")
        return self.responses.pop(0)


class FormalizerTests(unittest.TestCase):
    def test_parses_verification_certificate(self):
        certificate = certificate_from_text(
            """
            {
              "verifiable": true,
              "claim": {
                "metric": "quick_ratio",
                "claimed_value": 1.5718,
                "unit": "ratio",
                "period": "FY2022",
                "reported_value": 1.57
              },
              "facts": [
                {
                  "name": "cash",
                  "value": "4,835",
                  "unit": "USD millions",
                  "source_quote": "Cash and cash equivalents were $4,835 million",
                  "chunk_id": "chunk_12",
                  "period": "FY2022"
                },
                {
                  "name": "short_term_investments",
                  "value": 1020,
                  "unit": "USD millions",
                  "source_quote": "Short-term investments were $1,020 million",
                  "chunk_id": "chunk_12",
                  "period": "FY2022"
                },
                {
                  "name": "receivables",
                  "value": 4126,
                  "unit": "USD millions",
                  "source_quote": "Accounts receivable were $4,126 million",
                  "chunk_id": "chunk_12",
                  "period": "FY2022"
                },
                {
                  "name": "current_liabilities",
                  "value": 6350,
                  "unit": "USD millions",
                  "source_quote": "Total current liabilities were $6,350 million",
                  "chunk_id": "chunk_12",
                  "period": "FY2022"
                }
              ],
              "formula": "(cash + short_term_investments + receivables) / current_liabilities",
              "calculation": "(4835 + 1020 + 4126) / 6350",
              "tolerance": 0.001
            }
            """
        )
        claim, schema = certificate_to_claim_schema(certificate)
        self.assertEqual(claim.metric, "quick_ratio")
        self.assertEqual(claim.variables["cash"], 4835.0)
        self.assertIn("computed_quick_ratio", schema.allowed_variables)

    def test_normalizes_metric_name_that_starts_with_number(self):
        certificate = certificate_from_json(
            {
                "verifiable": True,
                "claim": {
                    "metric": "3_year_average_net_profit_margin",
                    "claimed_value": 2.8,
                    "unit": "percent",
                },
                "facts": [
                    {
                        "name": "net_income",
                        "value": 1228,
                        "unit": "USD millions",
                        "source_quote": "Net earnings were $1,228 million",
                        "chunk_id": "chunk_1",
                    },
                    {
                        "name": "revenue",
                        "value": 39403,
                        "unit": "USD millions",
                        "source_quote": "Revenue was $39,403 million",
                        "chunk_id": "chunk_1",
                    },
                ],
                "formula": "net_income / revenue * 100",
                "calculation": "1228 / 39403 * 100",
                "tolerance": 0.05,
            }
        )
        claim, schema = certificate_to_claim_schema(certificate)
        self.assertEqual(claim.metric, "three_year_average_net_profit_margin")
        self.assertIn("computed_three_year_average_net_profit_margin", schema.allowed_variables)

    def test_parses_raw_newline_inside_json_string(self):
        certificate = certificate_from_text(
            """
            {
              "verifiable": true,
              "claim": {"metric": "current_liabilities", "claimed_value": 2213.556, "unit": "USD millions"},
              "facts": [
                {
                  "name": "total_current_liabilities",
                  "value": 2213.556,
                  "unit": "USD millions",
                  "source_quote": "Total current liabilities
2,213,556",
                  "chunk_id": "chunk_1"
                }
              ],
              "formula": "total_current_liabilities",
              "calculation": "2213.556",
              "tolerance": 0.001
            }
            """
        )

        self.assertEqual(certificate.facts[0].source_quote, "Total current liabilities\n2,213,556")

    def test_rejects_formula_variable_without_fact(self):
        with self.assertRaisesRegex(FormalizationError, "formula_variable_missing_fact"):
            certificate_from_json(
                {
                    "verifiable": True,
                    "claim": {"metric": "roa", "claimed_value": 0.1, "unit": "ratio"},
                    "facts": [
                        {
                            "name": "net_income",
                            "value": 10,
                            "unit": "USD millions",
                            "source_quote": "Net income was $10 million",
                            "chunk_id": "chunk_1",
                        }
                    ],
                    "formula": "net_income / average_assets",
                }
            )

    def test_prunes_unused_facts_from_certificate(self):
        certificate = certificate_from_json(
            {
                "verifiable": True,
                "claim": {
                    "metric": "net_property_plant_equipment",
                    "claimed_value": 8.738,
                    "unit": "USD billions",
                },
                "facts": [
                    {
                        "name": "property_plant_equipment_gross",
                        "value": 24873,
                        "unit": "USD millions",
                        "source_quote": "Property, plant and equipment 24,873",
                        "chunk_id": "chunk_1",
                    },
                    {
                        "name": "accumulated_depreciation",
                        "value": 16135,
                        "unit": "USD millions",
                        "source_quote": "Less: Accumulated depreciation (16,135)",
                        "chunk_id": "chunk_1",
                    },
                    {
                        "name": "net_ppe",
                        "value": 8738,
                        "unit": "USD millions",
                        "source_quote": "Property, plant and equipment net 8,738",
                        "chunk_id": "chunk_1",
                    },
                ],
                "formula": "net_ppe / 1000",
                "calculation": "8738 / 1000 = 8.738",
                "tolerance": 0.01,
            }
        )

        self.assertEqual([fact.name for fact in certificate.facts], ["net_ppe"])

    def test_rejects_unverifiable_model(self):
        with self.assertRaisesRegex(FormalizationError, "not_verifiable"):
            certificate_from_json({"verifiable": False, "reason": "missing facts"})

    def test_formalizer_retries_unverifiable_response_before_abstaining(self):
        llm = SequencedLlm([
            '{"verifiable": false, "reason": "missing facts"}',
            """
            {
              "verifiable": true,
              "claim": {"metric": "revenue", "claimed_value": 12, "unit": "USD millions"},
              "facts": [
                {
                  "name": "revenue",
                  "value": 12,
                  "unit": "USD millions",
                  "source_quote": "Revenue was $12 million",
                  "chunk_id": "chunk_1"
                }
              ],
              "formula": "revenue",
              "calculation": "12",
              "tolerance": 0.01
            }
            """,
        ])

        certificate = Formalizer(llm).formalize(
            "What was revenue?",
            [EvidenceChunk("chunk_1", "doc", 1, "Revenue was $12 million")],
            "Revenue was 12.",
        )

        self.assertEqual(certificate.claim.metric, "revenue")
        self.assertEqual([stage for stage, _ in llm.calls], ["formalization", "formalization_no_abstain_retry"])

    def test_formalizer_prompt_includes_registry_guidance_for_interest_coverage(self):
        llm = SequencedLlm([
            """
            {
              "verifiable": true,
              "claim": {"metric": "interest_coverage_ratio", "claimed_value": 2.42, "unit": "ratio"},
              "facts": [
                {"name": "adjusted_ebitdar", "value": 3497.254, "unit": "USD millions", "source_quote": "Adjusted EBITDAR 3,497,254", "chunk_id": "chunk_1", "row_label": "Adjusted EBITDAR"},
                {"name": "depreciation_and_amortization", "value": 3482.05, "unit": "USD millions", "source_quote": "Depreciation and amortization 3,482,050", "chunk_id": "chunk_1", "row_label": "Depreciation and amortization"},
                {"name": "lease_rent_expense", "value": 1950.566, "unit": "USD millions", "source_quote": "Triple-net operating lease and ground lease rent expense 1,950,566", "chunk_id": "chunk_1", "row_label": "Triple-net operating lease and ground lease rent expense"},
                {"name": "interest_expense", "value": 594.954, "unit": "USD millions", "source_quote": "Interest expense, net of amounts capitalized 594,954", "chunk_id": "chunk_1", "row_label": "Interest expense, net of amounts capitalized"}
              ],
              "formula": "coverage_ratio(adjusted_ebitdar - depreciation_and_amortization - lease_rent_expense, interest_expense)",
              "calculation": "coverage_ratio(3497.254 - 3482.05 - 1950.566, 594.954)",
              "tolerance": 0.005
            }
            """,
        ])

        Formalizer(llm).formalize(
            "What was MGM's interest coverage ratio using FY2022 Adjusted EBIT as the numerator and annual Interest Expense as the denominator?",
            [EvidenceChunk("chunk_1", "doc", 13, "Adjusted EBITDAR 3,497,254 Interest expense, net of amounts capitalized 594,954")],
            "The verified interest coverage ratio is 2.42.",
        )

        prompt = llm.calls[0][1][0].content
        self.assertIn("financebench_interest_coverage_ratio", prompt)
        self.assertIn("coverage_ratio(adjusted_ebitdar - depreciation_and_amortization - lease_rent_expense, interest_expense)", prompt)
        self.assertIn("Never bind Operating income/loss to adjusted_ebit", prompt)
        self.assertIn("claim.metric must be copied exactly", prompt)
        self.assertIn("copy the formula field exactly", prompt)


if __name__ == "__main__":
    unittest.main()
