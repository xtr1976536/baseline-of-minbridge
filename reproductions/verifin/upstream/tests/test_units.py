import unittest

from verifiqa.types import CertificateFact
from verifiqa.units import normalize_fact_quantity


class UnitNormalizationTests(unittest.TestCase):
    def test_thousands_to_usd_millions(self):
        fact = CertificateFact(
            name="operating_income",
            raw_value=305826.0,
            raw_unit="USD",
            source_scale="thousands",
            source_scale_quote="in thousands",
            value=305.826,
            unit="USD millions",
            source_quote="Operating income 305,826 (in thousands)",
            chunk_id="chunk",
        )

        normalized = normalize_fact_quantity(fact, "Operating income 305,826 (in thousands)", strict=True)

        self.assertEqual(normalized.unit, "USD millions")
        self.assertEqual(normalized.source_scale, "thousands")
        self.assertAlmostEqual(normalized.value, 305.826)

    def test_thousands_grounded_by_chunk_scale_quote(self):
        fact = CertificateFact(
            name="revenue",
            raw_value=6779511.0,
            raw_unit="USD",
            source_scale="thousands",
            source_scale_quote="in thousands",
            value=6779.511,
            unit="USD millions",
            source_quote="Revenues $ 6,779,511",
            chunk_id="chunk",
        )

        normalized = normalize_fact_quantity(
            fact,
            "Consolidated statements of operations (in thousands) Revenues $ 6,779,511",
            strict=True,
        )

        self.assertEqual(normalized.raw_value, 6779511.0)
        self.assertEqual(normalized.source_scale, "thousands")
        self.assertAlmostEqual(normalized.value, 6779.511)

    def test_raw_units_to_usd_millions(self):
        fact = CertificateFact(
            name="credit_agreement",
            raw_value=400000000.0,
            raw_unit="USD",
            source_scale="ones",
            value=400.0,
            unit="USD millions",
            source_quote="credit agreement increased by $400,000,000",
            chunk_id="chunk",
        )

        normalized = normalize_fact_quantity(fact, "credit agreement increased by $400,000,000", strict=True)

        self.assertEqual(normalized.source_scale, "ones")
        self.assertAlmostEqual(normalized.value, 400.0)

    def test_billions_to_usd_millions(self):
        fact = CertificateFact(
            name="borrowing_capacity",
            raw_value=8.7,
            raw_unit="USD",
            source_scale="billions",
            source_scale_quote="$8.7 billion",
            value=8700.0,
            unit="USD millions",
            source_quote="borrowing capacity was $8.7 billion",
            chunk_id="chunk",
        )

        normalized = normalize_fact_quantity(fact, "borrowing capacity was $8.7 billion", strict=True)

        self.assertEqual(normalized.raw_value, 8.7)
        self.assertEqual(normalized.source_scale, "billions")
        self.assertAlmostEqual(normalized.value, 8700.0)

    def test_parenthesized_negative_millions(self):
        fact = CertificateFact(
            name="net_loss",
            raw_value=-505.0,
            raw_unit="USD",
            source_scale="millions",
            source_scale_quote="million",
            value=-505.0,
            unit="USD millions",
            source_quote="Net loss (505) million",
            chunk_id="chunk",
        )

        normalized = normalize_fact_quantity(fact, "Net loss (505) million", strict=True)

        self.assertEqual(normalized.raw_value, -505.0)
        self.assertEqual(normalized.source_scale, "millions")
        self.assertAlmostEqual(normalized.value, -505.0)

    def test_capex_parenthetical_outflow_normalizes_to_positive_magnitude(self):
        fact = CertificateFact(
            name="capex_fy2018",
            raw_value=-1577.0,
            raw_unit="USD",
            source_scale="millions",
            source_scale_quote="Millions",
            sign_convention="magnitude",
            value=-1577.0,
            unit="USD millions",
            row_label="Purchases of property, plant and equipment (PP&E)",
            source_quote="Purchases of property, plant and equipment (PP&E) (1,577)",
            chunk_id="chunk",
        )

        normalized = normalize_fact_quantity(fact, "(Millions) " + fact.source_quote, strict=True)

        self.assertEqual(normalized.raw_value, -1577.0)
        self.assertEqual(normalized.source_scale, "millions")
        self.assertEqual(normalized.value, 1577.0)

    def test_per_share_usd_fact_is_not_scaled_to_millions(self):
        fact = CertificateFact(
            name="tbvps",
            raw_value=66.56,
            raw_unit="USD",
            source_scale="ones",
            value=66.56,
            unit="USD",
            row_label="TBVPS",
            source_quote="The Firm grew TBVPS, ending the first quarter of 2021 at $66.56",
            chunk_id="chunk",
        )

        normalized = normalize_fact_quantity(fact, fact.source_quote, strict=True)

        self.assertEqual(normalized.unit, "USD/share")
        self.assertEqual(normalized.source_scale, "ones")
        self.assertAlmostEqual(normalized.value, 66.56)

    def test_rejects_bad_canonical_value(self):
        fact = CertificateFact(
            name="operating_income",
            raw_value=305826.0,
            raw_unit="USD",
            source_scale="thousands",
            source_scale_quote="in thousands",
            value=306.0,
            unit="USD millions",
            source_quote="Operating income 305,826",
            chunk_id="chunk",
        )

        with self.assertRaisesRegex(ValueError, "canonical_value_mismatch"):
            normalize_fact_quantity(fact, "Amounts in thousands. Operating income 305,826", strict=True)

    def test_accepts_equivalent_unambiguous_scale_when_copied_quote_differs(self):
        fact = CertificateFact(
            name="accounts_payable",
            raw_value=1174.0,
            raw_unit="USD",
            source_scale="millions",
            source_scale_quote="In millions, except share and per share amounts",
            value=1174.0,
            unit="USD millions",
            source_quote="Accounts payable 1,174",
            chunk_id="chunk",
        )

        normalized = normalize_fact_quantity(
            fact,
            "Consolidated Balance Sheets. In millions, except per share amounts. Accounts payable 1,174",
            strict=True,
        )

        self.assertEqual(normalized.source_scale, "millions")
        self.assertAlmostEqual(normalized.value, 1174.0)

    def test_accepts_compacted_pdf_scale_phrase(self):
        fact = CertificateFact(
            name="accounts_payable",
            raw_value=1174.0,
            raw_unit="USD",
            source_scale="millions",
            source_scale_quote="In millions, except share and per share amounts",
            value=1174.0,
            unit="USD millions",
            source_quote="Accountspayable 1,174",
            chunk_id="chunk",
        )

        normalized = normalize_fact_quantity(
            fact,
            "December31, (Inmillions,exceptshareandpershareamounts) 2020 2019 Accountspayable 1,174 1,587",
            strict=True,
        )

        self.assertEqual(normalized.source_scale, "millions")
        self.assertAlmostEqual(normalized.value, 1174.0)

    def test_rejects_copied_scale_quote_when_chunk_scale_is_ambiguous(self):
        fact = CertificateFact(
            name="accounts_payable",
            raw_value=1174.0,
            raw_unit="USD",
            source_scale="millions",
            source_scale_quote="In millions, except share and per share amounts",
            value=1174.0,
            unit="USD millions",
            source_quote="Accounts payable 1,174",
            chunk_id="chunk",
        )

        with self.assertRaisesRegex(ValueError, "ambiguous_source_scale"):
            normalize_fact_quantity(
                fact,
                "Amounts in thousands. Segment table in millions. Accounts payable 1,174",
                strict=True,
            )

    def test_accepts_absence_implies_zero_fact(self):
        fact = CertificateFact(
            name="restructuring_costs",
            fact_type="absence_implies_zero",
            raw_value=None,
            raw_unit="USD",
            source_scale="ones",
            value=0.0,
            unit="USD millions",
            source_quote="There were no such costs in 2020, 2021 or 2022",
            chunk_id="chunk",
            period="2022",
            absence_scope={
                "metric": "restructuring costs",
                "period": "2022",
                "statement": "income statement",
            },
        )

        normalized = normalize_fact_quantity(
            fact,
            (
                "costs directly associated with a major restructuring program. "
                "There were no such costs in 2020, 2021 or 2022."
            ),
            strict=True,
        )

        self.assertIsNone(normalized.raw_value)
        self.assertEqual(normalized.source_scale, "ones")
        self.assertEqual(normalized.value, 0.0)

    def test_rejects_absence_zero_without_absence_language(self):
        fact = CertificateFact(
            name="restructuring_costs",
            fact_type="absence_implies_zero",
            value=0.0,
            unit="USD millions",
            source_quote="Restructuring costs were discussed for 2022",
            chunk_id="chunk",
            period="2022",
            absence_scope={"metric": "restructuring costs", "period": "2022"},
        )

        with self.assertRaisesRegex(ValueError, "absence_not_supported"):
            normalize_fact_quantity(
                fact,
                "Restructuring costs were discussed for 2022.",
                strict=True,
            )


if __name__ == "__main__":
    unittest.main()
