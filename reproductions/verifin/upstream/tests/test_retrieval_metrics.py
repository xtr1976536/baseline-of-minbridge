import unittest

from verifiqa.eval.retrieval_metrics import compute_retrieval_metrics
from verifiqa.types import FinanceBenchExample, RavResult


class RetrievalMetricsTests(unittest.TestCase):
    def test_reports_near_hit_and_partial_multi_page_coverage(self):
        examples = [
            FinanceBenchExample(
                financebench_id="near",
                question="q",
                evidence=[{
                    "evidence_doc_name": "ACME_10K",
                    "evidence_page_num": 59,
                }],
                doc_name="ACME_10K",
            ),
            FinanceBenchExample(
                financebench_id="multi",
                question="q",
                evidence=[
                    {"evidence_doc_name": "ADOBE_10K", "evidence_page_num": 58},
                    {"evidence_doc_name": "ADOBE_10K", "evidence_page_num": 62},
                ],
                doc_name="ADOBE_10K",
            ),
            FinanceBenchExample(
                financebench_id="missing",
                question="q",
                evidence=[{
                    "evidence_doc_name": "MISSING_10K",
                    "evidence_page_num": 10,
                }],
                doc_name="MISSING_10K",
            ),
        ]
        results = [
            RavResult(
                financebench_id="near",
                question="q",
                answer="a",
                final_status="ABSTAIN",
                first_pass_solver_status="INVALID",
                retrieved_chunk_ids=["corpus:ACME_10K:p60"],
            ),
            RavResult(
                financebench_id="multi",
                question="q",
                answer="a",
                final_status="ABSTAIN",
                first_pass_solver_status="INVALID",
                retrieved_chunk_ids=["corpus:ADOBE_10K:p58"],
            ),
            RavResult(
                financebench_id="missing",
                question="q",
                answer="a",
                final_status="ABSTAIN",
                first_pass_solver_status="INVALID",
                retrieved_chunk_ids=[],
            ),
        ]

        summary = compute_retrieval_metrics(results, examples, k=10)
        rows = {row["financebench_id"]: row for row in summary["per_question"]}

        self.assertEqual(rows["near"]["failure_mode"], "near_page_hit")
        self.assertEqual(rows["multi"]["failure_mode"], "partial_multi_page_coverage")
        self.assertEqual(rows["missing"]["failure_mode"], "missing_or_unretrieved_document")
        self.assertEqual(rows["multi"]["recall_at_k"], 0.5)
        self.assertEqual(summary["multi_page_questions"], 1)
        self.assertEqual(summary["multi_page_full_coverage_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()
