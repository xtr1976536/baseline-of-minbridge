"""Operation-definition registry for deployment-realistic FinQA verification.

FinanceBench draws formula authority from the metric-policy registry; FinQA's gold
`program` is a per-question dataset annotation (an oracle). With the program disabled
(``--no-finqa-program``) the named-metric registry rarely covers FinQA's free-form
question-imposed arithmetic, so the verifier abstains.

This module supplies the legitimate, instance-independent alternative: the *definitions
of the standard financial-analysis operations* FinQA questions use. These are named,
citable techniques — not the gold derivation:

  * percentage change / growth        -> period-over-period growth rate
  * proportion / percent-of-total     -> common-size (vertical) analysis
  * absolute period change            -> arithmetic difference

The registry supplies only the FORM (e.g. ``part / base * 100``); the LLM still
classifies the operation and selects + grounds the operands, and the verifier checks
the grounded operands reproduce the canonical form. Operand ROLES are bound from the
question grammar and the document's own row labels (e.g. the "total" row), never from
the answer and never from the operand values.

Soundness discipline (uniform across families): bind roles only when they are
*unambiguous*; otherwise return None (abstain) rather than guess. A parse ambiguity
costs coverage, never soundness.
"""
from __future__ import annotations

import re
from typing import Any

from verifiqa.types import VerificationIR


# -- citations ---------------------------------------------------------------
# Same source class the metric-policy registry already cites (CFA Institute +
# standard financial-statement-analysis texts), so the operation registry's
# provenance matches the authority a reviewer already accepts for FinanceBench.
_CFA_FAT = {
    "title": "CFA Institute - Financial Analysis Techniques",
    "url": "https://www.cfainstitute.org/en/membership/professional-development/refresher-readings/financial-analysis-techniques",
}
_FSA_TEXT = {
    "title": "White, Sondhi & Fried, The Analysis and Use of Financial Statements (common-size / ratio analysis)",
}


_OPERATIONS: dict[str, dict[str, Any]] = {
    "percent_change": {
        "technique": "period-over-period growth rate",
        "note": "Percentage change = (later period - earlier period) / earlier period * 100.",
        "source_refs": [_CFA_FAT],
    },
    "period_change": {
        "technique": "arithmetic period difference",
        "note": "Period change = later-period value - earlier-period value.",
        "source_refs": [_CFA_FAT],
    },
    "proportion": {
        "technique": "common-size (vertical) analysis",
        "note": "Common-size analysis: a component expressed as a percentage of its base total (part / base * 100).",
        "source_refs": [_CFA_FAT, _FSA_TEXT],
    },
    "average": {
        "technique": "arithmetic mean",
        "note": "Average = sum of observations / count of observations.",
        "source_refs": [_CFA_FAT],
    },
    "generic_ratio": {
        "technique": "ratio of two quantities",
        "note": "Ratio = numerator / denominator.",
        "source_refs": [_CFA_FAT],
    },
}


