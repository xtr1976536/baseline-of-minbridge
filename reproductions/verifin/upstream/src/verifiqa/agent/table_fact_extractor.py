"""Deterministic table-based fact extraction (no LLM).

Parses pipe-separated tables from evidence_text, then looks up each role by
matching (row_label, column_year).  The caller uses these results instead of
(or before) the LLM extractor.

Outcomes per role:
  - GroundedFact        → exactly one cell matched; use it
  - None                → no cell matched; fall through to LLM extraction
  - AmbiguousTableLookup raised → multiple cells matched; caller should ABSTAIN
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from verifiqa.agent.types import GroundedFact, RoleSpec


class AmbiguousTableLookup(Exception):
    """Multiple table cells satisfy the role — caller must ABSTAIN."""

    def __init__(self, role_name: str, candidates: list["_Cell"]) -> None:
        self.role_name = role_name
        self.candidates = candidates
        vals = [f"{c.row_label!r}@{c.col_header!r}={c.raw}" for c in candidates[:4]]
        super().__init__(f"ambiguous_table_lookup:{role_name} candidates=[{', '.join(vals)}]")


@dataclass
class _Cell:
    row_label: str
    col_header: str
    raw: str
    value: float


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def lookup_fact(role: RoleSpec, evidence_text: str) -> Optional[GroundedFact]:
    """Try to find *role*'s value deterministically in *evidence_text* tables.

    Returns a GroundedFact on an unambiguous match.
    Returns None when no table cell matches (fall through to LLM extraction).
    Raises AmbiguousTableLookup when multiple cells match (caller abstains).
    """
    tables = _parse_tables(evidence_text)
    if not tables:
        return None

    all_cells: list[_Cell] = []
    for table in tables:
        all_cells.extend(_find_cells(role, table))

    # Deduplicate by (row_label, col_header, raw) — the same cell can appear in
    # multiple overlapping table blocks (e.g. individual row chunk + full_table).
    seen: set[tuple] = set()
    unique: list[_Cell] = []
    for c in all_cells:
        key = (c.row_label, c.col_header, c.raw)
        if key not in seen:
            seen.add(key)
            unique.append(c)

    if not unique:
        return None

    if len(unique) > 1:
        raise AmbiguousTableLookup(role.name, unique)

    cell = unique[0]
    source_quote = f"{cell.row_label} | {cell.col_header}: {cell.raw}"
    return GroundedFact(
        name=role.name,
        value=cell.value,
        unit="",
        source_quote=source_quote,
        column_header=cell.col_header,
        period=role.period or cell.col_header,
        row_label=cell.row_label,
    )


# ---------------------------------------------------------------------------
# Table parsing
# ---------------------------------------------------------------------------

def _parse_tables(evidence_text: str) -> list[list[list[str]]]:
    """Return a list of tables found in *evidence_text*.

    Each table is a list of rows; each row is a list of cell strings.
    Only blocks with ≥ 2 pipe-separated rows are treated as tables.
    """
    tables: list[list[list[str]]] = []
    current: list[list[str]] = []

    for raw_line in (evidence_text or "").split("\n"):
        line = raw_line.strip()
        if "|" in line:
            current.append([c.strip() for c in line.split("|")])
        else:
            if len(current) >= 2:
                tables.append(current)
            current = []

    if len(current) >= 2:
        tables.append(current)

    return tables


# ---------------------------------------------------------------------------
# Cell matching
# ---------------------------------------------------------------------------

def _find_cells(role: RoleSpec, table: list[list[str]]) -> list[_Cell]:
    """Return cells in *table* matching *role* by row label and column year."""
    if len(table) < 2:
        return []

    headers = table[0]          # First row = column headers
    data_rows = table[1:]       # Remaining rows = data

    # Find which column indices contain the role's requested year.
    col_indices = _matching_col_indices(role.period, headers)
    if not col_indices:
        return []

    # Find which data rows match the role's aliases.
    cells: list[_Cell] = []
    for row in data_rows:
        if not row:
            continue
        row_label = row[0] if row else ""
        if not _row_label_matches(role, row_label):
            continue
        for col_idx in col_indices:
            if col_idx >= len(row):
                continue
            raw = row[col_idx]
            value = _parse_number(raw)
            if value is None:
                continue
            col_header = headers[col_idx] if col_idx < len(headers) else ""
            cells.append(_Cell(
                row_label=row_label,
                col_header=col_header,
                raw=raw,
                value=value,
            ))

    return cells


# ---------------------------------------------------------------------------
# Column matching: period year → column indices
# ---------------------------------------------------------------------------

def _matching_col_indices(period: str, headers: list[str]) -> list[int]:
    """Return header indices whose year matches the year in *period*.

    Returns an empty list when *period* has no 4-digit year (caller falls
    through to LLM) or when no header contains that year.
    """
    period_years = re.findall(r"(?:19|20)\d{2}", period or "")
    if not period_years:
        return []
    target_year = period_years[-1]  # Use the last year found

    matching = []
    for i, header in enumerate(headers):
        if i == 0:
            continue  # First cell is the row-label column, never a data column
        header_years = re.findall(r"(?:19|20)\d{2}", header)
        if target_year in header_years:
            matching.append(i)
    return matching


# ---------------------------------------------------------------------------
# Row matching: role aliases → row label
# ---------------------------------------------------------------------------

_STOP = frozenset({
    "the", "a", "an", "of", "and", "or", "to", "in", "for", "from", "is",
    "are", "was", "were", "at", "by", "on", "as", "its", "with", "per",
})

# Matches only 4-digit calendar years like 2013, 1998 — NOT 2-digit or 3-digit numbers.
_CALENDAR_YEAR_RE = re.compile(r"^(?:19|20)\d{2}$")


def _content_tokens(text: str) -> set[str]:
    """Return meaningful lowercase tokens, excluding stop words and calendar years."""
    return {
        t for t in re.findall(r"[a-z0-9]+", (text or "").lower())
        if t not in _STOP and not _CALENDAR_YEAR_RE.match(t)
    }


_MAX_EXTRA_LABEL_TOKENS = 2  # How many extra tokens a label may have beyond the alias


def _row_label_matches(role: RoleSpec, row_label: str) -> bool:
    """Return True when a role alias is "contained in" *row_label* without too much extra content.

    Two conditions must both hold:
      1. All alias tokens appear in the row label (the alias is a subset of the label).
      2. The row label has at most _MAX_EXTRA_LABEL_TOKENS tokens not in the alias.
         This prevents "class a common stock" from matching "class b-2 common stock
         authorized …" (3 extra tokens: b, 2, authorized).

    When role.aliases is non-empty, only aliases are considered — the role name is
    deliberately excluded to avoid overly generic name-derived tokens (e.g.
    "development_costs_2007" → {"development","costs"}) matching unrelated rows.
    """
    if not row_label:
        return False
    label_tokens = _content_tokens(row_label)
    if not label_tokens:
        return False

    # Prefer explicit aliases; fall back to role name only when no aliases given.
    candidates: list[str] = list(role.aliases) if role.aliases else [role.name.replace("_", " ")]

    for alias in candidates:
        alias_tokens = _content_tokens(alias)
        if not alias_tokens:
            continue
        if not alias_tokens.issubset(label_tokens):
            continue
        extra = label_tokens - alias_tokens
        if len(extra) <= _MAX_EXTRA_LABEL_TOKENS:
            return True

    return False


# ---------------------------------------------------------------------------
# Number parsing
# ---------------------------------------------------------------------------

def _parse_number(raw: str) -> Optional[float]:
    """Parse a numeric value from a raw cell string, or None if not parseable.

    Handles accounting formats: "$ -2207 ( 2207 )" → -2207, "( 1234 )" → -1234.
    Strategy: extract the FIRST signed numeric token; if the raw string is purely
    parenthetical (no explicit sign), treat it as negative.
    """
    cleaned = raw.replace("$", "").replace(",", "")
    # Find the first numeric token (optional sign; handles "1.8", ".3", "2207")
    m = re.search(r"(-?\s*(?:\d[\d]*(?:\.\d+)?|\.\d+))", cleaned)
    if not m:
        return None
    token = m.group(1).replace(" ", "")
    try:
        value = float(token)
    except ValueError:
        return None
    # If the ENTIRE raw string is a bare parenthetical like "( 1234 )" or "(1234)"
    # with no leading minus, that is the standard accounting negative notation.
    if value > 0 and re.fullmatch(r"\s*\(\s*[\d,]+(?:\.\d+)?\s*\)\s*", raw.strip()):
        value = -value
    return value
