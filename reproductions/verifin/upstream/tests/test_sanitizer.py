import unittest

from verifiqa.formalization.formalizer import certificate_to_claim_schema
from verifiqa.formulas.evaluator import formula_domain_constraints_smt
from verifiqa.types import CertificateClaim, CertificateFact, VerificationCertificate
from verifiqa.verification.smt_sanitizer import SmtSanitizer

from smt_helpers import render_counterexample_smt


class SanitizerTests(unittest.TestCase):
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

    def test_rejects_missing_formula_assertion_name(self):
        smtlib = render_counterexample_smt(self.claim, self.schema)
        smtlib = smtlib.replace(":named formula_quick_ratio", ":named formula_wrong_name")
        validation = SmtSanitizer().validate(smtlib, self.claim, self.schema)
        self.assertEqual(validation.smt_status, "invalid")
        self.assertIn("missing_named_formula_assertion", validation.reason)

    def test_accepts_changed_formula_body(self):
        # Formula correctness is now caught by Z3, not the sanitizer.
        smtlib = render_counterexample_smt(self.claim, self.schema)
        smtlib = smtlib.replace(
            "(/ (+ cash short_term_investments receivables) current_liabilities)",
            "(/ (+ cash short_term_investments receivables) cash)",
        )
        validation = SmtSanitizer().validate(smtlib, self.claim, self.schema)
        self.assertEqual(validation.smt_status, "valid")

    def test_rejects_declared_but_unconstrained_required_fact(self):
        smtlib = render_counterexample_smt(self.claim, self.schema)
        smtlib = "\n".join(
            line for line in smtlib.splitlines()
            if ":named evidence_current_liabilities" not in line
        )
        validation = SmtSanitizer().validate(smtlib, self.claim, self.schema)
        self.assertEqual(validation.smt_status, "invalid")
        self.assertIn("missing_named_evidence_assertion:current_liabilities", validation.reason)

    def test_accepts_extra_whitespace_in_declarations(self):
        smtlib = render_counterexample_smt(self.claim, self.schema)
        smtlib = smtlib.replace("(declare-const cash Real)", "(declare-const   cash   Real )")
        validation = SmtSanitizer().validate(smtlib, self.claim, self.schema)
        self.assertEqual(validation.smt_status, "valid", validation.reason)

    def test_accepts_structurally_equivalent_nested_cagr_multiplication(self):
        certificate = VerificationCertificate(
            claim=CertificateClaim(metric="revenue_cagr_2020_2022", claimed_value=0.4, unit="percent"),
            facts=[
                CertificateFact("revenue_2020", 65398.0, "USD millions", "Revenue was 65,398", "chunk_1"),
                CertificateFact("revenue_2022", 65984.0, "USD millions", "Revenue was 65,984", "chunk_1"),
            ],
            formula="cagr_percent(revenue_2022, revenue_2020, 2)",
            tolerance=0.05,
        )
        claim, schema = certificate_to_claim_schema(certificate)
        smtlib = """
        (set-option :produce-models true)
        (declare-const computed_revenue_cagr_2020_2022 Real)
        (declare-const revenue_2020 Real)
        (declare-const revenue_2022 Real)
        (assert (! (= revenue_2020 65398.0) :named evidence_revenue_2020))
        (assert (! (= revenue_2022 65984.0) :named evidence_revenue_2022))
        (assert (!
          (= (* revenue_2020
                (* (+ 1 (/ computed_revenue_cagr_2020_2022 100))
                   (+ 1 (/ computed_revenue_cagr_2020_2022 100))))
             revenue_2022)
          :named formula_revenue_cagr_2020_2022))
        (assert (> computed_revenue_cagr_2020_2022 -100))
        (assert (!
          (or
            (> (- computed_revenue_cagr_2020_2022 0.4) 0.05)
            (> (- 0.4 computed_revenue_cagr_2020_2022) 0.05))
          :named violation_claim_tolerance))
        (check-sat)
        (get-model)
        """

        for index, constraint in enumerate(
            formula_domain_constraints_smt(
                f"computed_{schema.metric}",
                schema.formula,
                schema.computed_unit or schema.claim_unit,
            )
        ):
            smtlib += f"\n(assert (! {constraint} :named domain_{schema.metric}_{index}))"

        validation = SmtSanitizer().validate(smtlib, claim, schema)

        self.assertEqual(validation.smt_status, "valid", validation.reason)

    def test_accepts_semantically_equivalent_division_shape(self):
        certificate = VerificationCertificate(
            claim=CertificateClaim(metric="cash_conversion_cycle", claimed_value=-3.65, unit="days"),
            facts=[
                CertificateFact("inventory_2019", 1559.3, "USD millions", "Inventories 1,559.3", "chunk_1"),
                CertificateFact("inventory_2018", 1642.2, "USD millions", "Inventories 1,642.2", "chunk_1"),
                CertificateFact("accounts_receivable_2019", 1679.7, "USD millions", "Receivables 1,679.7", "chunk_1"),
                CertificateFact("accounts_receivable_2018", 1684.2, "USD millions", "Receivables 1,684.2", "chunk_1"),
                CertificateFact("accounts_payable_2019", 2854.1, "USD millions", "Accounts payable 2,854.1", "chunk_1"),
                CertificateFact("accounts_payable_2018", 2746.2, "USD millions", "Accounts payable 2,746.2", "chunk_1"),
                CertificateFact("cogs_2019", 11108.4, "USD millions", "Cost of sales 11,108.4", "chunk_1"),
                CertificateFact("revenue_2019", 16865.2, "USD millions", "Net sales 16,865.2", "chunk_1"),
            ],
            formula=(
                "365 * ((inventory_2019 + inventory_2018) / 2) / cogs_2019 + "
                "365 * ((accounts_receivable_2019 + accounts_receivable_2018) / 2) / revenue_2019 - "
                "365 * ((accounts_payable_2019 + accounts_payable_2018) / 2) / "
                "(cogs_2019 + (inventory_2019 - inventory_2018))"
            ),
            tolerance=0.005,
        )
        claim, schema = certificate_to_claim_schema(certificate)
        smtlib = """
        (set-option :produce-models true)
        (declare-const computed_cash_conversion_cycle Real)
        (declare-const accounts_payable_2018 Real)
        (declare-const accounts_payable_2019 Real)
        (declare-const accounts_receivable_2018 Real)
        (declare-const accounts_receivable_2019 Real)
        (declare-const cogs_2019 Real)
        (declare-const inventory_2018 Real)
        (declare-const inventory_2019 Real)
        (declare-const revenue_2019 Real)
        (assert (! (= accounts_payable_2018 2746.2) :named evidence_accounts_payable_2018))
        (assert (! (= accounts_payable_2019 2854.1) :named evidence_accounts_payable_2019))
        (assert (! (= accounts_receivable_2018 1684.2) :named evidence_accounts_receivable_2018))
        (assert (! (= accounts_receivable_2019 1679.7) :named evidence_accounts_receivable_2019))
        (assert (! (= cogs_2019 11108.4) :named evidence_cogs_2019))
        (assert (! (= inventory_2018 1642.2) :named evidence_inventory_2018))
        (assert (! (= inventory_2019 1559.3) :named evidence_inventory_2019))
        (assert (! (= revenue_2019 16865.2) :named evidence_revenue_2019))
        (assert (!
          (= computed_cash_conversion_cycle
             (- (+ (* 365 (/ (/ (+ inventory_2019 inventory_2018) 2) cogs_2019))
                   (* 365 (/ (/ (+ accounts_receivable_2019 accounts_receivable_2018) 2) revenue_2019)))
                (* 365 (/ (/ (+ accounts_payable_2019 accounts_payable_2018) 2)
                          (+ cogs_2019 (- inventory_2019 inventory_2018))))))
          :named formula_cash_conversion_cycle))
        (assert (!
          (or
            (> (- computed_cash_conversion_cycle -3.65) 0.005)
            (> (- -3.65 computed_cash_conversion_cycle) 0.005))
          :named violation_claim_tolerance))
        (check-sat)
        (get-model)
        """

        for index, constraint in enumerate(
            formula_domain_constraints_smt(
                f"computed_{schema.metric}",
                schema.formula,
                schema.computed_unit or schema.claim_unit,
            )
        ):
            smtlib += f"\n(assert (! {constraint} :named domain_{schema.metric}_{index}))"

        validation = SmtSanitizer().validate(smtlib, claim, schema)

        self.assertEqual(validation.smt_status, "valid", validation.reason)


if __name__ == "__main__":
    unittest.main()