# -- operation classification ------------------------------------------------
# Order matters — more specific patterns checked before broader ones.
_PERCENT_CHANGE = re.compile(
    r"percent(?:age)?\s+(?:change|increase|decrease|growth|difference)"
    r"|%\s*change"
    r"|change\b[^.?]*\bpercent"
    r"|growth\s+rate"
    r"|rate\s+of\s+(?:growth|change|increase|decrease)",
    re.IGNORECASE,
)
_ROI = re.compile(
    r"\broi\b"
    r"|rate\s+of\s+return\s+of\s+an?\s+investment"
    r"|(?:percentage\s+)?cumulative\s+(?:total\s+)?return"
    r"|\bfive[- ]year\s+total\s+return\b"
    r"|\btotal\s+return\s+(?:percentage|percent|on)\b",
    re.IGNORECASE,
)
_PROPORTION = re.compile(
    r"\bwhat\s+(?:percent(?:age)?|portion|proportion|fraction|share)\b"
    r"|\b(?:percent(?:age)?|portion|proportion|fraction|share)\s+of\b"
    r"|\bas\s+a\s+(?:percent(?:age)?|proportion|fraction|share)\s+of\b",
    re.IGNORECASE,
)
_AVERAGE = re.compile(
    r"\bwhat\s+(?:is|was)\s+the\s+average\b"
    r"|\bwhat\s+was\s+the\s+average\b"
    r"|\baverage\s+(?:of|for|from|amount|number|price|value|payment|percentage|weighted)\b"
    r"|\bavg\b",
    re.IGNORECASE,
)
# "average X per Y" is a per-unit rate (ratio), not a multi-period mean.
_AVERAGE_PER = re.compile(r"\baverage\b.{0,40}\bper\b", re.IGNORECASE)
_GENERIC_RATIO = re.compile(
    r"\bwhat\s+(?:is|was)\s+the\s+ratio\s+of\b"
    r"|\bratio\s+of\s+the\b",
    re.IGNORECASE,
)
_ABSOLUTE_CHANGE = re.compile(
    r"\b(?:change|increase|decrease|difference|grew|grow|growth|rose|fell|"
    r"decline|declined|reduction|gain)\b",
    re.IGNORECASE,
)
_DECLINE_MAGNITUDE = re.compile(
    r"\b(?:decrease|decline|declined|drop|dropped|fell|fall|reduction|lower)\b",
    re.IGNORECASE,
)


def classify_operation(question: str, metric: str = "") -> str | None:
    """Return the generic operation class implied by the question, or None.

    Order matters: more specific patterns are checked before broader ones.
    ROI is checked before proportion because cumulative return questions contain
    percentage language. Average and generic_ratio are checked before absolute
    change to avoid false matches on "average increase" etc.
    """
    text = f"{question or ''} {metric or ''}"
    if _PERCENT_CHANGE.search(text):
        return "percent_change"
    if _ROI.search(text):
        return "percent_change"  # same formula: (end - start) / start * 100
    if _PROPORTION.search(text):
        return "proportion"
    if _AVERAGE.search(text) and not _AVERAGE_PER.search(text):
        return "average"
    if _GENERIC_RATIO.search(text):
        return "generic_ratio"
    if _ABSOLUTE_CHANGE.search(text):
        return "period_change"
    return None


def resolve_generic_operation(ir: VerificationIR, question: str) -> dict[str, Any] | None:
    """Authorize a FinQA arithmetic claim against a cited operation definition.

    Returns a dict with the substituted ``formula`` (over this IR's fact names), the
    ``variables``, the ``computed_value``, the ``technique``/``source_note`` and
    ``source_refs`` (citations) — or None to abstain.
    """
    operation = classify_operation(question, ir.metric)
    if operation == "proportion":
        return _resolve_proportion(ir, question)
    if operation in ("percent_change", "period_change"):
        return _resolve_change(ir, question, operation)
    if operation == "average":
        return _resolve_average(ir, question)
    if operation == "generic_ratio":
        return _resolve_generic_ratio(ir, question)
    return None


# -- percentage / absolute change (period-ordered operands) ------------------

def _resolve_change(ir: VerificationIR, question: str, operation: str) -> dict[str, Any] | None:
    ordered = _facts_ordered_by_period(ir)
    if ordered is None:
        return None
    start_name, end_name = ordered
    try:
        start_value = float(ir.facts[start_name].value)
        end_value = float(ir.facts[end_name].value)
    except (KeyError, TypeError, ValueError):
        return None

    if operation == "percent_change":
        if start_value == 0.0:
            return None
        formula = f"({end_name} - {start_name}) / {start_name} * 100"
        computed = (end_value - start_value) / start_value * 100.0
    elif _DECLINE_MAGNITUDE.search(question or ""):
        formula = f"{start_name} - {end_name}"
        computed = start_value - end_value
    else:
        formula = f"{end_name} - {start_name}"
        computed = end_value - start_value

    return _result(operation, formula, sorted({start_name, end_name}), computed,
                   start=start_name, end=end_name)


