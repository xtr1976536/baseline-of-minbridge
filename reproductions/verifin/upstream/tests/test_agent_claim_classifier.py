import unittest

from verifiqa.agent.claim_classifier import (
    classify,
    decompose_question_consensus,
    decompose_question,
    parse_claimed_answer,
)
from verifiqa.agent.types import ClaimSpec, RoleSpec
from verifiqa.formulas.evaluator import evaluate_formula


class NoLlm:
    def chat(self, *args, **kwargs):
        raise AssertionError("LLM should not be called for known decomposition cases")


class StaticLlm:
    def __init__(self, response: str):
        self.response = response

    def chat(self, *args, **kwargs):
        return self.response


class RecordingLlm(StaticLlm):
    def __init__(self, response: str):
        super().__init__(response)
        self.calls = []
        self.messages = None

    def chat(self, messages, *args, **kwargs):
        self.calls.append((kwargs.get("stage"), messages))
        self.messages = messages
        return self.response


class SequentialLlm:
    def __init__(self, responses: list[str]):
        self.responses = list(responses)
        self.calls = []

    def chat(self, messages, *args, **kwargs):
        self.calls.append((kwargs.get("stage"), kwargs.get("temperature"), messages))
        return self.responses.pop(0)


class AgentClaimClassifierTests(unittest.TestCase):
    def test_gross_margin_decline_uses_prior_minus_current(self):
        spec = classify(
            "what was the gross margin decline in fiscal 2004 from 2003?",
            NoLlm(),
        )

        self.assertEqual(
            spec.formula,
            "gross_margin_percentage_2003 - gross_margin_percentage_2004",
        )
        self.assertEqual(
            [role.name for role in spec.roles],
            ["gross_margin_percentage_2003", "gross_margin_percentage_2004"],
        )
        self.assertAlmostEqual(
            evaluate_formula(
                spec.formula,
                {
                    "gross_margin_percentage_2003": 27.5,
                    "gross_margin_percentage_2004": 27.3,
                },
            ),
            0.2,
        )

    def test_loan_receivable_net_of_allowance_extracts_allowance_roles(self):
        spec = classify(
            "in 2010 what was the percentage change of the carrying amount of "
            "loan receivable net of the allowance",
            NoLlm(),
        )

        self.assertEqual(
            spec.formula,
            "((loan_receivable_end - allowance_end) - "
            "(loan_receivable_start - allowance_start)) / "
            "(loan_receivable_start - allowance_start) * 100",
        )
        self.assertEqual(
            [role.name for role in spec.roles],
            [
                "loan_receivable_start",
                "allowance_start",
                "loan_receivable_end",
                "allowance_end",
            ],
        )
        self.assertAlmostEqual(
            evaluate_formula(
                spec.formula,
                {
                    "loan_receivable_start": 920.0,
                    "allowance_start": 95.0,
                    "loan_receivable_end": 469.0,
                    "allowance_end": 77.0,
                },
            ),
            -52.4848484848,
        )

    def test_no_formula_falls_back_to_known_direct_lookup_policy(self):
        spec = classify(
            "What is FY2015 total current liabilities?",
            StaticLlm(
                '{"verifiable": "false", "claimed_value": 2213556, '
                '"claimed_unit": "USD thousands", "metric": "unknown", '
                '"formula": "", "roles": [], "claim_unit": "other", '
                '"formula_source": "no_formula"}'
            ),
            answer="$2,213,556",
        )

        self.assertEqual(spec.formula_source, "direct_lookup")
        self.assertEqual(spec.metric, "total_current_liabilities")
        self.assertEqual(spec.formula, "current_liabilities")
        self.assertEqual(spec.claimed_value, 2213556.0)
        self.assertEqual([role.name for role in spec.roles], ["current_liabilities"])
        self.assertEqual(spec.roles[0].period, "2015")
        self.assertIn("total current liabilities", spec.roles[0].aliases)

    def test_no_formula_falls_back_to_unknown_direct_lookup_identity(self):
        spec = classify(
            "What is the amount of customer refund liability in FY2022?",
            StaticLlm(
                '{"verifiable": "true", "claimed_value": 123, '
                '"claimed_unit": "USD millions", "metric": "unknown", '
                '"formula": "", "roles": [], "claim_unit": "other", '
                '"formula_source": "no_formula"}'
            ),
            answer="$123 million",
        )

        self.assertEqual(spec.formula_source, "direct_lookup")
        self.assertEqual(spec.metric, "customer_refund_liability")
        self.assertEqual(spec.formula, "customer_refund_liability")
        self.assertEqual([role.name for role in spec.roles], ["customer_refund_liability"])
        self.assertIn("customer refund liability", spec.roles[0].aliases)

    def test_direct_lookup_ignores_explanatory_clause(self):
        spec = classify(
            "What is the amount of gain accruing to JnJ as a result of the "
            "separation of its Consumer Health business segment?",
            StaticLlm(
                '{"verifiable": "false", "claimed_value": 20, '
                '"claimed_unit": "USD billions", "metric": "unknown", '
                '"formula": "", "roles": [], "claim_unit": "other", '
                '"formula_source": "no_formula"}'
            ),
            answer="approximately $20 billion",
        )

        self.assertEqual(spec.formula_source, "direct_lookup")
        self.assertEqual(spec.formula, "gain_accruing_jnj")
        self.assertEqual([role.name for role in spec.roles], ["gain_accruing_jnj"])

    def test_no_formula_does_not_direct_lookup_ratio_question(self):
        spec = classify(
            "What is the FY2015 operating cash flow ratio? Operating cash flow ratio "
            "is defined as cash from operations / total current liabilities.",
            StaticLlm(
                '{"verifiable": "false", "claimed_value": 0.66, '
                '"claimed_unit": "ratio", "metric": "unknown", '
                '"formula": "", "roles": [], "claim_unit": "ratio", '
                '"formula_source": "no_formula"}'
            ),
            answer="0.66",
        )

        self.assertEqual(spec.formula_source, "no_formula")
        self.assertEqual(spec.formula, "")
        self.assertEqual(spec.roles, [])

    def test_classifier_prompt_includes_evidence_text(self):
        llm = RecordingLlm(
            '{"verifiable": "true", "metric": "custom_metric", '
            '"formula": "reported_amount", '
            '"roles": [{"name": "reported_amount", "aliases": ["reported amount"], "period": "2022"}], '
            '"claim_unit": "USD millions", "formula_source": "document_derived"}'
        )

        decompose_question(
            "What is the reported amount?",
            llm,
            evidence_text="SENTINEL EVIDENCE ROW reported amount 10",
        )

        self.assertIsNotNone(llm.messages)
        self.assertIn("Evidence:\nSENTINEL EVIDENCE ROW", llm.messages[0].content)
        self.assertNotIn("Answer:", llm.messages[0].content)

    def test_parse_claimed_answer_extracts_final_value_only(self):
        llm = RecordingLlm('{"claimed_value": 0.2, "claimed_unit": "percent"}')
        claim_spec = ClaimSpec(
            metric="gross_margin_percentage_decline",
            formula="gross_margin_percentage_2003 - gross_margin_percentage_2004",
            roles=[
                RoleSpec("gross_margin_percentage_2003", ["gross margin percentage"], "2003"),
                RoleSpec("gross_margin_percentage_2004", ["gross margin percentage"], "2004"),
            ],
            claim_unit="percent",
            tolerance=0.01,
            formula_source="generic_operation",
        )

        claimed = parse_claimed_answer(
            "what was the gross margin decline in fiscal 2004 from 2003?",
            "Gross margin increased from $1,708M in 2003 to $2,259M in 2004, "
            "from 27.5% to 27.3%, a decline of 0.2 percentage points.",
            claim_spec,
            llm,
        )

        self.assertEqual(claimed.value, 0.2)
        self.assertEqual(claimed.unit, "percent")
        self.assertEqual(llm.calls[0][0], "claim_value_parse")

    def test_ambiguous_decline_does_not_become_absolute_formula(self):
        llm = RecordingLlm(
            '{"verifiable": "true", "metric": "period_change", '
            '"formula": "lease_2007 - lease_2008", '
            '"roles": ['
            '{"name": "lease_2007", "aliases": ["operating leases"], "period": "2007"}, '
            '{"name": "lease_2008", "aliases": ["operating leases"], "period": "2008"}], '
            '"claim_unit": "other", "formula_source": "generic_operation"}'
        )

        spec = decompose_question(
            "what is the decline from current future minimum lease payments and "
            "the following years expected obligation?\\n",
            llm,
            evidence_text="2007 | 1703\n2008 | 1371",
        )

        self.assertEqual(spec.operation, "ambiguous_operation")
        self.assertEqual(spec.formula_source, "no_formula")
        self.assertEqual(spec.formula, "")

    def test_claimspec_consensus_accepts_semantically_equivalent_formulas(self):
        responses = [
            '{"verifiable": "true", "metric": "asset_turnover", '
            '"formula": "revenue / assets", '
            '"roles": ['
            '{"name": "revenue", "aliases": ["revenue"], "period": "2022"}, '
            '{"name": "assets", "aliases": ["assets"], "period": "2022"}], '
            '"claim_unit": "ratio", "formula_source": "document_derived"}',
            '{"verifiable": "true", "metric": "asset_turnover", '
            '"formula": "(revenue) / (assets)", '
            '"roles": ['
            '{"name": "revenue", "aliases": ["revenue"], "period": "2022"}, '
            '{"name": "assets", "aliases": ["assets"], "period": "2022"}], '
            '"claim_unit": "ratio", "formula_source": "document_derived"}',
            '{"verifiable": "true", "metric": "asset_turnover", '
            '"formula": "revenue * (1 / assets)", '
            '"roles": ['
            '{"name": "revenue", "aliases": ["revenue"], "period": "2022"}, '
            '{"name": "assets", "aliases": ["assets"], "period": "2022"}], '
            '"claim_unit": "ratio", "formula_source": "document_derived"}',
        ]

        spec, diagnostics, failure = decompose_question_consensus(
            "What is the asset turnover ratio?",
            SequentialLlm(responses),
            evidence_text="revenue 10\nassets 5",
        )

        self.assertEqual(failure, "")
        self.assertIsNotNone(spec)
        self.assertTrue(diagnostics["claimspec_consensus"]["agreed"])
        self.assertEqual(len(diagnostics["claimspec_consensus"]["runs"]), 3)

    def test_claimspec_consensus_rejects_opposite_sign_formula(self):
        responses = [
            '{"verifiable": "true", "metric": "revenue_change", '
            '"formula": "revenue_2022 - revenue_2021", '
            '"roles": ['
            '{"name": "revenue_2021", "aliases": ["revenue"], "period": "2021"}, '
            '{"name": "revenue_2022", "aliases": ["revenue"], "period": "2022"}], '
            '"claim_unit": "USD millions", "formula_source": "generic_operation"}',
            '{"verifiable": "true", "metric": "revenue_change", '
            '"formula": "revenue_2021 - revenue_2022", '
            '"roles": ['
            '{"name": "revenue_2021", "aliases": ["revenue"], "period": "2021"}, '
            '{"name": "revenue_2022", "aliases": ["revenue"], "period": "2022"}], '
            '"claim_unit": "USD millions", "formula_source": "generic_operation"}',
            '{"verifiable": "true", "metric": "revenue_change", '
            '"formula": "revenue_2022 - revenue_2021", '
            '"roles": ['
            '{"name": "revenue_2021", "aliases": ["revenue"], "period": "2021"}, '
            '{"name": "revenue_2022", "aliases": ["revenue"], "period": "2022"}], '
            '"claim_unit": "USD millions", "formula_source": "generic_operation"}',
        ]

        _spec, diagnostics, failure = decompose_question_consensus(
            "In USD millions, what was the change in revenue from 2021 to 2022?",
            SequentialLlm(responses),
            evidence_text="revenue 2021 10\nrevenue 2022 8",
        )

        self.assertEqual(failure, "claimspec_consensus_failed")
        self.assertFalse(diagnostics["claimspec_consensus"]["agreed"])
        self.assertEqual(
            diagnostics["claimspec_consensus"]["failure_reason"],
            "formula_mismatch",
        )

if __name__ == "__main__":
    unittest.main()
