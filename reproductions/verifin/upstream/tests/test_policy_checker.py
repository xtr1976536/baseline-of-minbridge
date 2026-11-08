import unittest

from verifiqa.formalization.formalizer import certificate_to_claim_schema
from verifiqa.policy import DEFAULT_POLICY_REGISTRY, PolicySemanticChecker
from verifiqa.types import CertificateClaim, CertificateFact, VerificationCertificate
from verifiqa.verification.ir import ir_from_certificate


def _ir(certificate):
    claim, schema = certificate_to_claim_schema(certificate)
    return ir_from_certificate(certificate, claim, schema)


class MetricNameResolutionTests(unittest.TestCase):
    """Naming variations must resolve to the same policy so a misspelled/abbreviated
    metric name never causes a spurious UNVERIFIED_FORMULA when a policy exists."""

    def test_abbreviation_and_word_order_resolve(self):
        registry = DEFAULT_POLICY_REGISTRY
        target = registry.find_policy("net_profit_margin_3_year_average")
        self.assertIsNotNone(target)
        for variant in (
            "net_profit_margin_3yr_avg",      # avg -> average
            "net_profit_margin_3yr_average",  # 3yr -> 3 year
            "3 year average net profit margin",  # reordered
            "FY2015-FY2017 net profit margin 3yr avg",  # period decoration + abbrev
        ):
            self.assertEqual(
                registry.find_policy(variant).metric if registry.find_policy(variant) else None,
                target.metric,
                f"{variant!r} did not resolve to {target.metric!r}",
            )

    def test_strict_superset_is_not_conflated(self):
        # A plain metric must NOT match a more-specific multi-year-average policy.
        registry = DEFAULT_POLICY_REGISTRY
        avg_policy = registry.find_policy("net_profit_margin_3_year_average")
        plain = registry.find_policy("net profit margin")
        self.assertTrue(plain is None or plain.metric != avg_policy.metric)


