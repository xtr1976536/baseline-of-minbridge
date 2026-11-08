import unittest

from verifiqa.formalization.certificate_validator import CertificateValidator
from verifiqa.types import (
    CertificateClaim,
    CertificateFact,
    EvidenceChunk,
    RetrievalFact,
    RetrievalPlan,
    VerificationCertificate,
)


def make_certificate(**overrides):
    fact = CertificateFact(
        name="property_plant_equipment_net_2018",
        value=8738.0,
        unit="USD millions",
        source_quote="Property, plant and equipment net was $8,738 million",
        chunk_id="chunk_1",
        period="FY2018",
        row_label="Property, plant and equipment net",
        column="2018",
        raw_value=8738.0,
        source_scale="millions",
        source_scale_quote="$8,738 million",
    )
    certificate = VerificationCertificate(
        claim=CertificateClaim(
            metric="net_ppne",
            claimed_value=8.738,
            unit="USD billions",
            period="FY2018",
        ),
        facts=[fact],
        formula="property_plant_equipment_net_2018 / 1000",
        calculation="8738 / 1000 = 8.738",
        tolerance=0.01,
    )
    for key, value in overrides.items():
        setattr(certificate, key, value)
    return certificate


class CertificateValidatorTests(unittest.TestCase):
    def setUp(self):
        self.chunk = EvidenceChunk(
            chunk_id="chunk_1",
            doc_name="3M_2018_10K",
            page=42,
            text="Property, plant and equipment net was $8,738 million as of December 31, 2018.",
        )

    def test_accepts_grounded_certificate(self):
        result = CertificateValidator().validate(
            make_certificate(),
            [self.chunk],
            "The year end FY2018 net PPNE for 3M is $8.738 billion USD.",
        )
        self.assertTrue(result.valid, result.reason)

    def test_numeric_only_mode_allows_missing_units_but_keeps_grounding_checks(self):
        cert = make_certificate()
        cert.claim.unit = ""
        cert.facts[0].unit = ""

        default_result = CertificateValidator().validate(
            cert,
            [self.chunk],
            "The year end FY2018 net PPNE for 3M is 8.738.",
        )
        numeric_only_result = CertificateValidator().validate(
            cert,
            [self.chunk],
            "The year end FY2018 net PPNE for 3M is 8.738.",
            require_units=False,
        )

        self.assertFalse(default_result.valid)
        self.assertEqual(default_result.reason, "claim_missing_unit")
        self.assertTrue(numeric_only_result.valid, numeric_only_result.reason)

    def test_ignores_unused_facts_before_grounding_checks(self):
        cert = make_certificate()
        cert.facts.append(
            CertificateFact(
                name="accumulated_depreciation",
                value=16135.0,
                unit="USD millions",
                source_quote="not in evidence",
                chunk_id="missing_chunk",
            )
        )

        result = CertificateValidator().validate(
            cert,
            [self.chunk],
            "The year end FY2018 net PPNE for 3M is $8.738 billion USD.",
        )

        self.assertTrue(result.valid, result.reason)

    def test_rejects_statement_fact_from_notes_page(self):
        cert = VerificationCertificate(
            claim=CertificateClaim(metric="return_on_assets", claimed_value=0.01, unit="percent"),
            facts=[
                CertificateFact(
                    name="net_income_2022",
                    raw_value=3.0,
                    raw_unit="USD",
                    source_scale="millions",
                    source_scale_quote="in millions",
                    value=3.0,
                    unit="USD millions",
                    source_quote="Net income attributable to The AES Corporation $ — $ (3) $ (192)",
                    chunk_id="aes_notes",
                    period="2022",
                    row_label="Net income attributable to The AES Corporation",
                )
            ],
            formula="net_income_2022",
            tolerance=0.005,
        )
        chunk = EvidenceChunk(
            chunk_id="aes_notes",
            doc_name="AES_2022_10K",
            page=180,
            text=(
                "Notes to Consolidated Financial Statements—(Continued). "
                "Amounts are in millions. Net income attributable to The AES Corporation $ — $ (3) $ (192)"
            ),
        )
        plan = RetrievalPlan(
            metric="return_on_assets",
            facts=[
                RetrievalFact(
                    name="net_income_2022",
                    aliases=["net income"],
                    period="2022",
                    statement="income statement",
                )
            ],
        )

        result = CertificateValidator().validate(
            cert,
            [chunk],
            "The ROA is 0.01%.",
            retrieval_plan=plan,
        )

        self.assertFalse(result.valid)
        self.assertIn("fact_source_statement_mismatch:net_income_2022", result.reason)

    def test_rejects_fact_value_not_in_chunk(self):
        # Grounding is now against the independent source: the fact's reported
        # number must appear in the chunk text, regardless of the LLM quote.
        cert = make_certificate()
        cert.facts[0].value = 9999.0
        cert.facts[0].raw_value = 9999.0
        cert.facts[0].source_quote = "Property, plant and equipment net was $9,999 million"
        result = CertificateValidator().validate(
            cert,
            [self.chunk],
            "The year end FY2018 net PPNE for 3M is $8.738 billion USD.",
        )
        self.assertFalse(result.valid)
        self.assertIn("fact_value_not_in_chunk", result.reason)

    def test_accepts_value_grounded_despite_paraphrased_quote(self):
        # A paraphrased / non-verbatim quote no longer fails as long as the
        # reported value is present in the chunk.
        cert = make_certificate()
        cert.facts[0].source_quote = "PP&E, net ... $8,738 (in millions)"
        result = CertificateValidator().validate(
            cert,
            [self.chunk],
            "The year end FY2018 net PPNE for 3M is $8.738 billion USD.",
        )
        self.assertTrue(result.valid, result.reason)

    def test_accepts_compact_pdf_table_quote(self):
        cert = VerificationCertificate(
            claim=CertificateClaim(
                metric="restructuring_costs",
                claimed_value=411.0,
                unit="USD millions",
                reported_value=411.0,
            ),
            facts=[
                CertificateFact(
                    name="restructuring_and_impairment_charges",
                    raw_value=411.0,
                    raw_unit="USD",
                    source_scale="millions",
                    source_scale_quote="(in millions)",
                    value=411.0,
                    unit="USD millions",
                    source_quote="Restructuring and impairment charges411",
                    chunk_id="pepsico",
                )
            ],
            formula="restructuring_and_impairment_charges",
            tolerance=0.5,
        )
        chunk = EvidenceChunk(
            chunk_id="pepsico",
            doc_name="PEPSICO_2022_10K",
            page=94,
            text=(
                "Consolidated Statement of Cash Flows (in millions) 202220212020 "
                "Restructuring and impairment charges411247289"
            ),
        )

        result = CertificateValidator().validate(
            cert,
            [chunk],
            "The verified restructuring costs is 411 USD millions.",
        )

        self.assertTrue(result.valid, result.reason)

    def test_rejects_value_absent_from_chunk(self):
        # The fact claims 8,738 but the chunk only contains 8,700, so the value
        # is not grounded in the independent source.
        cert = make_certificate()
        cert.facts[0].value = 8738.0
        chunk = EvidenceChunk(
            chunk_id="chunk_1",
            doc_name="3M_2018_10K",
            page=42,
            text="Property, plant and equipment net was $8,700 million as of December 31, 2018.",
        )
        result = CertificateValidator().validate(
            cert,
            [chunk],
            "The year end FY2018 net PPNE for 3M is $8.738 billion USD.",
        )
        self.assertFalse(result.valid)
        self.assertIn("fact_value_not_in_chunk", result.reason)

    def test_accepts_grounded_thousands_scale_to_usd_millions(self):
        cert = VerificationCertificate(
            claim=CertificateClaim(metric="ebitda_margin", claimed_value=5.43, unit="percent"),
            facts=[
                CertificateFact(
                    name="operating_income",
                    value=305.826,
                    unit="USD millions",
                    source_quote="Operating income 305,826",
                    chunk_id="chunk_netflix",
                    raw_value=305826.0,
                    source_scale="thousands",
                    source_scale_quote="(in thousands)",
                ),
                CertificateFact(
                    name="revenue",
                    value=6779.511,
                    unit="USD millions",
                    source_quote="Revenues $ 6,779,511",
                    chunk_id="chunk_netflix",
                    raw_value=6779511.0,
                    source_scale="thousands",
                    source_scale_quote="(in thousands)",
                ),
            ],
            formula="operating_income / revenue * 100",
            tolerance=0.05,
        )
        chunk = EvidenceChunk(
            chunk_id="chunk_netflix",
            doc_name="NETFLIX_2015_10K",
            page=1,
            text="Consolidated statements of operations (in thousands) Operating income 305,826 Revenues $ 6,779,511",
        )

        result = CertificateValidator().validate(cert, [chunk], "The EBITDA margin is 5.43%.")

        self.assertTrue(result.valid, result.reason)

    def test_accepts_scale_grounded_by_previous_page_context_prefix(self):
        cert = VerificationCertificate(
            claim=CertificateClaim(metric="operating_cash_flow_ratio", claimed_value=0.66, unit="ratio"),
            facts=[
                CertificateFact(
                    name="cash_from_operations",
                    raw_value=1469502.0,
                    raw_unit="USD",
                    source_scale="thousands",
                    source_scale_quote="(In thousands)",
                    value=1469.502,
                    unit="USD millions",
                    source_quote="Net cash provided by operating activities 1,469,502",
                    chunk_id="cash_flow_continuation",
                ),
                CertificateFact(
                    name="current_liabilities",
                    raw_value=2213556.0,
                    raw_unit="USD",
                    source_scale="thousands",
                    source_scale_quote="(In thousands)",
                    value=2213.556,
                    unit="USD millions",
                    source_quote="Total current liabilities 2,213,556",
                    chunk_id="balance_sheet",
                ),
            ],
            formula="cash_from_operations / current_liabilities",
            tolerance=0.005,
        )
        chunks = [
            EvidenceChunk(
                chunk_id="cash_flow_continuation",
                doc_name="ADOBE_2015_10K",
                page=92,
                text=(
                    "[previous page table header/scale context from corpus:ADOBE_2015_10K:p91]\n"
                    "CONSOLIDATED STATEMENTS OF CASH FLOWS\n"
                    "(In thousands)\n\n"
                    "Net cash provided by operating activities 1,469,502"
                ),
            ),
            EvidenceChunk(
                chunk_id="balance_sheet",
                doc_name="ADOBE_2015_10K",
                page=89,
                text=(
                    "CONSOLIDATED BALANCE SHEETS\n"
                    "(In thousands, except par value)\n"
                    "Total current liabilities 2,213,556"
                ),
            ),
        ]

        result = CertificateValidator().validate(cert, chunks, "The operating cash flow ratio is 0.66.")

        self.assertTrue(result.valid, result.reason)

    def test_rejects_missing_source_scale_when_canonical_value_differs(self):
        cert = VerificationCertificate(
            claim=CertificateClaim(metric="operating_income", claimed_value=305.826, unit="USD millions"),
            facts=[
                CertificateFact(
                    name="operating_income",
                    value=305.826,
                    unit="USD millions",
                    source_quote="Operating income 305,826",
                    chunk_id="chunk_1",
                    raw_value=305826.0,
                )
            ],
            formula="operating_income",
        )
        chunk = EvidenceChunk(
            chunk_id="chunk_1",
            doc_name="NETFLIX_2015_10K",
            page=1,
            text="Operating income 305,826",
        )

        result = CertificateValidator().validate(cert, [chunk], "Operating income was 305.826 million.")

        self.assertFalse(result.valid)
        self.assertIn("missing_source_scale", result.reason)

    def test_rejects_ambiguous_source_scale_without_quote(self):
        cert = VerificationCertificate(
            claim=CertificateClaim(metric="operating_income", claimed_value=305.826, unit="USD millions"),
            facts=[
                CertificateFact(
                    name="operating_income",
                    value=305.826,
                    unit="USD millions",
                    source_quote="Operating income 305,826",
                    chunk_id="chunk_1",
                    raw_value=305826.0,
                    source_scale="thousands",
                )
            ],
            formula="operating_income",
        )
        chunk = EvidenceChunk(
            chunk_id="chunk_1",
            doc_name="NETFLIX_2015_10K",
            page=1,
            text="Amounts in thousands. Segment table in millions. Operating income 305,826",
        )

        result = CertificateValidator().validate(cert, [chunk], "Operating income was 305.826 million.")

        self.assertFalse(result.valid)
        self.assertIn("ambiguous_source_scale", result.reason)

    def test_rejects_claim_not_in_answer(self):
        result = CertificateValidator().validate(
            make_certificate(),
            [self.chunk],
            "The year end FY2018 net PPNE for 3M is $8.70 billion USD.",
        )
        self.assertFalse(result.valid)
        self.assertIn("claimed_value_not_supported_by_answer", result.reason)

    def test_accepts_blank_percent_table_cell_as_grounded_zero(self):
        cert = VerificationCertificate(
            claim=CertificateClaim(
                metric="real_change_in_sales",
                claimed_value=0.0,
                unit="percent",
                reported_value=0.0,
            ),
            facts=[
                CertificateFact(
                    name="comparable_constant_currency_growth",
                    raw_value=0.0,
                    raw_unit="percent",
                    source_scale="ones",
                    value=0.0,
                    unit="percent",
                    source_quote="Comparable Constant Currency Growth % 1 (3)",
                    chunk_id="amcor_growth",
                    row_label="Comparable Constant Currency Growth %",
                    column="Total",
                    period="Twelve Months Ended June 30",
                )
            ],
            formula="comparable_constant_currency_growth",
            tolerance=0.5,
        )
        chunk = EvidenceChunk(
            chunk_id="amcor_growth",
            doc_name="AMCOR_2023Q4_EARNINGS",
            page=9,
            text=(
                "Twelve Months Ended June 30 Flexibles Rigid Packaging Total "
                "Comparable Constant Currency Growth % 1 (3) Volume % (3) (4) (3)"
            ),
        )

        result = CertificateValidator().validate(cert, [chunk], "The real growth was flat, or 0%.")

        self.assertTrue(result.valid, result.reason)

    def test_accepts_reported_value_in_answer(self):
        cert = make_certificate()
        cert.claim.claimed_value = 8.738
        cert.claim.reported_value = 8.74
        result = CertificateValidator().validate(
            cert,
            [self.chunk],
            "The year end FY2018 net PPNE for 3M is $8.74 billion USD.",
        )
        self.assertTrue(result.valid, result.reason)

    def test_accepts_absence_implies_zero_when_question_allows_it(self):
        cert = VerificationCertificate(
            claim=CertificateClaim(
                metric="restructuring_costs",
                claimed_value=0.0,
                unit="USD millions",
                period="2022",
                reported_value=0.0,
            ),
            facts=[
                CertificateFact(
                    name="restructuring_costs",
                    fact_type="absence_implies_zero",
                    value=0.0,
                    unit="USD millions",
                    source_quote="There were no such costs in 2020, 2021 or 2022",
                    chunk_id="aes",
                    period="2022",
                    raw_unit="USD",
                    source_scale="ones",
                    absence_scope={
                        "metric": "restructuring costs",
                        "period": "2022",
                        "statement": "income statement",
                    },
                )
            ],
            formula="restructuring_costs",
            calculation="0",
            tolerance=0.5,
        )
        chunk = EvidenceChunk(
            chunk_id="aes",
            doc_name="AES_2022_10K",
            page=95,
            text=(
                "costs directly associated with a major restructuring program. "
                "There were no such costs in 2020, 2021 or 2022."
            ),
        )

        result = CertificateValidator().validate(
            cert,
            [chunk],
            "The verified restructuring costs is 0 USD millions.",
            question=(
                "What is the quantity of restructuring costs directly outlined in AES "
                "Corporation's income statements for FY2022? If restructuring costs "
                "are not explicitly outlined then state 0."
            ),
        )

        self.assertTrue(result.valid, result.reason)

    def test_accepts_absence_implies_zero_from_statement_omission(self):
        table_header = "Consolidated Statements of Operations Years ended December 31, 2022, 2021, and 2020 "
        statement_quote = (
            "General and administrative expenses (207) "
            "Interest expense (1,117) Interest income 389 "
            "Loss on extinguishment of debt (15) Other expense (68) Other income 102 "
            "Loss on disposal and sale of business interests (9) "
            "Goodwill impairment expense (777) Asset impairment expense (763) "
            "Foreign currency transaction gains losses (77) Other non-operating expense (175)"
        )
        cert = VerificationCertificate(
            claim=CertificateClaim(
                metric="restructuring_costs",
                claimed_value=0.0,
                unit="USD millions",
                period="FY2022",
                reported_value=0.0,
            ),
            facts=[
                CertificateFact(
                    name="restructuring_costs",
                    fact_type="absence_implies_zero",
                    value=0.0,
                    unit="USD millions",
                    source_quote=statement_quote,
                    chunk_id="aes_stmt",
                    period="FY2022",
                    raw_unit="USD",
                    source_scale="ones",
                    row_label="Restructuring costs",
                    column="2022",
                    absence_scope={
                        "metric": "restructuring costs",
                        "period": "FY2022",
                        "statement": "Consolidated Statements of Operations",
                    },
                )
            ],
            formula="restructuring_costs",
            calculation="0",
            tolerance=0.5,
        )
        chunk = EvidenceChunk(
            chunk_id="aes_stmt",
            doc_name="AES_2022_10K",
            page=131,
            text=table_header + statement_quote,
        )

        result = CertificateValidator().validate(
            cert,
            [chunk],
            "The restructuring costs directly outlined were 0.",
            question=(
                "What is the quantity of restructuring costs directly outlined in AES "
                "Corporation's income statements for FY2022? If restructuring costs "
                "are not explicitly outlined then state 0."
            ),
        )

        self.assertTrue(result.valid, result.reason)

    def test_rejects_absence_implies_zero_when_question_does_not_allow_it(self):
        cert = VerificationCertificate(
            claim=CertificateClaim(metric="restructuring_costs", claimed_value=0.0, unit="USD millions"),
            facts=[
                CertificateFact(
                    name="restructuring_costs",
                    fact_type="absence_implies_zero",
                    value=0.0,
                    unit="USD millions",
                    source_quote="There were no such costs in 2020, 2021 or 2022",
                    chunk_id="aes",
                    period="2022",
                    absence_scope={"metric": "restructuring costs", "period": "2022"},
                )
            ],
            formula="restructuring_costs",
        )
        chunk = EvidenceChunk(
            chunk_id="aes",
            doc_name="AES_2022_10K",
            page=95,
            text="restructuring program. There were no such costs in 2020, 2021 or 2022.",
        )

        result = CertificateValidator().validate(
            cert,
            [chunk],
            "The verified restructuring costs is 0 USD millions.",
            question="What were restructuring costs in FY2022?",
        )

        self.assertFalse(result.valid)
        self.assertIn("absence_zero_not_allowed_by_question", result.reason)

    def test_rejects_absence_implies_zero_with_retrieval_failure_quote(self):
        """WBV vector: LLM generates retrieval-failure meta-statement as source_quote."""
        cert = VerificationCertificate(
            claim=CertificateClaim(
                metric="capital_expenditures",
                claimed_value=0.0,
                unit="USD millions",
                period="FY2018",
                reported_value=0.0,
            ),
            facts=[
                CertificateFact(
                    name="capital_expenditures",
                    fact_type="absence_implies_zero",
                    value=0.0,
                    unit="USD millions",
                    source_quote=(
                        "no capital expenditures data from the cash flow statement was retrieved"
                    ),
                    chunk_id="aes_cf",
                    period="FY2018",
                    raw_unit="USD",
                    source_scale="ones",
                    absence_scope={
                        "metric": "capital expenditures",
                        "period": "FY2018",
                        "statement": "cash flow statement",
                    },
                )
            ],
            formula="capital_expenditures",
            tolerance=0.5,
        )
        chunk = EvidenceChunk(
            chunk_id="aes_cf",
            doc_name="AES_2018_10K",
            page=60,
            text=(
                "no capital expenditures data from the cash flow statement was retrieved"
            ),
        )

        result = CertificateValidator().validate(
            cert,
            [chunk],
            "Capital expenditures were 0 USD millions.",
            question=(
                "What were capital expenditures for AES in FY2018? "
                "State 0 if not present."
            ),
        )

        self.assertFalse(result.valid)
        self.assertIn("absence_zero_retrieval_failure_not_filing_absence", result.reason)

    def test_rejects_absence_implies_zero_with_no_genuine_absence_language(self):
        """WBV vector: source_quote is in the chunk but contains no genuine absence phrase."""
        cert = VerificationCertificate(
            claim=CertificateClaim(
                metric="goodwill_impairment",
                claimed_value=0.0,
                unit="USD millions",
                reported_value=0.0,
            ),
            facts=[
                CertificateFact(
                    name="goodwill_impairment",
                    fact_type="absence_implies_zero",
                    value=0.0,
                    unit="USD millions",
                    source_quote="Goodwill as of December 31, 2021 and 2022 totals 3,200 and 3,450",
                    chunk_id="chunk_goodwill",
                    period="2022",
                    raw_unit="USD",
                    source_scale="millions",
                    source_scale_quote="in millions",
                    absence_scope={
                        "metric": "goodwill impairment",
                        "period": "2022",
                        "statement": "income statement",
                    },
                )
            ],
            formula="goodwill_impairment",
            tolerance=0.5,
        )
        chunk = EvidenceChunk(
            chunk_id="chunk_goodwill",
            doc_name="CORP_2022_10K",
            page=88,
            text=(
                "(in millions) Goodwill as of December 31, 2021 and 2022 totals 3,200 and 3,450"
            ),
        )

        result = CertificateValidator().validate(
            cert,
            [chunk],
            "Goodwill impairment was 0 USD millions.",
            question=(
                "What was the goodwill impairment charge for FY2022? "
                "State 0 if not explicitly outlined."
            ),
        )

        self.assertFalse(result.valid)
        self.assertIn("absence_zero_no_absence_language_in_quote", result.reason)

    def test_accepts_genuine_absence_quote_when_question_allows_zero(self):
        """Confirm the new checks don't block legitimate absence_implies_zero facts."""
        cert = VerificationCertificate(
            claim=CertificateClaim(
                metric="goodwill_impairment",
                claimed_value=0.0,
                unit="USD millions",
                reported_value=0.0,
            ),
            facts=[
                CertificateFact(
                    name="goodwill_impairment",
                    fact_type="absence_implies_zero",
                    value=0.0,
                    unit="USD millions",
                    source_quote="No goodwill impairment charges were recorded in fiscal 2022.",
                    chunk_id="chunk_goodwill",
                    period="2022",
                    raw_unit="USD",
                    source_scale="ones",
                    absence_scope={
                        "metric": "goodwill impairment",
                        "period": "2022",
                        "statement": "income statement",
                    },
                )
            ],
            formula="goodwill_impairment",
            tolerance=0.5,
        )
        chunk = EvidenceChunk(
            chunk_id="chunk_goodwill",
            doc_name="CORP_2022_10K",
            page=88,
            text="No goodwill impairment charges were recorded in fiscal 2022.",
        )

        result = CertificateValidator().validate(
            cert,
            [chunk],
            "Goodwill impairment was 0 USD millions.",
            question=(
                "What was the goodwill impairment charge for FY2022? "
                "State 0 if not explicitly outlined."
            ),
        )

        self.assertTrue(result.valid, result.reason)

    def test_accepts_absence_witness_paraphrase_grounded_by_chunk_omission(self):
        """Regression: the witness is the model's paraphrase of an omission (not
        present verbatim in the chunk), but the chunk is the right statement and
        genuinely omits the requested row, so the absence-zero is grounded."""
        statement_chunk = (
            "Consolidated Statements of Operations "
            "Years ended December 31, 2022, 2021, and 2020 "
            "Total revenue 12,617 Total cost of sales (10,069) Operating margin 2,548 "
            "General and administrative expenses (207) Interest expense (1,117) "
            "Interest income 389 Goodwill impairment expense (777) "
            "Asset impairment expense (763) Income tax expense (291)"
        )
        cert = VerificationCertificate(
            claim=CertificateClaim(
                metric="restructuring_costs",
                claimed_value=0.0,
                unit="USD millions",
                period="FY2022",
                reported_value=0.0,
            ),
            facts=[
                CertificateFact(
                    name="restructuring_costs_fy2022",
                    fact_type="absence_implies_zero",
                    value=0.0,
                    unit="USD millions",
                    source_quote=(
                        "Consolidated Statements of Operations Years ended "
                        "December 31, 2022, 2021, and 2020. The statement does not "
                        "contain a line item for restructuring costs."
                    ),
                    chunk_id="aes_stmt",
                    period="FY2022",
                    raw_unit="USD",
                    source_scale="ones",
                    row_label="Restructuring costs",
                    column="2022",
                    absence_scope={
                        "metric": "restructuring costs",
                        "period": "FY2022",
                        "statement": "Consolidated Statements of Operations",
                    },
                )
            ],
            formula="restructuring_costs_fy2022",
            calculation="0",
            tolerance=0.5,
        )
        chunk = EvidenceChunk(
            chunk_id="aes_stmt",
            doc_name="AES_2022_10K",
            page=131,
            text=statement_chunk,
        )

        result = CertificateValidator().validate(
            cert,
            [chunk],
            "The restructuring costs directly outlined were 0.",
            question=(
                "What is the quantity of restructuring costs directly outlined in "
                "AES Corporation's income statements for FY2022? If restructuring "
                "costs are not explicitly outlined then state 0."
            ),
        )

        self.assertTrue(result.valid, result.reason)


if __name__ == "__main__":
    unittest.main()
