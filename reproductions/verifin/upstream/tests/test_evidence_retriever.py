import unittest

from verifiqa.retrieval.evidence_retriever import EvidenceRetriever, _Bm25Index, _alias_has_table_values
from verifiqa.retrieval.table_rows import STRUCTURED_ROWS_HEADER, attach_structured_rows, extract_structured_rows
from verifiqa.types import EvidenceChunk, RetrievalFact, RetrievalPlan


class FakeReranker:
    def predict(self, pairs):
        return [10.0 if "reranker favorite" in text else 0.0 for _, text in pairs]


class EvidenceRetrieverTests(unittest.TestCase):
    def test_doc_name_filter_restricts_to_correct_filing(self):
        chunks = [
            EvidenceChunk(
                chunk_id="wrong:evidence:0",
                doc_name="Other_10K",
                page=1,
                text="Quick ratio evidence for an unrelated company with cash and liabilities.",
            ),
            EvidenceChunk(
                chunk_id="target:evidence:0",
                doc_name="Target_10K",
                page=2,
                text="Total assets were 100 and net income was 10.",
            ),
        ]
        result = EvidenceRetriever(chunks).retrieve(
            "What is the quick ratio?",
            doc_name="Target_10K",
            top_k=1,
        )
        self.assertEqual([chunk.chunk_id for chunk in result], ["target:evidence:0"])

    def test_doc_name_filter_works_when_corpus_has_no_company_metadata(self):
        chunks = [
            EvidenceChunk(
                chunk_id="wrong:evidence:0",
                doc_name="Other_10K",
                page=1,
                text="Cash was 5.",
                company="",
            ),
            EvidenceChunk(
                chunk_id="target:evidence:0",
                doc_name="Target_10K",
                page=2,
                text="Net income was 10.",
                company="",
            ),
        ]
        result = EvidenceRetriever(chunks).retrieve(
            "What is net income?",
            company="Target",
            doc_name="Target_10K",
            top_k=1,
        )
        self.assertEqual([chunk.chunk_id for chunk in result], ["target:evidence:0"])

    def test_filter_miss_returns_no_evidence(self):
        chunks = [
            EvidenceChunk(
                chunk_id="target:evidence:0",
                doc_name="Target_10K",
                page=2,
                text="Total assets were 100 and net income was 10.",
                company="Target",
            ),
        ]
        retriever = EvidenceRetriever(chunks)

        result = retriever.retrieve(
            "What is net income?",
            company="OtherCo",
            doc_name="Other_10K",
            top_k=1,
        )

        self.assertEqual(result, [])

    def test_financebench_id_filter_miss_returns_no_evidence(self):
        chunks = [
            EvidenceChunk(
                chunk_id="target:evidence:0",
                doc_name="Target_10K",
                page=2,
                text="Total assets were 100 and net income was 10.",
                financebench_id="target",
            ),
        ]
        retriever = EvidenceRetriever(chunks)

        result = retriever.retrieve(
            "What is net income?",
            financebench_id="missing",
            top_k=1,
        )

        self.assertEqual(result, [])

    def test_oracle_retrieval_prioritizes_gold_evidence_over_xbrl(self):
        chunks = [
            EvidenceChunk(
                chunk_id="q:xbrl:0",
                doc_name="Target_10K",
                page=None,
                text="Pension obligations and postretirement benefit liabilities.",
                source_type="xbrl",
                financebench_id="q",
            ),
            EvidenceChunk(
                chunk_id="q:xbrl:1",
                doc_name="Target_10K",
                page=None,
                text="More pension obligations and liabilities.",
                source_type="xbrl",
                financebench_id="q",
            ),
            EvidenceChunk(
                chunk_id="q:evidence:0",
                doc_name="Target_10K",
                page=93,
                text="Estimated Future Benefit Payments. 2024 Pension Benefits 1,097 Health Care and Life 862.",
                source_type="filing",
                financebench_id="q",
            ),
        ]

        result = EvidenceRetriever(chunks).retrieve(
            "How much did the company expect to pay retirees in 2024?",
            financebench_id="q",
            top_k=2,
        )

        self.assertEqual(result[0].chunk_id, "q:evidence:0")

    def test_top_k_can_exceed_first_stage_k(self):
        chunks = [
            EvidenceChunk(
                chunk_id=f"chunk:{i}",
                doc_name="Target_10K",
                page=i,
                text=f"Revenue evidence line {i}.",
            )
            for i in range(4)
        ]

        result = EvidenceRetriever(chunks, first_stage_k=2).retrieve(
            "What is revenue?",
            doc_name="Target_10K",
            top_k=4,
        )

        self.assertEqual(len(result), 4)

    def test_fact_targeted_retrieval_assembles_distinct_required_fact_pages(self):
        chunks = [
            EvidenceChunk(
                chunk_id="corpus:Target_10K:p10",
                doc_name="Target_10K",
                page=10,
                text="Management discussion with general comments about fixed asset turnover and revenue.",
                source_type="filing_page",
            ),
            EvidenceChunk(
                chunk_id="corpus:Target_10K:p58",
                doc_name="Target_10K",
                page=58,
                text="Consolidated statement of operations. Total revenues 194,579 for 2018.",
                source_type="filing_page",
            ),
            EvidenceChunk(
                chunk_id="corpus:Target_10K:p62",
                doc_name="Target_10K",
                page=62,
                text="Consolidated balance sheets. Property and equipment, net 11,349 for 2018 and 10,292 for 2017.",
                source_type="filing_page",
            ),
        ]
        plan = RetrievalPlan(
            metric="fixed_asset_turnover",
            facts=[
                RetrievalFact("revenue_2018", aliases=["Total revenues"], period="2018", statement="income statement"),
                RetrievalFact("ppe_2018_2017", aliases=["Property and equipment, net"], period="2018 2017", statement="balance sheet"),
            ],
        )

        result = EvidenceRetriever(chunks, first_stage_k=3).retrieve_with_plan(
            "What is FY2018 fixed asset turnover, defined as revenue divided by average PP&E?",
            plan,
            doc_name="Target_10K",
            top_k=2,
        )

        self.assertEqual(
            {chunk.chunk_id for chunk in result},
            {"corpus:Target_10K:p58", "corpus:Target_10K:p62"},
        )

    def test_expand_for_facts_promotes_targeted_missing_fact_page(self):
        chunks = [
            EvidenceChunk(
                chunk_id="corpus:Target_10K:p10",
                doc_name="Target_10K",
                page=10,
                text="Consolidated statements of operations. Net sales 100 for 2020.",
                source_type="filing_page",
            ),
            EvidenceChunk(
                chunk_id="corpus:Target_10K:p11",
                doc_name="Target_10K",
                page=11,
                text="General business discussion with no cash flow table.",
                source_type="filing_page",
            ),
            EvidenceChunk(
                chunk_id="corpus:Target_10K:p12",
                doc_name="Target_10K",
                page=12,
                text=(
                    "Consolidated statement of cash flows\n"
                    "2020\n2019\n"
                    "Depreciation and amortization\n"
                    "20\n18\n"
                ),
                source_type="filing_page",
            ),
        ]
        plan = RetrievalPlan(
            metric="ebitda_margin",
            facts=[
                RetrievalFact("revenue", aliases=["Net sales"], period="2020", statement="income statement"),
                RetrievalFact(
                    "depreciation_amortization",
                    aliases=["Depreciation and amortization", "D&A"],
                    period="2020",
                    statement="cash flow",
                ),
            ],
        )

        result = EvidenceRetriever(chunks, first_stage_k=3).expand_for_facts(
            "What is FY2020 EBITDA margin?",
            plan,
            [plan.facts[1]],
            existing_chunks=chunks[:2],
            doc_name="Target_10K",
            top_k=2,
        )

        self.assertEqual(result[0].chunk_id, "corpus:Target_10K:p12")
        self.assertEqual(len(result), 2)

    def test_planned_fact_ranking_uses_reranker_when_available(self):
        chunks = [
            EvidenceChunk(
                chunk_id="corpus:Target_10K:p1",
                doc_name="Target_10K",
                page=1,
                text="Revenue table with ordinary dense and lexical terms.",
                source_type="filing_page",
            ),
            EvidenceChunk(
                chunk_id="corpus:Target_10K:p2",
                doc_name="Target_10K",
                page=2,
                text="Revenue evidence reranker favorite.",
                source_type="filing_page",
            ),
            EvidenceChunk(
                chunk_id="corpus:Target_10K:p3",
                doc_name="Target_10K",
                page=3,
                text="Revenue note with ordinary dense and lexical terms.",
                source_type="filing_page",
            ),
        ]
        plan = RetrievalPlan(
            metric="revenue",
            facts=[
                RetrievalFact(
                    name="revenue",
                    aliases=["Revenue"],
                    period="2018",
                    statement="income statement",
                )
            ],
        )
        retriever = EvidenceRetriever(chunks, first_stage_k=3, rerank_planned_queries=True)
        retriever._reranker = FakeReranker()
        records = []
        retriever.set_debug_callback(records.append)

        result = retriever.retrieve_with_plan(
            "What is FY2018 revenue?",
            plan,
            doc_name="Target_10K",
            top_k=1,
        )

        self.assertEqual(result[0].chunk_id, "corpus:Target_10K:p2")
        fact_records = [record for record in records if "required fact:" in record["query_text"]]
        self.assertTrue(fact_records)
        self.assertTrue(fact_records[0]["reranker_applied"])
        self.assertEqual(fact_records[0]["limit"], 1)
        self.assertEqual(fact_records[0]["first_k"], 3)

    def test_bm25_scores_exact_financial_terms(self):
        chunks = [
            EvidenceChunk(
                chunk_id="corpus:Target_10K:p10",
                doc_name="Target_10K",
                page=10,
                text="General discussion of revenue and operating expenses.",
                source_type="filing_page",
            ),
            EvidenceChunk(
                chunk_id="corpus:Target_10K:p58",
                doc_name="Target_10K",
                page=58,
                text="Consolidated statements of operations. AlphaSegment recurring revenue 123 for 2020.",
                source_type="filing_page",
            ),
        ]

        scores = _Bm25Index(chunks).score(
            "What was AlphaSegment recurring revenue in 2020?",
            [0, 1],
        )

        self.assertGreater(scores[1], scores[0])

    def test_hybrid_retrieval_records_bm25_signal(self):
        chunks = [
            EvidenceChunk(
                chunk_id="corpus:Target_10K:p10",
                doc_name="Target_10K",
                page=10,
                text="General discussion of revenue and operating expenses.",
                source_type="filing_page",
            ),
            EvidenceChunk(
                chunk_id="corpus:Target_10K:p58",
                doc_name="Target_10K",
                page=58,
                text="Consolidated statements of operations. AlphaSegment recurring revenue 123 for 2020.",
                source_type="filing_page",
            ),
        ]
        retriever = EvidenceRetriever(chunks, retrieval_mode="hybrid", first_stage_k=2)
        records = []
        retriever.set_debug_callback(records.append)

        result = retriever.retrieve(
            "What was AlphaSegment recurring revenue in 2020?",
            doc_name="Target_10K",
            top_k=1,
        )

        self.assertEqual(result[0].chunk_id, "corpus:Target_10K:p58")
        self.assertEqual(records[0]["retrieval_mode"], "hybrid")
        by_chunk = {row["chunk_id"]: row for row in records[0]["first_stage"]}
        self.assertGreater(
            by_chunk["corpus:Target_10K:p58"]["bm25_score"],
            by_chunk["corpus:Target_10K:p10"]["bm25_score"],
        )

    def test_fact_targeted_retrieval_prefers_statement_row_over_note_table(self):
        chunks = [
            EvidenceChunk(
                chunk_id="corpus:Target_10K:p22",
                doc_name="Target_10K",
                page=22,
                text=(
                    "We recorded $1 million of project-related costs in cost of sales "
                    "in fiscal 2019 compared to $11 million in fiscal 2018."
                ),
                source_type="filing_page",
            ),
            EvidenceChunk(
                chunk_id="corpus:Target_10K:p53",
                doc_name="Target_10K",
                page=53,
                text=(
                    "Consolidated Statements of Earnings\n"
                    "Fiscal Year\n"
                    "2019\n2018\n2017\n"
                    "Net sales\n$ 16,865.2\n$ 15,740.4\n$ 15,619.8\n"
                    "Cost of sales\n11,108.4\n10,304.8\n10,052.0\n"
                ),
                source_type="filing_page",
            ),
            EvidenceChunk(
                chunk_id="corpus:Target_10K:p66",
                doc_name="Target_10K",
                page=66,
                text=(
                    "Restructuring and impairment charges and project-related costs "
                    "are classified in our Consolidated Statements of Earnings as follows:\n"
                    "Fiscal\nIn Millions\n2019\n2018\n2017\n"
                    "Cost of sales\n9.9\n14.0\n41.5\n"
                ),
                source_type="filing_page",
            ),
        ]
        plan = RetrievalPlan(
            metric="cash_conversion_cycle",
            facts=[
                RetrievalFact(
                    name="cogs_2019",
                    aliases=["Cost of sales", "Cost of goods sold", "COGS"],
                    period="2019",
                    statement="income statement",
                )
            ],
        )

        result = EvidenceRetriever(chunks, first_stage_k=3).retrieve_with_plan(
            "What is FY2019 cash conversion cycle using FY2019 COGS?",
            plan,
            doc_name="Target_10K",
            top_k=1,
        )

        self.assertEqual(result[0].chunk_id, "corpus:Target_10K:p53")

    def test_retrieved_page_includes_previous_table_scale_context(self):
        chunks = [
            EvidenceChunk(
                chunk_id="corpus:Target_10K:p10",
                doc_name="Target_10K",
                page=10,
                text=(
                    "CONSOLIDATED STATEMENTS OF CASH FLOWS\n"
                    "(In thousands)\n"
                    "Years Ended December 31, 2020 2019"
                ),
                source_type="filing_page",
            ),
            EvidenceChunk(
                chunk_id="corpus:Target_10K:p11",
                doc_name="Target_10K",
                page=11,
                text="Net cash provided by operating activities 1,469,502",
                source_type="filing_page",
            ),
        ]

        result = EvidenceRetriever(chunks, first_stage_k=2).retrieve(
            "What was net cash provided by operating activities?",
            doc_name="Target_10K",
            top_k=1,
        )

        self.assertEqual(result[0].chunk_id, "corpus:Target_10K:p11")
        self.assertIn("previous page table header/scale context", result[0].text)
        self.assertIn("(In thousands)", result[0].text)
        self.assertIn("Net cash provided by operating activities 1,469,502", result[0].text)

    def test_table_row_hit_expands_to_parent_page_context(self):
        chunks = [
            EvidenceChunk(
                chunk_id="corpus:Target_10K:p53",
                doc_name="Target_10K",
                page=53,
                text=(
                    "Consolidated Statements of Earnings\n"
                    "Fiscal Year\n"
                    "2019\n2018\n2017\n"
                    "Net sales\n$ 16,865.2\n$ 15,740.4\n$ 15,619.8\n"
                    "Cost of sales\n11,108.4\n10,304.8\n10,052.0\n"
                ),
                source_type="filing_page",
            ),
            EvidenceChunk(
                chunk_id="corpus:Target_10K:row:p53:r1",
                doc_name="Target_10K",
                page=53,
                text=(
                    "TABLE ROW CHUNK:\n"
                    "Parent chunk id: corpus:Target_10K:p53\n"
                    "Page: 53\n"
                    "Statement: income statement\n"
                    "Row label: Cost of sales\n"
                    "Columns:\n"
                    "- 2019: 11108.4\n"
                    "- 2018: 10304.8\n"
                    "Source quote: Cost of sales 11,108.4 10,304.8 10,052.0"
                ),
                source_type="table_row",
            ),
        ]
        retriever = EvidenceRetriever(chunks)

        [result] = retriever._with_page_context([chunks[1]])

        self.assertEqual(result.chunk_id, "corpus:Target_10K:p53")
        self.assertEqual(result.source_type, "filing_page")
        self.assertIn("retrieved table-row match", result.text)
        self.assertIn("Row label: Cost of sales", result.text)
        self.assertIn("PARENT FILING PAGE TEXT", result.text)
        self.assertIn("Consolidated Statements of Earnings", result.text)

    def test_extracts_structured_rows_from_statement_table(self):
        chunk = EvidenceChunk(
            chunk_id="corpus:NIKE_2021_10K:p59",
            doc_name="NIKE_2021_10K",
            page=59,
            text=(
                "CONSOLIDATED STATEMENTS OF INCOME\n"
                "YEAR ENDED MAY 31,\n"
                "(In millions, except per share data)\n"
                "2021\n2020\n2019\n"
                "Revenues\n$ 44,538 $\n37,403 $\n39,117\n"
                "Cost of sales\n24,576\n21,162\n21,643\n"
                "Gross profit\n19,962\n16,241\n17,474\n"
            ),
            source_type="filing_page",
        )
        plan = RetrievalPlan(
            metric="inventory_turnover_ratio",
            facts=[
                RetrievalFact(
                    name="cost_of_goods_sold_2021",
                    aliases=["cost of sales", "cost of goods sold"],
                    period="2021",
                    statement="income statement",
                )
            ],
        )

        rows = extract_structured_rows(chunk, plan)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].required_fact, "cost_of_goods_sold_2021")
        self.assertEqual(rows[0].row_label, "Cost of sales")
        self.assertEqual(rows[0].columns["2021"], 24576.0)
        self.assertEqual(rows[0].unit_scale, "millions")
        self.assertEqual(rows[0].statement, "income statement")

    def test_structured_rows_use_total_rows_instead_of_balance_sheet_section_headers(self):
        chunk = EvidenceChunk(
            chunk_id="corpus:GENERALMILLS_2020_10K:p50",
            doc_name="GENERALMILLS_2020_10K",
            page=50,
            text=(
                "Consolidated Balance Sheets\n"
                "(In Millions, Except Par Value)\n"
                "May 31, 2020\nMay 26, 2019\n"
                "ASSETS\n"
                "Current assets:\n"
                "Cash and cash equivalents $ 1,677.8 $ 450.0\n"
                "Receivables 1,615.1 1,679.7\n"
                "Inventories 1,426.3 1,559.3\n"
                "Prepaid expenses and other current assets 402.1 497.5\n"
                "Total current assets 5,121.3 4,186.5\n"
                "LIABILITIES AND EQUITY\n"
                "Current liabilities:\n"
                "Accounts payable $ 3,247.7 $ 2,854.1\n"
                "Current portion of long-term debt 2,257.7 1,831.1\n"
                "Notes payable 561.6 1,001.9\n"
                "Total current liabilities 7,491.5 7,087.1\n"
            ),
            source_type="filing_page",
        )
        plan = RetrievalPlan(
            metric="working_capital_ratio",
            facts=[
                RetrievalFact(
                    name="total_current_assets",
                    aliases=["Total current assets", "Current assets", "Current assets total"],
                    period="2020",
                    statement="balance sheet",
                ),
                RetrievalFact(
                    name="total_current_liabilities",
                    aliases=["Total current liabilities", "Current liabilities", "Current liabilities total"],
                    period="2020",
                    statement="balance sheet",
                ),
            ],
        )

        rows = extract_structured_rows(chunk, plan)

        self.assertEqual(len(rows), 2)
        by_fact = {row.required_fact: row for row in rows}
        self.assertEqual(by_fact["total_current_assets"].row_label, "Total current assets")
        self.assertEqual(by_fact["total_current_assets"].columns["2020"], 5121.3)
        self.assertEqual(by_fact["total_current_liabilities"].row_label, "Total current liabilities")
        self.assertEqual(by_fact["total_current_liabilities"].columns["2020"], 7491.5)

    def test_attaches_structured_rows_before_raw_text(self):
        chunk = EvidenceChunk(
            chunk_id="corpus:PEPSICO_2022_10K:p94",
            doc_name="PEPSICO_2022_10K",
            page=94,
            text=(
                "Consolidated Statement of Cash Flows\n"
                "(in millions)\n"
                "202220212020\n"
                "Restructuring and impairment charges411247289\n"
                "Cash payments for restructuring charges(224)(256)(255)\n"
            ),
            source_type="filing_page",
        )
        plan = RetrievalPlan(
            metric="restructuring_costs",
            facts=[
                RetrievalFact(
                    name="restructuring_costs",
                    aliases=["restructuring and impairment charges"],
                    period="2022",
                    statement="cash flow",
                )
            ],
        )

        [result] = attach_structured_rows([chunk], plan)

        self.assertIn(STRUCTURED_ROWS_HEADER, result.text)
        self.assertIn('"columns"', result.text)
        self.assertIn('"2022": 411.0', result.text)
        self.assertIn('"unit_scale": "millions"', result.text)
        self.assertIn("RAW FILING PAGE TEXT", result.text)

    def test_structured_rows_use_document_default_scale_context(self):
        chunk = EvidenceChunk(
            chunk_id="corpus:PEPSICO_2021_10K:p82",
            doc_name="PEPSICO_2021_10K",
            page=82,
            text=(
                "20212020Change\n"
                "Net cash provided by operating activities, GAAP measure$11,616$10,613 9%\n"
                "Capital spending(4,625)(4,240)\n"
                "Free cash flow, non-GAAP measure$7,157$6,428 11%\n"
            ),
            source_type="filing_page",
        )
        plan = RetrievalPlan(
            metric="capital_expenditure",
            facts=[
                RetrievalFact(
                    name="capital_spending",
                    aliases=["capital spending"],
                    period="2021",
                    statement="cash flow",
                )
            ],
        )

        [result] = attach_structured_rows(
            [chunk],
            plan,
            doc_scale_context={
                "PEPSICO_2021_10K": "Unless otherwise noted, tabular dollars are presented in millions, except per share amounts."
            },
        )

        self.assertIn('"2021": 4625.0', result.text)
        self.assertIn('"unit_scale": "millions"', result.text)
        self.assertIn("tabular dollars are presented in millions", result.text)

    def test_has_document_checks_exact_or_partial_doc_name(self):
        chunks = [
            EvidenceChunk(
                chunk_id="corpus:Target_10K:p1",
                doc_name="Target_10K",
                page=1,
                text="Document text.",
            )
        ]
        retriever = EvidenceRetriever(chunks)

        self.assertTrue(retriever.has_document("Target_10K"))
        self.assertTrue(retriever.has_document("Target"))
        self.assertFalse(retriever.has_document("Missing_10K"))

    def test_alias_table_value_boost_ignores_accounting_policy_prose(self):
        statement_page = (
            "Consolidated Statements of Earnings\n"
            "Fiscal Year\n"
            "2019\n2018\n2017\n"
            "Net sales\n$ 16,865.2\n$ 15,740.4\n$ 15,619.8\n"
            "Cost of sales\n"
            "11,108.4\n"
            "10,304.8\n"
            "10,052.0\n"
        )
        policy_page = (
            "Shipping costs associated with distribution are recorded as cost of sales, "
            "and are recognized when the related finished product is shipped. Buildings "
            "are usually depreciated over 40 years."
        )

        self.assertTrue(_alias_has_table_values(statement_page, "Cost of sales", "2019"))
        self.assertFalse(_alias_has_table_values(policy_page, "Cost of sales", "2019"))

    def test_structured_rows_ignore_prose_mentions_of_row_aliases(self):
        chunk = EvidenceChunk(
            chunk_id="corpus:GENERALMILLS_2019_10K:p28",
            doc_name="GENERALMILLS_2019_10K",
            page=28,
            text=(
                "We recorded $1 million of restructuring initiative project-related "
                "costs in cost of sales in fiscal 2019, compared to $11 million "
                "of restructuring initiative project-related costs in cost of sales "
                "in fiscal 2018."
            ),
            source_type="filing_page",
        )
        plan = RetrievalPlan(
            metric="cash_conversion_cycle",
            facts=[
                RetrievalFact(
                    name="cogs_2019",
                    aliases=["Cost of sales", "Cost of goods sold"],
                    period="2019",
                    statement="income statement",
                )
            ],
        )

        self.assertEqual(extract_structured_rows(chunk, plan), [])

    def test_empty_corpus_rejected(self):
        with self.assertRaisesRegex(ValueError, "no_evidence_chunks"):
            EvidenceRetriever([])


if __name__ == "__main__":
    unittest.main()
