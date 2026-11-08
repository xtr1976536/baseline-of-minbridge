import unittest

from verifiqa.types import VerificationFact, VerificationIR
from verifiqa.verification.finqa_table import _bind_fact_table, attach_table_calculations


def _fact(name, row_label, value=0.0, unit="USD millions"):
    return VerificationFact(
        name=name,
        value=value,
        unit=unit,
        row_label=row_label,
        fact_type="numeric",
    )


class FinqaTableBindingTests(unittest.TestCase):
    def test_binds_by_row_and_year_value_blind(self):
        table = [
            ["in millions", "december 312013", "december 312012"],
            ["commercial mortgages", "$ 586", "$ 772"],
            ["total residential mortgages", "1356", "2220"],
        ]
        binding = _bind_fact_table(
            _fact("total_residential_mortgages_2013", "total residential mortgages", value=999999.0),
            table,
        )

        self.assertIsNotNone(binding)
        self.assertEqual(binding["source"], "finqa_table")
        self.assertEqual(binding["xbrl_value"], 1356.0)
        self.assertEqual(binding["context_id"], "table_r2_c1")

    def test_splits_ocr_mashed_digit_letter_row_labels(self):
        table = [
            ["december 31 ( in millions )", "2008", "2007"],
            ["total tier 1capital", "$ 136104", "$ 88746"],
            ["risk-weighted assets", "$ 1244659", "$ 1051879"],
        ]
        binding = _bind_fact_table(_fact("total_tier_1_capital_2008", "total tier 1 capital"), table)

        self.assertIsNotNone(binding)
        self.assertEqual(binding["xbrl_value"], 136104.0)


    def test_binds_when_period_is_in_row_and_column_is_named_series(self):
        table = [
            ["date", "citi", "s&p 500"],
            ["31-dec-2012", "100.0", "100.0"],
            ["31-dec-2017", "193.5", "208.1"],
        ]
        fact = VerificationFact(
            name="citi_end_value",
            value=0.0,
            unit="index",
            row_label="31-dec-2017",
            column="citi",
            period="31-dec-2017",
        )

        binding = _bind_fact_table(fact, table)

        self.assertIsNotNone(binding)
        self.assertEqual(binding["xbrl_value"], 193.5)
        self.assertEqual(binding["context_id"], "table_r2_c1")

    def test_binds_one_token_row_with_named_measure_column(self):
        table = [
            ["", "oil ( mmbbls )", "gas ( bcf )", "total ( mmboe )"],
            ["canada", "23", "198", "60"],
            ["total", "66", "894", "243"],
        ]
        fact = VerificationFact(
            name="canada_mmboe",
            value=0.0,
            unit="mmboe",
            row_label="canada",
            column="total ( mmboe )",
            period="2007",
        )

        binding = _bind_fact_table(fact, table)

        self.assertIsNotNone(binding)
        self.assertEqual(binding["xbrl_value"], 60.0)
        self.assertEqual(binding["context_id"], "table_r1_c3")

    def test_binds_single_value_column_when_period_is_in_row_label(self):
        table = [
            ["", "amount ( in millions )"],
            ["2009 net revenue", "$ 536.7"],
            ["2010 net revenue", "$ 555.3"],
        ]
        fact = VerificationFact(
            name="net_revenue_2010",
            value=0.0,
            unit="USD millions",
            row_label="2010 net revenue",
            column="amount ( in millions )",
            period="2010",
        )

        binding = _bind_fact_table(fact, table)

        self.assertIsNotNone(binding)
        self.assertEqual(binding["xbrl_value"], 555.3)
        self.assertEqual(binding["context_id"], "table_r2_c1")


    def test_uses_binding_multiplier_for_table_scale_to_fact_unit(self):
        table = [
            ["company", "payments volume ( billions )", "total transactions ( billions )"],
            ["american express", "$ 637", "5.0"],
        ]
        payment = VerificationFact(
            name="payments_volume",
            value=637000.0,
            unit="USD millions",
            row_label="american express",
            column="payments volume ( billions )",
            period="2008",
        )
        transactions = VerificationFact(
            name="total_transactions",
            value=5000.0,
            unit="count millions",
            row_label="american express",
            column="total transactions ( billions )",
            period="2008",
        )

        payment_binding = _bind_fact_table(payment, table)
        transaction_binding = _bind_fact_table(transactions, table)

        self.assertIsNotNone(payment_binding)
        self.assertIsNotNone(transaction_binding)
        self.assertEqual(payment_binding["xbrl_value"], 637.0)
        self.assertEqual(payment_binding["binding_multiplier"], 1000.0)
        self.assertEqual(transaction_binding["xbrl_value"], 5.0)
        self.assertEqual(transaction_binding["binding_multiplier"], 1000.0)

    def test_attach_requires_all_numeric_facts_to_bind(self):
        table = [
            ["in millions", "2013", "2012"],
            ["total residential mortgages", "1356", "2220"],
        ]
        ir = VerificationIR(
            metric="mortgage_change",
            formula="total_residential_mortgages_2013 - missing_fact_2013",
            facts={
                "total_residential_mortgages_2013": _fact(
                    "total_residential_mortgages_2013", "total residential mortgages"
                ),
                "missing_fact_2013": _fact("missing_fact_2013", "not in table"),
            },
            claimed_value=0.0,
            claim_unit="USD millions",
            tolerance=0.5,
        )

        attach_table_calculations(ir, table)

        self.assertEqual(ir.xbrl_calculations["source"], "finqa_table")
        self.assertEqual(ir.xbrl_calculations["status"], "partial_table_bindings")
        self.assertEqual(ir.xbrl_calculations["grounding_status"], "PARTIAL_TABLE_BINDINGS")
        self.assertEqual(ir.xbrl_calculations["bindings"], [])
        self.assertEqual(ir.xbrl_calculations["partial_bindings"], ["total_residential_mortgages_2013"])

    def test_attach_marks_full_table_grounding_ok(self):
        table = [
            ["in millions", "2013", "2012"],
            ["total residential mortgages", "1356", "2220"],
        ]
        ir = VerificationIR(
            metric="total_residential_mortgages",
            formula="total_residential_mortgages_2013",
            facts={
                "total_residential_mortgages_2013": _fact(
                    "total_residential_mortgages_2013", "total residential mortgages"
                ),
            },
            claimed_value=1356.0,
            claim_unit="USD millions",
            tolerance=0.5,
        )

        attach_table_calculations(ir, table)

        self.assertEqual(ir.xbrl_calculations["status"], "ok")
        self.assertEqual(ir.xbrl_calculations["grounding_status"], "TABLE_OK")
        self.assertEqual(ir.xbrl_calculations["binding_sources"], ["finqa_table"])
        self.assertEqual(ir.xbrl_calculations["bindings"][0]["xbrl_value"], 1356.0)


if __name__ == "__main__":
    unittest.main()
