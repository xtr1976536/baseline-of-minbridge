"""Canonical-formula grounding catches a wrong *formula* as an SMT counterexample.

XBRL grounding gives the solver an independent source for inputs; this gives it an
independent source for the *formula* (the policy registry). For a metric with a policy,
an extra constraint recomputes the metric from the canonical formula over the IR's own
fact variables and checks the claim against it — so a wrong formula (right inputs)
becomes UNSAT instead of riding through SAT. Additive: no policy / unresolved roles ->
nothing appended.
"""
import unittest

from verifiqa.policy.registry import load_policy_registry
from verifiqa.types import VerificationFact, VerificationIR
from verifiqa.verification.policy_formula import (
    _infix_to_smt,
    augment_smt_with_policy_formula,
    resolve_policy_formula,
)

_REG = load_policy_registry()


def _ir(metric, facts, claimed, tol=0.5, precision=1, fact_unit="USD millions", claim_unit="percent"):
    return VerificationIR(
        metric=metric,
        formula="",
        facts={n: VerificationFact(name=n, value=v, unit=fact_unit) for n, v in facts.items()},
        claimed_value=claimed,
        claim_unit=claim_unit,
        tolerance=tol,
        precision_digits=precision,
    )


_NETFLIX_BASE = """(set-logic QF_NRA)
(declare-const computed_ebitda_margin_percent Real)
(declare-const operating_income Real)
(declare-const da_property_equipment_intangibles Real)
(declare-const revenue Real)
(assert (= operating_income 305.826))
(assert (= da_property_equipment_intangibles 62.283))
(assert (= revenue 6779.511))
(check-sat)
"""


class TranslatorTests(unittest.TestCase):
    def test_precedence_and_substitution(self):
        s = _infix_to_smt("(a + b) / c * 100", {"a": "A", "b": "B", "c": "C"})
        self.assertEqual(s, "(* (/ (+ A B) C) 100)")

    def test_nested_average(self):
        s = _infix_to_smt("ni / ((s + e) / 2)", {"ni": "NI", "s": "S", "e": "E"})
        self.assertEqual(s, "(/ NI (/ (+ S E) 2))")


class AugmentationTests(unittest.TestCase):
    def test_emits_canonical_constraint_for_covered_metric(self):
        ir = _ir("ebitda_margin_percent",
                 {"operating_income": 305.826, "da_property_equipment_intangibles": 62.283, "revenue": 6779.511},
                 claimed=56.8)
        out = augment_smt_with_policy_formula(_NETFLIX_BASE, ir, _REG)
        self.assertIn("policy_formula_ebitda_margin_percent", out)
        # canonical (op + da)/rev*100 inlined; revenue guarded as denominator
        self.assertIn("(* (/ (+ operating_income da_property_equipment_intangibles) revenue) 100)", out)
        self.assertIn("(or (> revenue 0) (< revenue 0))", out)

    def test_scale_variant_does_not_false_positive(self):
        # net_ppe has templates ["ppe", "ppe / 1000"]; the claim is in billions while the
        # fact is in millions. The disjunction must accept the "ppe / 1000" form (SAT).
        try:
            import z3
        except ImportError:
            self.skipTest("z3 not installed")
        ir = _ir("net_ppe", {"net_ppe": 8738.0}, claimed=8.738, precision=3)
        base = """(set-logic QF_NRA)
(declare-const net_ppe Real)
(assert (= net_ppe 8738.0))
(check-sat)
"""
        out = augment_smt_with_policy_formula(base, ir, _REG)
        self.assertIn("policy_formula_net_ppe", out)
        s = z3.Solver(); s.from_string(out)
        self.assertEqual(s.check(), z3.sat)

    def test_fixed_asset_turnover_resolves_average_ppe(self):
        ir = _ir(
            "fixed_asset_turnover_ratio",
            {"ppe_fy2018": 282.0, "ppe_fy2019": 253.0, "revenue_fy2019": 6489.0},
            claimed=24.26,
            tol=0.01,
            precision=2,
            claim_unit="ratio",
        )
        base = """(set-logic QF_NRA)
(declare-const ppe_fy2018 Real)
(declare-const ppe_fy2019 Real)
(declare-const revenue_fy2019 Real)
(check-sat)
"""
        out = augment_smt_with_policy_formula(base, ir, _REG)

        self.assertIn("policy_formula_fixed_asset_turnover_ratio", out)
        self.assertIn("(+ ppe_fy2018 ppe_fy2019)", out)

    def test_no_policy_is_noop(self):
        ir = _ir("some_bespoke_metric", {"x": 1.0}, claimed=5.0)
        self.assertEqual(augment_smt_with_policy_formula(_NETFLIX_BASE, ir, _REG), _NETFLIX_BASE)

    def test_unresolved_roles_is_noop(self):
        # ebitda policy needs D&A; without a D&A-named fact the role can't resolve.
        ir = _ir("ebitda_margin_percent",
                 {"operating_income": 305.826, "revenue": 6779.511}, claimed=56.8)
        base = """(set-logic QF_NRA)
(declare-const operating_income Real)
(declare-const revenue Real)
(check-sat)
"""
        self.assertEqual(augment_smt_with_policy_formula(base, ir, _REG), base)

    def test_skips_when_variable_not_declared(self):
        # Canonical formula must reference already-declared variables; a fact missing
        # from the SMT means no constraint (would otherwise be a free variable).
        ir = _ir("ebitda_margin_percent",
                 {"operating_income": 305.826, "da_property_equipment_intangibles": 62.283, "revenue": 6779.511},
                 claimed=56.8)
        base = """(set-logic QF_NRA)
(declare-const operating_income Real)
(declare-const revenue Real)
(check-sat)
"""
        self.assertEqual(augment_smt_with_policy_formula(base, ir, _REG), base)