def _facts_ordered_by_period(ir: VerificationIR) -> tuple[str, str] | None:
    """(earlier_fact, later_fact) iff exactly two facts each carry a distinct
    4-digit period in their name; else None (abstain)."""
    facts = list(ir.facts.keys())
    if len(facts) != 2:
        return None
    keyed: list[tuple[int, str]] = []
    for name in facts:
        years = [int(y) for y in re.findall(r"(?:19|20)\d{2}", name)]
        if not years:
            return None
        keyed.append((years[-1], name))
    if keyed[0][0] == keyed[1][0]:
        return None
    keyed.sort(key=lambda item: item[0])
    return keyed[0][1], keyed[1][1]


# -- average (arithmetic mean) ----------------------------------------------

def _resolve_average(ir: VerificationIR, question: str) -> dict[str, Any] | None:
    items = list(ir.facts.items())
    if len(items) < 2:
        return None

    expected_years = _year_span_from_question(question)
    if expected_years:
        keyed: list[tuple[int, str]] = []
        for name, fact in items:
            years = _fact_years(name, fact)
            if len(years) != 1:
                return None
            keyed.append((years[0], name))
        if sorted(year for year, _name in keyed) != expected_years:
            return None
        keyed.sort(key=lambda item: item[0])
        names = [name for _year, name in keyed]
    else:
        names = [name for name, _fact in items]

    try:
        values = [float(ir.facts[name].value) for name in names]
    except (KeyError, TypeError, ValueError):
        return None
    count = len(values)
    if count == 0:
        return None

    formula = f"({' + '.join(names)}) / {count}"
    computed = sum(values) / count
    return _result("average", formula, names, computed, count=str(count))


def _year_span_from_question(question: str) -> list[int]:
    years = [int(year) for year in re.findall(r"\b(?:19|20)\d{2}\b", question or "")]
    if len(years) < 2:
        return []
    first, last = years[0], years[-1]
    if first > last or last - first > 20:
        return []
    return list(range(first, last + 1))


def _fact_years(name: str, fact: Any) -> list[int]:
    text = " ".join(
        str(value or "")
        for value in (name, getattr(fact, "period", ""), getattr(fact, "row_label", ""))
    )
    return [int(year) for year in re.findall(r"(?:19|20)\d{2}", text)]


# -- explicit ratio (question grammar binds numerator and denominator) -------

def _resolve_generic_ratio(ir: VerificationIR, question: str) -> dict[str, Any] | None:
    items = list(ir.facts.items())
    if len(items) != 2:
        return None

    phrases = _ratio_phrases(question)
    if phrases is None:
        return None
    numerator_phrase, denominator_phrase = phrases
    numerator = _best_fact_for_phrase(items, numerator_phrase)
    denominator = _best_fact_for_phrase(items, denominator_phrase)
    if numerator is None or denominator is None or numerator == denominator:
        return None

    try:
        numerator_value = float(ir.facts[numerator].value)
        denominator_value = float(ir.facts[denominator].value)
    except (KeyError, TypeError, ValueError):
        return None
    if denominator_value == 0.0:
        return None

    formula = f"{numerator} / {denominator}"
    computed = numerator_value / denominator_value
    return _result("generic_ratio", formula, sorted({numerator, denominator}), computed,
                   numerator=numerator, denominator=denominator)


def _ratio_phrases(question: str) -> tuple[str, str] | None:
    q = (question or "").lower()
    match = re.search(
        r"\bratio\s+of\s+(?:the\s+)?(.{1,120}?)\s+"
        r"(?:to|over|divided\s+by)\s+(?:the\s+)?(.{1,120}?)(?:[?.]|$)",
        q,
    )
    if not match:
        return None
    return match.group(1), match.group(2)


def _best_fact_for_phrase(items: list[tuple[str, Any]], phrase: str) -> str | None:
    phrase_tokens = _content_tokens(phrase)
    if not phrase_tokens:
        return None
    best_name, best_score, tie = None, 0, False
    for name, fact in items:
        tokens = _content_tokens(f"{getattr(fact, 'row_label', '') or ''} {name}")
        score = len(tokens & phrase_tokens)
        if score > best_score:
            best_name, best_score, tie = name, score, False
        elif score == best_score and score > 0:
            tie = True
    if best_score == 0 or tie:
        return None
    return best_name


# -- proportion / percent-of-total (common-size analysis) --------------------

