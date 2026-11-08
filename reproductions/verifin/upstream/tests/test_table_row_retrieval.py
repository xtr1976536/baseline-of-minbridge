"""Tests for table-row pre-indexing and retrieval fixes.

The motivating bug: AES 2022 ROA was verified wrong because
  - p180 (Notes AOCI table) outscored p131 (Consolidated Statements of Operations)
    due to false-positive heading bonuses on notes pages.
  - _has_structured_row_value only worked on filing_page chunks, so table_row
    chunks never got the +10 structured-row bonus.
  - _statement_for_chunk used singular "statement of operations" but PDFs write
    the plural "statements of operations", so every row chunk got statement=''.

All three fixes are tested below with minimal synthetic chunks — no disk corpus
or embedding model required.
"""
from __future__ import annotations

import re
import unittest

from verifiqa.retrieval.evidence_retriever import (
    _has_structured_row_value,
    _is_notes_continuation_chunk,
    _lexical_score,
    _table_row_chunk_matches,
)
from verifiqa.retrieval.table_rows import (
    _is_notes_continuation_page,
    _statement_for_chunk,
    table_row_chunks_from_pages,
)
from verifiqa.types import EvidenceChunk


# ---------------------------------------------------------------------------
# Minimal synthetic data
# ---------------------------------------------------------------------------

_P131_TEXT = """\
129
Consolidated Statements of Operations
Years ended December 31, 2022, 2021, and 2020
2022 2021 2020
(in millions, except per share amounts)
Revenue:
Regulated $ 3,538 $ 2,868 $ 2,661
Non-Regulated 9,079 8,273 6,999
Total revenue 12,617 11,141 9,660
Cost of sales:
Regulated (3,162) (2,448) (2,235)
Non-Regulated (6,907) (5,982) (4,732)
Total cost of sales (10,069) (8,430) (6,967)
Operating margin 2,548 2,711 2,693
Interest expense (1,117) (911) (1,038)
NET INCOME (LOSS) (505) (951) 152
NET INCOME (LOSS) ATTRIBUTABLE TO THE AES CORPORATION $ (546) $ (409) $ 46
"""

_P180_TEXT = """\
177 | Notes to Consolidated Financial Statements—(Continued) | December 31, 2022, 2021 and 2020
Reclassifications out of AOCL are presented in the following table. Amounts for the periods
indicated are in millions and those in parenthesis indicate debits to the Consolidated
Statements of Operations.
Details About AOCL Components  Affected Line Item in the Consolidated Statements of Operations
                                2022     2021     2020
Foreign currency translation adjustments, net
  Gain on disposal                        $ —    $ (3)   $ (192)
  Net income attributable to The AES Corporation $ —  $ (3)  $ (192)
"""

_P130_TEXT = """\
128
Consolidated Balance Sheets
December 31, 2022 and 2021
2022  2021
(in millions, except share and per share data)
TOTAL ASSETS $ 38,363 $ 32,963
"""


def _make_page(chunk_id: str, text: str) -> EvidenceChunk:
    page = int(re.search(r":p(\d+)$", chunk_id).group(1))
    return EvidenceChunk(
        chunk_id=chunk_id, doc_name="AES_2022_10K",
        page=page, text=text, source_type="filing_page",
    )


# ---------------------------------------------------------------------------
# Fix 1: _statement_for_chunk — plurals
# ---------------------------------------------------------------------------

class TestStatementForChunk(unittest.TestCase):

    def test_recognises_plural_statements_of_operations(self):
        """p131 should be tagged 'income statement' despite plural heading."""
        self.assertEqual(_statement_for_chunk(_P131_TEXT), "income statement")

    def test_notes_page_returns_empty_despite_column_reference(self):
        """p180 references 'Statements of Operations' as a column header; result must be empty."""
        self.assertEqual(_statement_for_chunk(_P180_TEXT), "")

    def test_balance_sheet(self):
        self.assertEqual(_statement_for_chunk(_P130_TEXT), "balance sheet")


# ---------------------------------------------------------------------------
# Fix 2: notes-page detection
# ---------------------------------------------------------------------------

class TestNotesPageDetection(unittest.TestCase):

    def test_primary_statement_is_not_notes(self):
        self.assertFalse(_is_notes_continuation_page(_P131_TEXT))
        self.assertFalse(_is_notes_continuation_chunk(_P131_TEXT))

    def test_notes_continuation_is_detected(self):
        self.assertTrue(_is_notes_continuation_page(_P180_TEXT))
        self.assertTrue(_is_notes_continuation_chunk(_P180_TEXT))

    def test_balance_sheet_is_not_notes(self):
        self.assertFalse(_is_notes_continuation_chunk(_P130_TEXT))


# ---------------------------------------------------------------------------
# Fix 3: _has_structured_row_value for pre-indexed table_row chunks
# ---------------------------------------------------------------------------