class ResolutionTests(unittest.TestCase):
    def test_effective_tax_rate_change_resolves_period_roles_from_percent_values(self):
        ir = _ir(
            "effective_tax_rate_change",
            {"effective_tax_rate_2021": 24.6, "effective_tax_rate_2022": 21.6},
            claimed=-3.0,
            tol=0.1,
            precision=1,
            fact_unit="percent",
        )
        resolved = resolve_policy_formula(ir, _REG)

        self.assertEqual(resolved["status"], "applied")
        self.assertEqual(resolved["policy_id"], "financebench_effective_tax_rate_change")
        self.assertEqual(
            resolved["formula"],
            "effective_tax_rate_2022 - effective_tax_rate_2021",
        )
        self.assertAlmostEqual(resolved["computed_value"], -3.0)

    def test_effective_tax_rate_change_uses_xbrl_ratio_values_for_percentage_points(self):
        ir = _ir(
            "effective_tax_rate_change",
            {"effective_tax_rate_fy2021": 24.6, "effective_tax_rate_fy2022": 21.6},
            claimed=-3.0,
            tol=0.1,
            precision=1,
            fact_unit="percent",
        )
        ir.xbrl_calculations = {
            "bindings": [
                {
                    "fact_name": "effective_tax_rate_fy2021",
                    "xbrl_value": 0.246,
                    "binding_multiplier": 1.0,
                    "unit_measures": ["pure"],
                    "unit_ref": "USD",
                },
                {
                    "fact_name": "effective_tax_rate_fy2022",
                    "xbrl_value": 0.216,
                    "binding_multiplier": 1.0,
                    "unit_measures": ["pure"],
                    "unit_ref": "USD",
                },
            ]
        }

        resolved = resolve_policy_formula(ir, _REG)

        self.assertEqual(resolved["status"], "applied")
        self.assertEqual(
            resolved["formula"],
            "(effective_tax_rate_fy2022 - effective_tax_rate_fy2021) * 100",
        )
        self.assertAlmostEqual(resolved["computed_value"], -3.0)

    def test_effective_tax_rate_ignores_usd_xbrl_label_collision(self):
        ir = _ir(
            "effective_tax_rate_change",
            {"effective_tax_rate_2021": 24.6, "effective_tax_rate_2022": 21.6},
            claimed=-3.0,
            tol=0.1,
            precision=1,
            fact_unit="percent",
        )
        ir.xbrl_calculations = {
            "bindings": [
                {
                    "fact_name": "effective_tax_rate_2021",
                    "xbrl_value": 780000000,
                    "binding_multiplier": 1.0,
                    "unit_ref": "USD",
                    "unit_measures": ["USD"],
                    "concept": "us-gaap:UnrecognizedTaxBenefitsThatWouldImpactEffectiveTaxRate",
                },
                {
                    "fact_name": "effective_tax_rate_2022",
                    "xbrl_value": 750000000,
                    "binding_multiplier": 1.0,
                    "unit_ref": "USD",
                    "unit_measures": ["USD"],
                    "concept": "us-gaap:UnrecognizedTaxBenefitsThatWouldImpactEffectiveTaxRate",
                },
            ]
        }

        resolved = resolve_policy_formula(ir, _REG)

        self.assertEqual(resolved["status"], "applied")
        self.assertEqual(resolved["formula"], "effective_tax_rate_2022 - effective_tax_rate_2021")
        self.assertAlmostEqual(resolved["computed_value"], -3.0)


    def test_period_decorated_direct_capex_metric_resolves(self):
        ir = _ir(
            "fy2018_capital_expenditure",
            {"fy2018_purchases_of_ppe": 1577.0},
            claimed=1577.0,
            fact_unit="USD millions",
            claim_unit="USD millions",
        )

        resolved = resolve_policy_formula(ir, _REG)

        self.assertEqual(resolved["status"], "applied")
        self.assertEqual(resolved["policy_id"], "direct_capital_expenditure")
        self.assertEqual(resolved["formula"], "fy2018_purchases_of_ppe")

    def test_numeric_only_mode_resolves_formula_despite_fact_unit_label_mismatch(self):
        ir = _ir(
            "fy2018_capital_expenditure",
            {"fy2018_purchases_of_ppe": 1577.0},
            claimed=1577.0,
            fact_unit="ratio",
            claim_unit="USD millions",
        )

        default_resolved = resolve_policy_formula(ir, _REG)
        numeric_only_resolved = resolve_policy_formula(
            ir,
            _REG,
            ignore_unit_matching=True,
        )

        self.assertEqual(default_resolved["status"], "unresolved")
        self.assertIn("policy_role_constraints_failed", default_resolved["reason"])
        self.assertEqual(numeric_only_resolved["status"], "applied")
        self.assertEqual(numeric_only_resolved["formula"], "fy2018_purchases_of_ppe")
        self.assertAlmostEqual(numeric_only_resolved["computed_value"], 1577.0)

    def test_days_payable_outstanding_resolves_period_roles(self):
        ir = _ir(
            "days_payable_outstanding_fy2017",
            {
                "accounts_payable_fy2016": 2533.0,
                "accounts_payable_fy2017": 3461.0,
                "cost_of_sales_fy2017": 111934.0,
                "inventories_fy2016": 11461.0,
                "inventories_fy2017": 16047.0,
            },
            claimed=36.73,
            tol=0.01,
            precision=2,
            fact_unit="USD millions",
            claim_unit="days",
        )

        resolved = resolve_policy_formula(ir, _REG)

        self.assertEqual(resolved["status"], "applied")
        self.assertEqual(resolved["policy_id"], "standard_days_payable_outstanding")
        self.assertIn("accounts_payable_fy2016", resolved["formula"])
        self.assertIn("accounts_payable_fy2017", resolved["formula"])

    def test_cagr_policy_emits_solver_constraint(self):
        ir = _ir(
            "revenue_cagr_2year",
            {"fy2020_total_net_sales": 100.0, "fy2022_total_net_sales": 121.0},
            claimed=10.0,
            tol=0.01,
            precision=1,
            fact_unit="USD millions",
            claim_unit="percent",
        )
        base = """(set-logic QF_NRA)
(declare-const fy2020_total_net_sales Real)
(declare-const fy2022_total_net_sales Real)
(assert (= fy2020_total_net_sales 100.0))
(assert (= fy2022_total_net_sales 121.0))
(check-sat)
"""

        resolved = resolve_policy_formula(ir, _REG)
        out = augment_smt_with_policy_formula(base, ir, _REG)

        self.assertEqual(resolved["status"], "applied")
        self.assertAlmostEqual(resolved["computed_value"], 10.0)
        self.assertIn("policy_formula_revenue_cagr_2year", out)
        self.assertIn("policy_value_revenue_cagr_2year", out)

    def test_raw_unit_can_rescue_bad_canonical_unit_label(self):
        ir = VerificationIR(
            metric="adjusted_non_gaap_ebitda",
            formula="adjusted_ebitda_fy2023",
            facts={
                "adjusted_ebitda_fy2023": VerificationFact(
                    name="adjusted_ebitda_fy2023",
                    value=2018.0,
                    unit="USD/share",
                    raw_unit="USD millions",
                    row_label="Adjusted EBITDA, EBIT, Net income and EPS",
                    source_quote="Adjusted EBITDA, EBIT, Net income and EPS 2,018",
                )
            },
            claimed_value=2018.0,
            claim_unit="USD millions",
            tolerance=0.5,
        )

        resolved = resolve_policy_formula(ir, _REG)

        self.assertEqual(resolved["status"], "applied")
        self.assertEqual(resolved["policy_id"], "direct_adjusted_non_gaap_ebitda")

    def test_adjusted_ebit_rejects_operating_income_source_label(self):
        ir = VerificationIR(
            metric="interest_coverage_ratio",
            formula="adjusted_ebit / interest_expense",
            facts={
                "adjusted_ebit": VerificationFact(
                    name="adjusted_ebit",
                    value=1439.372,
                    unit="USD millions",
                    row_label="Operating income (loss)",
                    source_quote="Operating income (loss)  (1,896) 368,847 1,439,372",
                ),
                "interest_expense": VerificationFact(
                    name="interest_expense",
                    value=594.954,
                    unit="USD millions",
                    row_label="Interest expense, net of amounts capitalized",
                ),
            },
            claimed_value=2.4,
            claim_unit="ratio",
            tolerance=0.01,
        )

        resolved = resolve_policy_formula(ir, _REG)

        self.assertEqual(resolved["status"], "unresolved")
        self.assertEqual(resolved["reason"], "policy_role_constraints_failed:adjusted_ebit")

    def test_interest_coverage_rejects_operating_income_plus_da_substitute(self):
        ir = VerificationIR(
            metric="interest_coverage_ratio",
            formula="(operating_income + depreciation_and_amortization) / interest_expense",
            facts={
                "operating_income": VerificationFact(
                    name="operating_income",
                    value=1439.372,
                    unit="USD millions",
                    row_label="Operating income",
                ),
                "depreciation_and_amortization": VerificationFact(
                    name="depreciation_and_amortization",
                    value=3482.050,
                    unit="USD millions",
                    row_label="Depreciation and amortization",
                ),
                "interest_expense": VerificationFact(
                    name="interest_expense",
                    value=594.954,
                    unit="USD millions",
                    row_label="Interest expense, net of amounts capitalized",
                ),
            },
            claimed_value=8.27,
            claim_unit="ratio",
            tolerance=0.01,
        )

        resolved = resolve_policy_formula(ir, _REG)

        self.assertEqual(resolved["status"], "unresolved")
        self.assertEqual(resolved["reason"], "policy_role_constraints_failed:adjusted_ebit")

    def test_interest_coverage_floors_negative_adjusted_ebit_to_zero(self):
        ir = VerificationIR(
            metric="interest_coverage_ratio",
            formula="adjusted_ebit / interest_expense",
            facts={
                "adjusted_ebit": VerificationFact(
                    name="adjusted_ebit",
                    value=-10.0,
                    unit="USD millions",
                    row_label="Adjusted EBIT",
                ),
                "interest_expense": VerificationFact(
                    name="interest_expense",
                    value=5.0,
                    unit="USD millions",
                    row_label="Interest expense",
                ),
            },
            claimed_value=0.0,
            claim_unit="ratio",
            tolerance=0.01,
        )

        resolved = resolve_policy_formula(ir, _REG)

        self.assertEqual(resolved["status"], "applied")
        self.assertEqual(resolved["formula"], "coverage_ratio(adjusted_ebit, interest_expense)")
        self.assertAlmostEqual(resolved["computed_value"], 0.0)

    def test_interest_coverage_uses_adjusted_ebitdar_bridge_when_ebit_absent(self):
        ir = VerificationIR(
            metric="interest_coverage_ratio",
            formula="coverage_ratio(adjusted_ebitdar - depreciation_and_amortization - lease_rent_expense, interest_expense)",
            facts={
                "adjusted_ebitdar": VerificationFact(
                    name="adjusted_ebitdar",
                    value=3497.254,
                    unit="USD millions",
                    row_label="Adjusted EBITDAR",
                    source_quote="Adjusted EBITDAR 3,497,254",
                ),
                "depreciation_and_amortization": VerificationFact(
                    name="depreciation_and_amortization",
                    value=3482.050,
                    unit="USD millions",
                    row_label="Depreciation and amortization",
                    source_quote="Depreciation and amortization 3,482,050",
                ),
                "lease_rent_expense": VerificationFact(
                    name="lease_rent_expense",
                    value=1950.566,
                    unit="USD millions",
                    row_label="Triple-net operating lease and ground lease rent expense",
                    source_quote="Triple-net operating lease and ground lease rent expense 1,950,566",
                ),
                "interest_expense": VerificationFact(
                    name="interest_expense",
                    value=594.954,
                    unit="USD millions",
                    row_label="Interest expense, net of amounts capitalized",
                    source_quote="Interest expense, net of amounts capitalized 594,954",
                ),
            },
            claimed_value=0.0,
            claim_unit="ratio",
            tolerance=0.01,
        )

        resolved = resolve_policy_formula(ir, _REG)

        self.assertEqual(resolved["status"], "applied")
        self.assertEqual(
            resolved["formula"],
            "coverage_ratio(adjusted_ebitdar - depreciation_and_amortization - lease_rent_expense, interest_expense)",
        )
        self.assertAlmostEqual(resolved["computed_value"], 0.0)

    def test_consumer_health_separation_gain_scales_millions_to_billions(self):
        ir = VerificationIR(
            metric="consumer_health_separation_gain",
            formula="separation_gain",
            facts={
                "separation_gain": VerificationFact(
                    name="separation_gain",
                    value=20000.0,
                    unit="USD millions",
                    source_quote="gain of approximately $20 billion from the separation",
                )
            },
            claimed_value=20.0,
            claim_unit="ratio",
            tolerance=0.5,
        )

        resolved = resolve_policy_formula(ir, _REG)

        self.assertEqual(resolved["status"], "applied")
        self.assertEqual(resolved["policy_id"], "financebench_consumer_health_separation_gain")
        self.assertEqual(resolved["formula"], "separation_gain / 1000")
        self.assertAlmostEqual(resolved["computed_value"], 20.0)
        self.assertEqual(resolved["policy_metadata"]["claim_unit"], "USD billions")

    def test_kenvue_cash_proceeds_scales_millions_to_billions(self):
        ir = VerificationIR(
            metric="kenvue_separation_cash_proceeds",
            formula="cash_proceeds_kenvue",
            facts={
                "cash_proceeds_kenvue": VerificationFact(
                    name="cash_proceeds_kenvue",
                    value=13200.0,
                    unit="USD millions",
                    source_quote="cash proceeds from the Kenvue debt offering and initial public offering",
                )
            },
            claimed_value=13.2,
            claim_unit="ratio",
            tolerance=0.05,
        )

        resolved = resolve_policy_formula(ir, _REG)

        self.assertEqual(resolved["status"], "applied")
        self.assertEqual(resolved["policy_id"], "financebench_kenvue_separation_cash_proceeds")
        self.assertEqual(resolved["formula"], "cash_proceeds_kenvue / 1000")
        self.assertAlmostEqual(resolved["computed_value"], 13.2)
        self.assertEqual(resolved["policy_metadata"]["claim_unit"], "USD billions")

    def test_restructuring_policy_prefers_document_fact_over_companyfacts_collision(self):
        ir = VerificationIR(
            metric="restructuring_costs",
            formula="total_restructuring_and_impairment_charges",
            facts={
                "total_restructuring_and_impairment_charges": VerificationFact(
                    name="total_restructuring_and_impairment_charges",
                    value=411.0,
                    unit="USD millions",
                    row_label="Total restructuring and impairment charges",
                )
            },
            claimed_value=411.0,
            claim_unit="USD millions",
            tolerance=0.5,
            xbrl_calculations={
                "bindings": [
                    {
                        "fact_name": "total_restructuring_and_impairment_charges",
                        "xbrl_value": 0.0,
                        "binding_multiplier": 1.0,
                        "source": "edgar_companyfacts_fy",
                        "unit_ref": "USD",
                        "unit_measures": ["USD"],
                    }
                ]
            },
        )

        resolved = resolve_policy_formula(ir, _REG)

        self.assertEqual(resolved["status"], "applied")
        self.assertEqual(resolved["policy_id"], "financebench_restructuring_costs_income_statement")
        self.assertAlmostEqual(resolved["computed_value"], 411.0)
        self.assertEqual(resolved["policy_metadata"]["source_priority"], "document")

    def test_upjohn_future_costs_uses_incurred_amount_and_percent_incurred(self):
        ir = VerificationIR(
            metric="upjohn_spinoff_future_costs",
            formula="total_separation_costs * (100 - percent_incurred) / 100",
            facts={
                "total_separation_costs": VerificationFact(
                    name="total_separation_costs",
                    value=700.0,
                    unit="USD millions",
                    source_quote="costs of approximately $700 million in connection with separating Upjohn",
                ),
                "percent_incurred": VerificationFact(
                    name="percent_incurred",
                    value=90.0,
                    unit="percent",
                    source_quote="approximately 90% has been incurred",
                ),
            },
            claimed_value=77.78,
            claim_unit="USD millions",
            tolerance=0.01,
        )

        resolved = resolve_policy_formula(ir, _REG)

        self.assertEqual(resolved["status"], "applied")
        self.assertEqual(resolved["policy_id"], "financebench_upjohn_spinoff_future_costs")
        self.assertEqual(
            resolved["formula"],
            "total_separation_costs * (100 - percent_incurred) / percent_incurred",
        )
        self.assertAlmostEqual(resolved["computed_value"], 77.77777777777777)

    def test_cash_dividends_policy_prefers_positive_amount_paid(self):
        ir = VerificationIR(
            metric="cash_dividends_paid",
            formula="-dividends_paid / 1000",
            facts={
                "dividends_paid": VerificationFact(
                    name="dividends_paid",
                    value=-389.0,
                    unit="USD millions",
                )
            },
            claimed_value=-0.389,
            claim_unit="USD billions",
            tolerance=0.0005,
            precision_digits=3,
            xbrl_calculations={
                "bindings": [
                    {"fact_name": "dividends_paid", "xbrl_value": 389.0, "binding_multiplier": 1.0}
                ]
            },
        )

        resolved = resolve_policy_formula(ir, _REG)

        self.assertEqual(resolved["status"], "applied")
        self.assertEqual(resolved["formula"], "dividends_paid / 1000")
        self.assertAlmostEqual(resolved["computed_value"], 0.389)
        self.assertGreater(resolved["claim_error"], 0.7)


class SolverTests(unittest.TestCase):
    def test_wrong_formula_is_unsat(self):
        try:
            import z3
        except ImportError:
            self.skipTest("z3 not installed")
        ir = _ir("ebitda_margin_percent",
                 {"operating_income": 305.826, "da_property_equipment_intangibles": 62.283, "revenue": 6779.511},
                 claimed=56.8)  # wrong: LLM added content amortization. canonical = 5.43
        out = augment_smt_with_policy_formula(_NETFLIX_BASE, ir, _REG)
        s = z3.Solver(); s.from_string(out)
        self.assertEqual(s.check(), z3.unsat)

    def test_correct_formula_is_sat(self):
        try:
            import z3
        except ImportError:
            self.skipTest("z3 not installed")
        ir = _ir("ebitda_margin_percent",
                 {"operating_income": 305.826, "da_property_equipment_intangibles": 62.283, "revenue": 6779.511},
                 claimed=5.4)  # correct canonical value
        out = augment_smt_with_policy_formula(_NETFLIX_BASE, ir, _REG)
        s = z3.Solver(); s.from_string(out)
        self.assertEqual(s.check(), z3.sat)


if __name__ == "__main__":
    unittest.main()
