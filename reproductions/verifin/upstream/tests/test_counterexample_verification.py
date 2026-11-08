import unittest

from verifiqa.formalization.formalizer import certificate_to_claim_schema
from verifiqa.types import CertificateClaim, CertificateFact, Claim, VerificationCertificate
from verifiqa.verification.smt_sanitizer import SmtSanitizer
from verifiqa.verification.z3_runner import Z3Runner

from smt_helpers import render_counterexample_smt


class CounterexampleVerificationTests(unittest.TestCase):
    def setUp(self):
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
        self.claim, self.schema = certificate_to_claim_schema(certificate)

    def _make_claim(self, claimed_value: float) -> Claim:
        return Claim(
            metric=self.schema.metric,
            claimed_value=claimed_value,
            variables=self.claim.variables,
        )

    def test_sat_means_verified_for_claim_query(self):
        claim = self._make_claim(1.5718)
        smtlib = render_counterexample_smt(claim, self.schema)
        validation = SmtSanitizer().validate(smtlib, claim, self.schema)
        self.assertEqual(validation.smt_status, "valid", validation.reason)
        result = Z3Runner().run(smtlib)
        self.assertEqual(result.solver_status, "SAT", result.raw_output)
        self.assertIn("computed_quick_ratio", result.model)

    def test_unsat_means_claim_is_inconsistent(self):
        claim = self._make_claim(1.95)
        smtlib = render_counterexample_smt(claim, self.schema)
        validation = SmtSanitizer().validate(smtlib, claim, self.schema)
        self.assertEqual(validation.smt_status, "valid", validation.reason)
        result = Z3Runner().run(smtlib, debug_unsat_core=True)
        self.assertEqual(result.solver_status, "UNSAT", result.raw_output)
        self.assertTrue(result.unsat_core)

    def test_missing_evidence_does_not_default_to_zero(self):
        claim = Claim(
            metric=self.schema.metric,
            claimed_value=1.0,
            variables={"cash": 1.0},
        )
        with self.assertRaisesRegex(ValueError, "missing_evidence_variable"):
            render_counterexample_smt(claim, self.schema)

    def test_cagr_percent_counterexample_query_verifies_rounded_answer(self):
        certificate = VerificationCertificate(
            claim=CertificateClaim(
                metric="revenue_cagr_2020_2022",
                claimed_value=0.4,
                unit="percent",
            ),
            facts=[
                CertificateFact(
                    "revenue_2022",
                    65984.0,
                    "USD millions",
                    "Net sales Total net sales $ 65,984",
                    "chunk_1",
                ),
                CertificateFact(
                    "revenue_2020",
                    65398.0,
                    "USD millions",
                    "Net sales Total net sales $ 65,398",
                    "chunk_1",
                ),
            ],
            formula="cagr_percent(revenue_2022, revenue_2020, 2)",
            tolerance=0.05,
        )
        claim, schema = certificate_to_claim_schema(certificate)
        smtlib = render_counterexample_smt(claim, schema)

        validation = SmtSanitizer().validate(smtlib, claim, schema)
        self.assertEqual(validation.smt_status, "valid", validation.reason)
        result = Z3Runner().run(smtlib)
        self.assertEqual(result.solver_status, "SAT", result.raw_output)


if __name__ == "__main__":
    unittest.main()