class TestHasStructuredRowValue(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        page_chunks = [_make_page("corpus:AES_2022_10K:p131", _P131_TEXT),
                       _make_page("corpus:AES_2022_10K:p180", _P180_TEXT)]
        row_chunks = table_row_chunks_from_pages(page_chunks)
        cls.rows = {rc.chunk_id: rc for rc in row_chunks}

    def _row(self, parent_page: int) -> EvidenceChunk | None:
        """Return the first net-income table_row chunk from the given page."""
        for cid, chunk in self.rows.items():
            if f":p{parent_page}:" in cid and "net income" in chunk.text.lower():
                return chunk
        return None

    def test_p131_net_income_row_matches(self):
        row = self._row(131)
        self.assertIsNotNone(row, "No net-income row found on p131")
        result = _has_structured_row_value(
            row,
            aliases=["net income", "net earnings", "net loss"],
            period="2022",
            statement="income statement",
        )
        self.assertTrue(result)

    def test_p180_aoci_row_does_not_match_due_to_missing_unit_scale(self):
        row = self._row(180)
        self.assertIsNotNone(row, "No net-income-like row found on p180")
        result = _has_structured_row_value(
            row,
            aliases=["net income", "net earnings", "net loss"],
            period="2022",
            statement="income statement",
        )
        self.assertFalse(result)

    def test_table_row_chunk_matches_helper_directly(self):
        # Synthetic TABLE ROW CHUNK text as it appears in the corpus
        good = (
            "TABLE ROW CHUNK:\n"
            "Parent chunk id: corpus:AES_2022_10K:p131\n"
            "Document: corpus:AES_2022_10K:p131\n"
            "Page: 131\n"
            "Row label: NET INCOME LOSS\n"
            "Columns:\n"
            "- 2022: 505\n"
            "- 2021: 951\n"
            "- 2020: 152\n"
            "Unit scale: millions\n"
            "Unit scale quote: (in millions, except per share amounts)\n"
            "Source quote: NET INCOME (LOSS) (505) (951) 152"
        )
        bad = (
            "TABLE ROW CHUNK:\n"
            "Parent chunk id: corpus:AES_2022_10K:p180\n"
            "Row label: Net income attributable to The AES Corporation\n"
            "Columns:\n"
            "- 2022: 3\n"
            "- 2021: 192\n"
            # No 'Unit scale:' line — discriminator
            "Source quote: Net income attributable to The AES Corporation $ — $ (3) $ (192)"
        )
        aliases = ["net income", "net earnings", "net loss"]
        self.assertTrue(_table_row_chunk_matches(good, aliases=aliases, period="2022"))
        self.assertFalse(_table_row_chunk_matches(bad, aliases=aliases, period="2022"))


# ---------------------------------------------------------------------------
# Combined: lexical score ordering
# ---------------------------------------------------------------------------

class TestLexicalScoreOrdering(unittest.TestCase):
    """p131 (IS page) must outrank p180 (notes page) after the notes-page penalty."""

    @classmethod
    def setUpClass(cls):
        page_chunks = [_make_page("corpus:AES_2022_10K:p131", _P131_TEXT),
                       _make_page("corpus:AES_2022_10K:p180", _P180_TEXT)]
        row_chunks = table_row_chunks_from_pages(page_chunks)
        all_chunks = page_chunks + row_chunks
        cls.chunks = {c.chunk_id: c for c in all_chunks}

    def _score(self, chunk_id: str) -> float:
        return _lexical_score(
            "AES net income 2022 consolidated statement of income",
            self.chunks[chunk_id],
            aliases=["net income", "net earnings", "net loss", "profit for the year"],
            period="2022",
            statement="income statement",
        )

    def _net_income_row(self, page: int) -> str:
        for cid, chunk in self.chunks.items():
            if f":p{page}:" in cid and chunk.source_type == "table_row" \
                    and "net income" in chunk.text.lower():
                return cid
        return ""

    def test_p131_outranks_p180_page(self):
        s131 = self._score("corpus:AES_2022_10K:p131")
        s180 = self._score("corpus:AES_2022_10K:p180")
        self.assertGreater(s131, s180,
            f"p131 ({s131:.2f}) should outrank p180 ({s180:.2f}) after notes-page penalty")

    def test_p131_page_beats_p180_by_at_least_five_points(self):
        gap = self._score("corpus:AES_2022_10K:p131") - self._score("corpus:AES_2022_10K:p180")
        self.assertGreaterEqual(gap, 5.0,
            f"Gap should be ≥ 5 (notes-page penalty is 8). Got {gap:.2f}")

    def test_p131_row_chunk_outranks_p180_row_chunk(self):
        p131_row = self._net_income_row(131)
        p180_row = self._net_income_row(180)
        self.assertTrue(p131_row, "No net-income row chunk found for p131")
        self.assertTrue(p180_row, "No net-income row chunk found for p180")
        s131r = self._score(p131_row)
        s180r = self._score(p180_row)
        self.assertGreater(s131r, s180r,
            f"p131 row ({s131r:.2f}) should outrank p180 row ({s180r:.2f})")

    def test_notes_page_penalty_fires_only_for_statement_query(self):
        """Without a statement target, notes-page penalty must NOT apply."""
        p180 = self.chunks["corpus:AES_2022_10K:p180"]
        score_with_stmt    = _lexical_score("net income", p180, aliases=["net income"],
                                            period="2022", statement="income statement")
        score_without_stmt = _lexical_score("net income", p180, aliases=["net income"],
                                            period="2022", statement="")
        self.assertLess(score_with_stmt, score_without_stmt,
            "Penalty should only fire when statement is specified")


if __name__ == "__main__":
    unittest.main()