class PolicySemanticCheckerTests(unittest.TestCase):
    def test_default_registry_is_source_backed(self):
        net_income = DEFAULT_POLICY_REGISTRY.concepts["NetIncomeLike"]
        roa = DEFAULT_POLICY_REGISTRY.find_policy("roa")

        self.assertIn("us-gaap:NetIncomeLoss", net_income.xbrl_concepts)
        self.assertEqual(net_income.source_type, "xbrl_taxonomy_mapping")
        self.assertIsNotNone(roa)
        self.assertEqual(roa.source_type, "metric_convention_with_taxonomy_semantics")
        self.assertTrue(roa.source_refs)
        self.assertIn("formula_source_note", roa.metadata)

    def test_roa_policy_accepts_net_income_over_assets(self):
        certificate = VerificationCertificate(
            claim=CertificateClaim(metric="roa", claimed_value=0.12, unit="ratio"),
            facts=[
                CertificateFact("net_income", 12.0, "USD millions", "Net income was $12 million", "chunk_1"),
                CertificateFact("average_assets", 100.0, "USD millions", "Average total assets were $100 million", "chunk_1"),
            ],
            formula="net_income / average_assets",
        )

        result = PolicySemanticChecker().validate_ir(_ir(certificate))

        self.assertTrue(result.valid, result.reason)
        self.assertEqual(result.policy_id, "standard_roa_assets")
        self.assertEqual(result.role_bindings["net_income"], "net_income")
        self.assertEqual(result.role_bindings["assets"], "average_assets")

    def test_roa_policy_rejects_revenue_as_numerator(self):
        certificate = VerificationCertificate(
            claim=CertificateClaim(metric="roa", claimed_value=0.5, unit="ratio"),
            facts=[
                CertificateFact("revenue", 50.0, "USD millions", "Revenue was $50 million", "chunk_1"),
                CertificateFact("average_assets", 100.0, "USD millions", "Average total assets were $100 million", "chunk_1"),
            ],
            formula="revenue / average_assets",
        )

        result = PolicySemanticChecker().validate_ir(_ir(certificate))

        self.assertFalse(result.valid)
        self.assertEqual(result.policy_id, "standard_roa_assets")
        self.assertEqual(result.reason, "formula_not_allowed_by_policy")

    def test_roa_policy_accepts_average_assets_formula(self):
        certificate = VerificationCertificate(
            claim=CertificateClaim(metric="return_on_assets", claimed_value=0.01, unit="ratio"),
            facts=[
                CertificateFact("net_income_2022", 3.0, "USD millions", "Net income was $3 million", "chunk_1"),
                CertificateFact("total_assets_2022", 38363.0, "USD millions", "Total assets were $38,363 million", "chunk_1"),
                CertificateFact("total_assets_2021", 32963.0, "USD millions", "Total assets were $32,963 million", "chunk_1"),
            ],
            formula="net_income_2022 / ((total_assets_2022 + total_assets_2021) / 2) * 100",
        )

        result = PolicySemanticChecker().validate_ir(_ir(certificate))

        self.assertTrue(result.valid, result.reason)
        self.assertEqual(result.policy_id, "standard_roa_assets")

    def test_fixed_asset_turnover_policy_accepts_average_ppe_formula(self):
        certificate = VerificationCertificate(
            claim=CertificateClaim(metric="fixed_asset_turnover_ratio", claimed_value=24.26, unit="ratio"),
            facts=[
                CertificateFact("revenue_2019", 6489.0, "USD millions", "Total net revenues were $6,489 million", "chunk_1"),
                CertificateFact("ppe_2019", 253.0, "USD millions", "Property and equipment net was $253 million", "chunk_1"),
                CertificateFact("ppe_2018", 282.0, "USD millions", "Property and equipment net was $282 million", "chunk_1"),
            ],
            formula="revenue_2019 / ((ppe_2019 + ppe_2018) / 2)",
        )

        result = PolicySemanticChecker().validate_ir(_ir(certificate))

        self.assertTrue(result.valid, result.reason)
        self.assertEqual(result.policy_id, "standard_fixed_asset_turnover")

    def test_capex_percent_revenue_average_policy_accepts_three_year_formula(self):
        certificate = VerificationCertificate(
            claim=CertificateClaim(metric="capex_as_percent_of_revenue_3yr_avg", claimed_value=1.9, unit="percent"),
            facts=[
                CertificateFact("capex_2017", 155.0, "USD millions", "Capital expenditures were $155 million", "chunk_1"),
                CertificateFact("capex_2018", 131.0, "USD millions", "Capital expenditures were $131 million", "chunk_1"),
                CertificateFact("capex_2019", 116.0, "USD millions", "Capital expenditures were $116 million", "chunk_1"),
                CertificateFact("revenue_2017", 7017.0, "USD millions", "Total net revenues were $7,017 million", "chunk_1"),
                CertificateFact("revenue_2018", 7500.0, "USD millions", "Total net revenues were $7,500 million", "chunk_1"),
                CertificateFact("revenue_2019", 6489.0, "USD millions", "Total net revenues were $6,489 million", "chunk_1"),
            ],
            formula="((capex_2017 / revenue_2017) + (capex_2018 / revenue_2018) + (capex_2019 / revenue_2019)) / 3 * 100",
        )

        result = PolicySemanticChecker().validate_ir(_ir(certificate))

        self.assertTrue(result.valid, result.reason)
        self.assertEqual(result.policy_id, "standard_capex_as_percent_of_revenue_average")

    def test_direct_capex_policy_does_not_match_compound_capex_metric_by_substring(self):
        policy = DEFAULT_POLICY_REGISTRY.find_policy("capex_as_percent_of_revenue_unknown_form")

        self.assertIsNone(policy)

    def test_quick_ratio_policy_accepts_liquid_asset_formula(self):
        certificate = VerificationCertificate(
            claim=CertificateClaim(metric="quick_ratio", claimed_value=1.5, unit="ratio"),
            facts=[
                CertificateFact("cash", 10.0, "USD millions", "Cash and cash equivalents were $10 million", "chunk_1"),
                CertificateFact("short_term_investments", 5.0, "USD millions", "Short-term investments were $5 million", "chunk_1"),
                CertificateFact("receivables", 15.0, "USD millions", "Accounts receivable were $15 million", "chunk_1"),
                CertificateFact("current_liabilities", 20.0, "USD millions", "Total current liabilities were $20 million", "chunk_1"),
            ],
            formula="(cash + short_term_investments + receivables) / current_liabilities",
        )

        result = PolicySemanticChecker().validate_ir(_ir(certificate))

        self.assertTrue(result.valid, result.reason)
        self.assertEqual(result.policy_id, "standard_quick_ratio")

    def test_direct_net_ppne_policy_accepts_millions_to_billions_lookup(self):
        certificate = VerificationCertificate(
            claim=CertificateClaim(metric="net_ppne", claimed_value=8.738, unit="USD billions"),
            facts=[
                CertificateFact(
                    "net_property_plant_equipment",
                    8738.0,
                    "USD millions",
                    "Property, plant and equipment - net $ 8,738 $ 8,866",
                    "chunk_1",
                    row_label="Property plant and equipment net",
                    column="2018",
                ),
            ],
            formula="net_property_plant_equipment / 1000",
        )

        result = PolicySemanticChecker().validate_ir(_ir(certificate))

        self.assertTrue(result.valid, result.reason)
        self.assertEqual(result.policy_id, "direct_net_ppne")
        self.assertEqual(result.role_bindings["ppe"], "net_property_plant_equipment")

    def test_unknown_metric_is_skipped(self):
        certificate = VerificationCertificate(
            claim=CertificateClaim(metric="company_specific_metric", claimed_value=1.0, unit="ratio"),
            facts=[
                CertificateFact("custom_fact", 1.0, "ratio", "Custom fact was 1.0", "chunk_1"),
            ],
            formula="custom_fact",
        )

        result = PolicySemanticChecker().validate_ir(_ir(certificate))

        self.assertTrue(result.valid)
        self.assertEqual(result.status, "no_policy")


if __name__ == "__main__":
    unittest.main()
