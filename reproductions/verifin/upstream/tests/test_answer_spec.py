import unittest

from verifiqa.answer_spec import answer_spec_from_question, apply_answer_spec, apply_output_contract
from verifiqa.formalization.formalizer import certificate_to_claim_schema
from verifiqa.types import CertificateClaim, CertificateFact, VerificationCertificate


class AnswerSpecTests(unittest.TestCase):
    def test_ratio_question_normalizes_percent_claim_to_ratio(self):
        certificate = VerificationCertificate(
            claim=CertificateClaim(metric="roa", claimed_value=1.42, unit="percent"),
            facts=[
                CertificateFact("net_income", 1248.0, "USD millions", "Net income was 1,248", "chunk"),
                CertificateFact("average_assets", 87583.0, "USD millions", "Average assets were 87,583", "chunk"),
            ],
            formula="net_income / average_assets",
        )
        claim, schema = certificate_to_claim_schema(certificate)
        spec = answer_spec_from_question(
            "What is the FY2017 return on assets (ROA)? Round your answer to two decimal places."
        )

        normalized_certificate, normalized_claim, normalized_schema = apply_answer_spec(
            certificate, claim, schema, spec
        )

        self.assertEqual(spec.expected_unit, "ratio")
        self.assertAlmostEqual(normalized_claim.claimed_value, 0.0142)
        self.assertAlmostEqual(normalized_certificate.claim.claimed_value, 0.0142)
        self.assertEqual(normalized_schema.tolerance, 0.005)

    def test_ratio_question_strips_formula_percent_multiplier(self):
        certificate = VerificationCertificate(
            claim=CertificateClaim(metric="return_on_assets", claimed_value=-0.0142, unit="ratio"),
            facts=[
                CertificateFact("net_income_2022", -505.0, "USD millions", "Net loss was 505", "chunk"),
                CertificateFact("total_assets_2022", 38363.0, "USD millions", "Total assets were 38,363", "chunk"),
                CertificateFact("total_assets_2021", 32963.0, "USD millions", "Total assets were 32,963", "chunk"),
            ],
            formula="net_income_2022 / ((total_assets_2022 + total_assets_2021) / 2.0) * 100.0",
        )
        claim, schema = certificate_to_claim_schema(certificate)
        spec = answer_spec_from_question(
            "What is the FY2022 return on assets (ROA)? Round your answer to two decimal places."
        )

        normalized_certificate, normalized_claim, normalized_schema = apply_answer_spec(
            certificate, claim, schema, spec
        )

        expected_formula = "net_income_2022/((total_assets_2022+total_assets_2021)/2.0)"
        self.assertEqual(spec.expected_unit, "ratio")
        self.assertAlmostEqual(normalized_claim.claimed_value, -0.0142)
        self.assertEqual(normalized_certificate.formula, expected_formula)
        self.assertEqual(normalized_schema.formula, expected_formula)

    def test_percent_question_uses_percent_units_and_one_decimal_tolerance(self):
        certificate = VerificationCertificate(
            claim=CertificateClaim(metric="gross_margin", claimed_value=0.397, unit="ratio"),
            facts=[
                CertificateFact("cogs", 397.0, "USD millions", "COGS was 397", "chunk"),
                CertificateFact("revenue", 1000.0, "USD millions", "Revenue was 1,000", "chunk"),
            ],
            formula="cogs / revenue",
        )
        claim, schema = certificate_to_claim_schema(certificate)
        spec = answer_spec_from_question(
            "What is COGS margin in units of percents and round to one decimal place?"
        )

        normalized_certificate, normalized_claim, normalized_schema = apply_answer_spec(
            certificate, claim, schema, spec
        )

        self.assertEqual(spec.expected_unit, "percent")
        self.assertAlmostEqual(normalized_claim.claimed_value, 39.7)
        self.assertAlmostEqual(normalized_certificate.claim.claimed_value, 39.7)
        self.assertEqual(normalized_certificate.formula, "(cogs / revenue) * 100")
        self.assertEqual(normalized_schema.formula, "(cogs / revenue) * 100")
        self.assertEqual(normalized_schema.tolerance, 0.05)

    def test_usd_millions_amount_uses_half_unit_tolerance_by_default(self):
        spec = answer_spec_from_question("How much capex did ACME report in USD millions?")
        self.assertEqual(spec.expected_unit, "USD millions")
        self.assertEqual(spec.tolerance, 0.5)

    def test_ambiguous_margin_question_does_not_force_percent_units(self):
        spec = answer_spec_from_question("What was ExampleCo's FY2023 gross margin?")
        self.assertEqual(spec.expected_unit, "unspecified")
        self.assertEqual(spec.tolerance, 0.01)

    def test_answer_precision_sets_tolerance_when_question_has_no_rounding_rule(self):
        certificate = VerificationCertificate(
            claim=CertificateClaim(metric="quick_ratio", claimed_value=1.57, unit="ratio"),
            facts=[
                CertificateFact("current_assets", 1570.0, "USD millions", "Current assets were 1,570 million", "chunk"),
                CertificateFact("current_liabilities", 1000.0, "USD millions", "Current liabilities were 1,000 million", "chunk"),
            ],
            formula="current_assets / current_liabilities",
        )
        claim, schema = certificate_to_claim_schema(certificate)
        spec = answer_spec_from_question("What was the quick ratio?", "The quick ratio was 1.57.")

        _, _, normalized_schema = apply_answer_spec(certificate, claim, schema, spec, "The quick ratio was 1.57.")

        self.assertEqual(normalized_schema.precision_digits, 2)
        self.assertEqual(normalized_schema.tolerance_source, "answer_precision")
        # Precision was inferred from the printed answer (the question states no
        # rounding rule). The 0.1% relative floor is below the half-ULP here:
        # max(half-ULP 0.005, 0.001 * 1.57) = 0.005.
        self.assertAlmostEqual(normalized_schema.tolerance, 0.005)

    def test_output_contract_rejects_too_many_question_decimals(self):
        certificate = VerificationCertificate(
            claim=CertificateClaim(metric="return_on_assets", claimed_value=-0.0142, unit="ratio"),
            facts=[
                CertificateFact("net_income", -505.0, "USD millions", "Net loss was 505", "chunk"),
                CertificateFact("average_assets", 35663.0, "USD millions", "Average assets were 35,663", "chunk"),
            ],
            formula="net_income / average_assets",
        )
        claim, schema = certificate_to_claim_schema(certificate)
        spec = answer_spec_from_question(
            "What is the FY2022 return on assets (ROA)? Round your answer to two decimal places.",
            "The ROA is -0.0142.",
        )
        certificate, claim, schema = apply_answer_spec(certificate, claim, schema, spec, "The ROA is -0.0142.")

        _, normalized_claim, _, check = apply_output_contract(
            certificate, claim, schema, spec, "The ROA is -0.0142."
        )

        self.assertFalse(check["valid"])
        self.assertEqual(check["reason"], "answer_precision_exceeds_question:4>2")
        self.assertTrue(check["solver_enforced"])
        self.assertAlmostEqual(normalized_claim.claimed_value, -0.0142)

    def test_output_contract_uses_displayed_rounded_answer(self):
        certificate = VerificationCertificate(
            claim=CertificateClaim(metric="return_on_assets", claimed_value=-0.0142, unit="ratio"),
            facts=[
                CertificateFact("net_income", -505.0, "USD millions", "Net loss was 505", "chunk"),
                CertificateFact("average_assets", 35663.0, "USD millions", "Average assets were 35,663", "chunk"),
            ],
            formula="net_income / average_assets",
        )
        claim, schema = certificate_to_claim_schema(certificate)
        answer = "The ROA is -0.01."
        spec = answer_spec_from_question(
            "What is the FY2022 return on assets (ROA)? Round your answer to two decimal places.",
            answer,
        )
        certificate, claim, schema = apply_answer_spec(certificate, claim, schema, spec, answer)

        normalized_certificate, normalized_claim, normalized_schema, check = apply_output_contract(
            certificate, claim, schema, spec, answer
        )

        self.assertTrue(check["valid"])
        self.assertEqual(check["claim_token"], "-0.01")
        self.assertAlmostEqual(normalized_claim.claimed_value, -0.01)
        self.assertAlmostEqual(normalized_certificate.claim.claimed_value, -0.01)
        self.assertAlmostEqual(normalized_schema.tolerance, 0.005)

    def test_percent_written_ratio_answer_uses_percent_token_tolerance(self):
        # The question asks for a ratio, but the answer is written as a percent.
        # The displayed token's decimals are percent decimals, so the display
        # tolerance must be converted back into ratio space.
        certificate = VerificationCertificate(
            claim=CertificateClaim(metric="return_on_assets", claimed_value=-0.0142, unit="ratio"),
            facts=[
                CertificateFact("net_income", -505.0, "USD millions", "Net loss was 505", "chunk"),
                CertificateFact("average_assets", 35663.0, "USD millions", "Average assets were 35,663", "chunk"),
            ],
            formula="net_income / average_assets",
        )
        claim, schema = certificate_to_claim_schema(certificate)
        answer = "The ROA is -1.42 percent."
        spec = answer_spec_from_question(
            "What is the FY2022 return on assets (ROA)? Round your answer to two decimal places.",
            answer,
        )
        certificate, claim, schema = apply_answer_spec(certificate, claim, schema, spec, answer)

        _, normalized_claim, normalized_schema, check = apply_output_contract(certificate, claim, schema, spec, answer)

        self.assertTrue(check["valid"])
        self.assertAlmostEqual(normalized_claim.claimed_value, -0.0142)
        self.assertAlmostEqual(check["tolerance"], 0.00005)
        self.assertAlmostEqual(normalized_schema.tolerance, 0.00005)
        self.assertIn("percent_token_to_ratio", check["tolerance_source"])

    def test_percent_written_ratio_answer_does_not_get_full_ratio_tolerance(self):
        certificate = VerificationCertificate(
            claim=CertificateClaim(metric="return_on_assets", claimed_value=-0.0147, unit="ratio"),
            facts=[
                CertificateFact("net_income", -546.0, "USD millions", "Net loss was 546", "chunk"),
                CertificateFact("average_assets", 35663.0, "USD millions", "Average assets were 35,663", "chunk"),
            ],
            formula="net_income / average_assets",
        )
        claim, schema = certificate_to_claim_schema(certificate)
        answer = "-1.47% (FY2022 net income of -$505 million / average total assets of $35,663 million)"
        spec = answer_spec_from_question(
            "What is the FY2022 return on assets (ROA)? Round your answer to two decimal places.",
            answer,
        )
        certificate, claim, schema = apply_answer_spec(certificate, claim, schema, spec, answer)

        _, _, normalized_schema, check = apply_output_contract(certificate, claim, schema, spec, answer)

        self.assertTrue(check["valid"])
        self.assertAlmostEqual(normalized_schema.tolerance, 0.00005)
        # The XBRL-grounded value for the same denominator is about -0.01531,
        # which should not be accepted as the displayed -1.47% claim.
        self.assertGreater(abs((-546.0 / 35663.0) - check["normalized_claimed_value"]), check["tolerance"])

    def test_output_contract_accepts_relational_answer_via_components(self):
        # A derived "change" claim presented through its components: the answer
        # states 24.6% and 21.6% but not the -3.0 pp difference.
        certificate = VerificationCertificate(
            claim=CertificateClaim(
                metric="effective_tax_rate_change", claimed_value=-3.0, unit="percentage points"
            ),
            facts=[
                CertificateFact("effective_tax_rate_2022", 21.6, "percent", "21.6%", "chunk"),
                CertificateFact("effective_tax_rate_2021", 24.6, "percent", "24.6%", "chunk"),
            ],
            formula="effective_tax_rate_2022 - effective_tax_rate_2021",
        )
        claim, schema = certificate_to_claim_schema(certificate)
        answer = "The effective tax rate dropped from 24.6% in FY 2021 to 21.6% in FY 2022."
        spec = answer_spec_from_question(
            "How has the effective tax rate changed from FY2021 to FY2022?", answer
        )
        certificate, claim, schema = apply_answer_spec(certificate, claim, schema, spec, answer)

        _, _, _, check = apply_output_contract(certificate, claim, schema, spec, answer)

        self.assertTrue(check["valid"])
        self.assertEqual(check["reason"], "answer_states_claim_components")
        self.assertFalse(check["solver_enforced"])

    def test_output_contract_rejects_wrong_components(self):
        certificate = VerificationCertificate(
            claim=CertificateClaim(
                metric="effective_tax_rate_change", claimed_value=-3.0, unit="percentage points"
            ),
            facts=[
                CertificateFact("effective_tax_rate_2022", 21.6, "percent", "21.6%", "chunk"),
                CertificateFact("effective_tax_rate_2021", 24.6, "percent", "24.6%", "chunk"),
            ],
            formula="effective_tax_rate_2022 - effective_tax_rate_2021",
        )
        claim, schema = certificate_to_claim_schema(certificate)
        answer = "The effective tax rate was around 30% and 10%."
        spec = answer_spec_from_question(
            "How has the effective tax rate changed from FY2021 to FY2022?", answer
        )
        certificate, claim, schema = apply_answer_spec(certificate, claim, schema, spec, answer)

        _, _, _, check = apply_output_contract(certificate, claim, schema, spec, answer)

        self.assertFalse(check["valid"])
        self.assertEqual(check["reason"], "claimed_value_not_in_answer")

    def test_cagr_formula_is_canonicalized_to_percent_function(self):
        certificate = VerificationCertificate(
            claim=CertificateClaim(metric="revenue_cagr", claimed_value=0.4, unit="percent"),
            facts=[
                CertificateFact("revenue_2022", 65984.0, "USD millions", "Revenue was 65,984", "chunk"),
                CertificateFact("revenue_2020", 65398.0, "USD millions", "Revenue was 65,398", "chunk"),
            ],
            formula="(revenue_2022 / revenue_2020) ^ (1 / 2) - 1",
        )
        claim, schema = certificate_to_claim_schema(certificate)
        spec = answer_spec_from_question(
            "What is the 2 year revenue CAGR in units of percents and round to one decimal place?"
        )

        normalized_certificate, _, normalized_schema = apply_answer_spec(certificate, claim, schema, spec)

        self.assertEqual(normalized_certificate.formula, "cagr_percent(revenue_2022, revenue_2020, 2)")
        self.assertEqual(normalized_schema.formula, "cagr_percent(revenue_2022, revenue_2020, 2)")
        self.assertEqual(normalized_schema.tolerance, 0.05)


if __name__ == "__main__":
    unittest.main()
