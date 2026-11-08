import unittest

from verifiqa.formalization.formalizer import certificate_to_claim_schema
from verifiqa.types import CertificateClaim, CertificateFact, VerificationCertificate
from verifiqa.verification.ir import ir_from_claim_schema
from verifiqa.verification.smt_generator import SmtGenerator

from smt_helpers import render_counterexample_smt


class FakeLlm:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def chat(self, messages, temperature=0.0, stage="unknown", max_tokens=None):
        self.calls.append(
            {
                "messages": messages,
                "temperature": temperature,
                "stage": stage,
                "max_tokens": max_tokens,
            }
        )
        return self.response


class SmtGeneratorTests(unittest.TestCase):
    def test_smt_is_generated_by_llm_call(self):
        certificate = VerificationCertificate(
            claim=CertificateClaim(metric="quick_ratio", claimed_value=1.5718, unit="ratio"),
            facts=[
                CertificateFact("cash", 4835.0, "USD millions", "Cash was $4,835 million", "chunk_1"),
                CertificateFact("short_term_investments", 1020.0, "USD millions", "Investments were $1,020 million", "chunk_1"),
                CertificateFact("receivables", 4126.0, "USD millions", "Receivables were $4,126 million", "chunk_1"),
                CertificateFact("current_liabilities", 6350.0, "USD millions", "Liabilities were $6,350 million", "chunk_1"),
            ],
            formula="(cash + short_term_investments + receivables) / current_liabilities",
            tolerance=0.001,
        )
        claim, schema = certificate_to_claim_schema(certificate)
        expected = render_counterexample_smt(claim, schema)
        llm = FakeLlm(f"```smt2\n{expected}\n```")

        smtlib = SmtGenerator(llm).generate(claim, schema)

        self.assertEqual(smtlib, expected)
        self.assertEqual(llm.calls[0]["stage"], "smt_generation")
        self.assertEqual(llm.calls[0]["max_tokens"], 1024)
        self.assertIn('"value": 1.5718', llm.calls[0]["messages"][0].content)
        self.assertIn('"computed_variable": "computed_quick_ratio"', llm.calls[0]["messages"][0].content)

    def test_repair_strips_prose_around_raw_smt(self):
        certificate = VerificationCertificate(
            claim=CertificateClaim(metric="capital_expenditure", claimed_value=1577.0, unit="USD millions"),
            facts=[
                CertificateFact("capex_fy2018", -1577.0, "USD millions", "Capex was (1,577)", "chunk_1"),
            ],
            formula="capex_fy2018",
            tolerance=0.5,
        )
        claim, schema = certificate_to_claim_schema(certificate)
        repaired = render_counterexample_smt(claim, schema).replace(
            "(= computed_capital_expenditure capex_fy2018)",
            "(= computed_capital_expenditure (- capex_fy2018))",
        )
        llm = FakeLlm(
            "The issue is clear: here is the fix.\n\n"
            + repaired
            + "\n\nThis should satisfy Z3."
        )

        smtlib = SmtGenerator(llm).repair(ir_from_claim_schema(claim, schema), "bad smt", ["claim_lower"])

        self.assertEqual(smtlib, repaired)
        self.assertTrue(smtlib.startswith("(set-logic QF_NRA)"))
        self.assertNotIn("The issue is clear", smtlib)

    def test_missing_llm_client_is_error(self):
        certificate = VerificationCertificate(
            claim=CertificateClaim(metric="roa", claimed_value=0.1, unit="ratio"),
            facts=[
                CertificateFact("net_income", 10.0, "USD millions", "Net income was $10 million", "chunk_1"),
                CertificateFact("average_assets", 100.0, "USD millions", "Average assets were $100 million", "chunk_1"),
            ],
            formula="net_income / average_assets",
        )
        claim, schema = certificate_to_claim_schema(certificate)
        with self.assertRaisesRegex(ValueError, "missing_llm_client"):
            SmtGenerator(None).generate(claim, schema)

    def test_llm_prompt_supports_cagr_percent(self):
        certificate = VerificationCertificate(
            claim=CertificateClaim(metric="revenue_cagr", claimed_value=0.4, unit="percent"),
            facts=[
                CertificateFact("revenue_2022", 65984.0, "USD millions", "Revenue was 65,984", "chunk"),
                CertificateFact("revenue_2020", 65398.0, "USD millions", "Revenue was 65,398", "chunk"),
            ],
            formula="cagr_percent(revenue_2022, revenue_2020, 2)",
            tolerance=0.05,
        )
        claim, schema = certificate_to_claim_schema(certificate)
        expected = render_counterexample_smt(claim, schema)
        llm = FakeLlm(expected)

        smtlib = SmtGenerator(llm).generate(claim, schema)

        self.assertEqual(smtlib, expected)
        prompt = llm.calls[0]["messages"][0].content
        self.assertIn("cagr_percent(end, start, years)", prompt)
        self.assertIn('"formula": "cagr_percent(revenue_2022, revenue_2020, 2)"', prompt)

    def test_scientific_notation_literals_are_normalized(self):
        certificate = VerificationCertificate(
            claim=CertificateClaim(metric="return_on_assets", claimed_value=-0.0147, unit="ratio"),
            facts=[
                CertificateFact("net_income", -505.0, "USD millions", "Net loss was 505", "chunk"),
                CertificateFact("average_assets", 35663.0, "USD millions", "Average assets were 35,663", "chunk"),
            ],
            formula="net_income / average_assets",
            tolerance=0.00005,
        )
        claim, schema = certificate_to_claim_schema(certificate)
        smt = render_counterexample_smt(claim, schema).replace("0.00005", "5e-05")
        llm = FakeLlm(smt)

        smtlib = SmtGenerator(llm).generate(claim, schema)

        prompt = llm.calls[0]["messages"][0].content
        payload = prompt.rsplit("\nInput:\n", 1)[1]
        self.assertIn("0.00005", payload)
        self.assertNotIn("5e-05", payload)
        self.assertIn("0.00005", smtlib)
        self.assertNotIn("5e-05", smtlib)
        self.assertIn("never scientific notation", prompt)


if __name__ == "__main__":
    unittest.main()