def _resolve_proportion(ir: VerificationIR, question: str) -> dict[str, Any] | None:
    """Authorize a percent-of-total claim as part / base * 100.

    Requires exactly two facts and an *unambiguous* base (denominator), bound from
    the document's own "total" row label and/or the question grammar (the noun after
    "of"). Abstains on ambiguity, never guesses; never inspects the operand values.
    """
    items = list(ir.facts.items())
    if len(items) != 2:
        return None
    base_name = _select_base(items, question)
    if base_name is None:
        return None
    part_name = next(n for n, _ in items if n != base_name)
    try:
        base_value = float(ir.facts[base_name].value)
        part_value = float(ir.facts[part_name].value)
    except (KeyError, TypeError, ValueError):
        return None
    if base_value == 0.0:
        return None

    formula = f"{part_name} / {base_name} * 100"
    computed = part_value / base_value * 100.0
    return _result("proportion", formula, sorted({part_name, base_name}), computed,
                   part=part_name, base=base_name)


def _select_base(items: list[tuple[str, Any]], question: str) -> str | None:
    """Identify the base (denominator) fact value-blind, or None if ambiguous.

    Two independent signals; they must not contradict:
      1. document row-label carries a total/aggregate marker (the base of a
         common-size ratio is the total);
      2. question grammar: the fact named immediately after "of".
    """
    marked = [name for name, fact in items if _has_total_marker(fact)]
    if len(marked) >= 2:
        return None  # two "total"-labeled facts -> genuinely ambiguous -> abstain
    label_base = marked[0] if marked else None
    grammar_base = _base_by_grammar(items, question)

    if label_base and grammar_base:
        return label_base if label_base == grammar_base else None  # disagree -> abstain
    return label_base or grammar_base


_TOTAL_MARKERS = ("total", "aggregate", "overall", "consolidated", "all ")


def _has_total_marker(fact: Any) -> bool:
    text = " ".join(
        str(value or "")
        for value in (getattr(fact, "row_label", ""), getattr(fact, "name", ""),
                      getattr(fact, "source_quote", ""))
    ).lower()
    return any(marker in text for marker in _TOTAL_MARKERS)


_STOP = frozenset({
    "the", "a", "an", "of", "and", "or", "to", "in", "for", "from", "is", "are",
    "was", "were", "total", "percent", "percentage", "what", "comes", "come",
    "that", "which", "due", "as", "by", "on", "s",
})


def _base_by_grammar(items: list[tuple[str, Any]], question: str) -> str | None:
    """The fact whose label tokens appear in the phrase immediately after "of"."""
    q = (question or "").lower()
    match = re.search(
        r"\bof\s+(?:the\s+)?(?:total\s+)?(.{0,70}?)"
        r"(?:\s+(?:is|are|was|were|comes?|that|which|due|attributable|represent|account)\b|[,?]|$)",
        q,
    )
    if not match:
        return None
    phrase_tokens = {t for t in re.findall(r"[a-z0-9]+", match.group(1)) if t not in _STOP}
    if not phrase_tokens:
        return None
    best_name, best_score, tie = None, 0, False
    for name, fact in items:
        tokens = _content_tokens(f"{getattr(fact, 'row_label', '') or ''} {name}")
        score = len(tokens & phrase_tokens)
        if score > best_score:
            best_name, best_score, tie = name, score, False
        elif score == best_score and score > 0:
            tie = True
    if best_score == 0 or tie:
        return None
    return best_name


def _content_tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", (text or "").lower())
            if t not in _STOP and not re.fullmatch(r"(?:19|20)?\d{2,4}", t)}


# -- result helper -----------------------------------------------------------

def _result(operation: str, formula: str, variables: list[str], computed: float,
            **roles: str) -> dict[str, Any]:
    spec = _OPERATIONS[operation]
    out = {
        "status": "applied",
        "operation": operation,
        "technique": spec["technique"],
        "formula": formula,
        "variables": variables,
        "computed_value": computed,
        "source_note": spec["note"],
        "source_refs": list(spec["source_refs"]),
    }
    out.update(roles)
    return out
