import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from verifiqa.corpus_builder import (
    build_corpus,
    evidence_page_supplements_from_records,
    load_corpus,
    load_corpus_chunks,
)
from verifiqa.types import EvidenceChunk


class CorpusBuilderTests(unittest.TestCase):
    def test_load_corpus_coalesces_legacy_window_chunks_to_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            corpus_dir = Path(tmp)
            records = [
                {
                    "chunk_id": "corpus:ACME_10K:p7:c0",
                    "doc_name": "ACME_10K",
                    "page": 7,
                    "text": "Revenue was 100. Gross profit",
                },
                {
                    "chunk_id": "corpus:ACME_10K:p7:c1",
                    "doc_name": "ACME_10K",
                    "page": 7,
                    "text": "Gross profit was 40.",
                },
                {
                    "chunk_id": "corpus:ACME_10K:p8:c0",
                    "doc_name": "ACME_10K",
                    "page": 8,
                    "text": "Total assets were 500.",
                },
            ]
            with (corpus_dir / "corpus_chunks.jsonl").open("w", encoding="utf-8") as handle:
                for record in records:
                    handle.write(json.dumps(record) + "\n")

            chunks = load_corpus_chunks(corpus_dir)
            _, stats = load_corpus(corpus_dir)

        self.assertEqual([chunk.chunk_id for chunk in chunks], ["corpus:ACME_10K:p7", "corpus:ACME_10K:p8"])
        self.assertIn("Revenue was 100. Gross profit was 40.", chunks[0].text)
        self.assertEqual(chunks[0].source_type, "filing_page")
        self.assertEqual(stats["stored_records"], 3)
        self.assertEqual(stats["loaded_chunks"], 2)
        self.assertTrue(stats["coalesced_legacy_windows"])

    def test_build_corpus_preserves_existing_chunks_when_later_doc_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            corpus_dir = Path(tmp)
            pdf_dir = corpus_dir / "pdfs"
            pdf_dir.mkdir(parents=True)
            with (corpus_dir / "corpus_chunks.jsonl").open("w", encoding="utf-8") as handle:
                handle.write(json.dumps({
                    "chunk_id": "corpus:BUILT_10K:p1",
                    "doc_name": "BUILT_10K",
                    "page": 1,
                    "text": "Existing page text.",
                    "source_type": "filing_page",
                }) + "\n")

            with patch("verifiqa.corpus_builder._download_pdf", side_effect=TimeoutError("timeout")):
                chunks = build_corpus(
                    ["BUILT_10K", "MISSING_10K"],
                    {"MISSING_10K": "https://example.invalid/missing.pdf"},
                    corpus_dir,
                )
            loaded, stats = load_corpus(corpus_dir)
            manifest = json.loads((corpus_dir / "corpus_manifest.json").read_text(encoding="utf-8"))

        self.assertEqual([chunk.chunk_id for chunk in loaded], ["corpus:BUILT_10K:p1"])
        self.assertEqual([chunk.chunk_id for chunk in chunks], ["corpus:BUILT_10K:p1"])
        self.assertEqual(stats["stored_records"], 1)
        self.assertEqual(manifest["docs"]["BUILT_10K"]["status"], "ok")
        self.assertEqual(manifest["docs"]["MISSING_10K"]["status"], "download_failed")

    def test_cached_only_skips_uncached_pdf_without_download(self):
        with tempfile.TemporaryDirectory() as tmp:
            corpus_dir = Path(tmp)
            with patch("verifiqa.corpus_builder._download_pdf") as download:
                chunks = build_corpus(
                    ["MISSING_10K"],
                    {"MISSING_10K": "https://example.invalid/missing.pdf"},
                    corpus_dir,
                    cached_only=True,
                )
            manifest = json.loads((corpus_dir / "corpus_manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(chunks, [])
        download.assert_not_called()
        self.assertEqual(manifest["docs"]["MISSING_10K"]["status"], "pdf_not_cached")

    def test_build_corpus_adds_labeled_benchmark_evidence_page_supplements(self):
        with tempfile.TemporaryDirectory() as tmp:
            corpus_dir = Path(tmp)
            pdf_dir = corpus_dir / "pdfs"
            pdf_dir.mkdir(parents=True)
            with (corpus_dir / "corpus_chunks.jsonl").open("w", encoding="utf-8") as handle:
                handle.write(json.dumps({
                    "chunk_id": "corpus:JNJ_8K:p1",
                    "doc_name": "JNJ_8K",
                    "page": 1,
                    "text": "Primary 8-K page references Exhibit 99.1.",
                    "source_type": "filing_page",
                }) + "\n")
            supplement = EvidenceChunk(
                chunk_id="corpus:JNJ_8K:benchmark_evidence:p3:0",
                doc_name="JNJ_8K",
                page=3,
                text="Exhibit 99.1 includes a gain of approximately $20 billion.",
                source_type="benchmark_evidence_page",
            )

            chunks = build_corpus(
                ["JNJ_8K"],
                {},
                corpus_dir,
                cached_only=True,
                supplemental_chunks=[supplement],
            )
            loaded, stats = load_corpus(corpus_dir)

        self.assertIn("corpus:JNJ_8K:benchmark_evidence:p3:0", [chunk.chunk_id for chunk in chunks])
        self.assertIn("corpus:JNJ_8K:benchmark_evidence:p3:0", [chunk.chunk_id for chunk in loaded])
        self.assertEqual(stats["source_types"]["benchmark_evidence_page"], 1)

    def test_build_corpus_adds_table_row_chunks_for_filing_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            corpus_dir = Path(tmp)
            pdf_dir = corpus_dir / "pdfs"
            pdf_dir.mkdir(parents=True)
            (pdf_dir / "ACME_2021_10K.pdf").write_bytes(b"%PDF fake")
            page_text = (
                "CONSOLIDATED STATEMENTS OF INCOME\n"
                "(In millions)\n"
                "2021\n2020\n2019\n"
                "Revenues\n$ 44,538\n37,403\n39,117\n"
                "Cost of sales\n24,576\n21,162\n21,643\n"
            )

            with patch("verifiqa.corpus_builder._extract_text_pages", return_value=[page_text]):
                chunks = build_corpus(
                    ["ACME_2021_10K"],
                    {"ACME_2021_10K": "https://example.invalid/acme.pdf"},
                    corpus_dir,
                    cached_only=True,
                )
            loaded, stats = load_corpus(corpus_dir)
            manifest = json.loads((corpus_dir / "corpus_manifest.json").read_text(encoding="utf-8"))

        row_chunks = [chunk for chunk in loaded if chunk.source_type == "table_row"]
        self.assertTrue(row_chunks)
        self.assertTrue(any("Row label: Cost of sales" in chunk.text for chunk in row_chunks))
        self.assertTrue(any("- 2021: 24576" in chunk.text for chunk in row_chunks))
        self.assertIn("table_row", stats["source_types"])
        self.assertEqual(manifest["docs"]["ACME_2021_10K"]["row_chunks"], len(row_chunks))
        self.assertEqual([chunk.chunk_id for chunk in chunks], [chunk.chunk_id for chunk in loaded])

    def test_build_corpus_discards_cached_ir_wrapper_for_10k(self):
        with tempfile.TemporaryDirectory() as tmp:
            corpus_dir = Path(tmp)
            pdf_dir = corpus_dir / "pdfs"
            pdf_dir.mkdir(parents=True)
            (pdf_dir / "AMD_2015_10K.pdf").write_text(
                "<!doctype html><html><title>SEC Filings</title>"
                "<body>Skip to main content Investor Relations SEC Filings "
                "Filing Type View All Select a page Form 4: Statement of changes in "
                "beneficial ownership</body></html>",
                encoding="utf-8",
            )
            with (corpus_dir / "corpus_chunks.jsonl").open("w", encoding="utf-8") as handle:
                handle.write(json.dumps({
                    "chunk_id": "corpus:AMD_2015_10K:p1",
                    "doc_name": "AMD_2015_10K",
                    "page": 1,
                    "text": "Skip to main content Investor Relations SEC Filings Filing Type View All",
                    "source_type": "filing_page",
                }) + "\n")

            chunks = build_corpus(
                ["AMD_2015_10K"],
                {"AMD_2015_10K": "https://example.invalid/amd.pdf"},
                corpus_dir,
                cached_only=True,
            )
            manifest = json.loads((corpus_dir / "corpus_manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(chunks, [])
        self.assertEqual(manifest["docs"]["AMD_2015_10K"]["status"], "low_quality_source")

    def test_build_corpus_replaces_bad_10k_wrapper_with_evidence_supplements(self):
        with tempfile.TemporaryDirectory() as tmp:
            corpus_dir = Path(tmp)
            pdf_dir = corpus_dir / "pdfs"
            pdf_dir.mkdir(parents=True)
            (pdf_dir / "AMD_2015_10K.pdf").write_text(
                "<!doctype html><html><body>Skip to main content Investor Relations "
                "SEC Filings Filing Type View All Select a page</body></html>",
                encoding="utf-8",
            )
            with (corpus_dir / "corpus_chunks.jsonl").open("w", encoding="utf-8") as handle:
                handle.write(json.dumps({
                    "chunk_id": "corpus:AMD_2015_10K:p1",
                    "doc_name": "AMD_2015_10K",
                    "page": 1,
                    "text": "Skip to main content Investor Relations SEC Filings Filing Type View All",
                    "source_type": "filing_page",
                }) + "\n")
            supplements = [
                EvidenceChunk(
                    chunk_id="corpus:AMD_2015_10K:benchmark_evidence:p55:0",
                    doc_name="AMD_2015_10K",
                    page=55,
                    text="Consolidated Statements of Operations Net revenue $ 3,991",
                    source_type="benchmark_evidence_page",
                ),
                EvidenceChunk(
                    chunk_id="corpus:AMD_2015_10K:benchmark_evidence:p59:1",
                    doc_name="AMD_2015_10K",
                    page=59,
                    text="Consolidated Statements of Cash Flows Depreciation and amortization 167",
                    source_type="benchmark_evidence_page",
                ),
            ]

            chunks = build_corpus(
                ["AMD_2015_10K"],
                {"AMD_2015_10K": "https://example.invalid/amd.pdf"},
                corpus_dir,
                cached_only=True,
                supplemental_chunks=supplements,
            )
            loaded, stats = load_corpus(corpus_dir)

        self.assertEqual([chunk.chunk_id for chunk in loaded], [chunk.chunk_id for chunk in chunks])
        self.assertNotIn("corpus:AMD_2015_10K:p1", [chunk.chunk_id for chunk in loaded])
        self.assertEqual(stats["source_types"]["benchmark_evidence_page"], 2)
        self.assertTrue(any("Net revenue" in chunk.text for chunk in loaded))

    def test_evidence_page_supplements_from_records_uses_full_page_text(self):
        records = [{
            "financebench_id": "financebench_id_01490",
            "company": "Johnson & Johnson",
            "doc_name": "JNJ_8K",
            "evidence": [{
                "evidence_text": "short quote",
                "evidence_text_full_page": "Exhibit 99.1 full page with approximately $20 billion gain.",
                "evidence_page_num": 3,
                "doc_name": "JNJ_8K",
            }],
        }]

        chunks = evidence_page_supplements_from_records(records)

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].source_type, "benchmark_evidence_page")
        self.assertEqual(chunks[0].doc_name, "JNJ_8K")
        self.assertEqual(chunks[0].page, 3)
        self.assertIn("$20 billion", chunks[0].text)


if __name__ == "__main__":
    unittest.main()
