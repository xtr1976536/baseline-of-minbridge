"""Phase B: extract one GroundedFact per role from full evidence text.

All roles are extracted in parallel via ThreadPoolExecutor. Each call is a
single focused LLM prompt — one role, one JSON response.
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from verifiqa.agent.types import ClaimSpec, GroundedFact, RoleSpec
from verifiqa.agent.utils import extract_json
from verifiqa.generation.llm_client import ChatMessage


_PROMPT = """\
Extract the value for ONE financial line item from the evidence text below.

Role: {role_name}
Acceptable row labels (any of these match): {aliases}
Time period needed: {period}
Formula context: this variable appears in  {formula}

Return JSON only — no markdown:
{{
  "value": <number — canonical USD millions for monetary, as-reported for ratios/percents/counts>,
  "unit": "<USD millions|percent|ratio|count|other>",
  "source_quote": "<verbatim excerpt from the evidence that contains the number>",
  "period": "<period of this value, e.g. 2022 or Q3 2023>",
  "row_label": "<exact row label from the table or text>"
}}

If the value is not present in the evidence return:
{{"found": false, "reason": "<brief reason>"}}

Rules:
- value: use the number exactly as it appears in the evidence. Do NOT convert units.
  - If a TABLE HEADER or caption says "amounts in millions" or "in thousands", apply that scale factor to the cell values.
  - If a ROW LABEL says "volume (billions)" or "total (billions)", that describes what the value represents — use the number as printed, do not multiply.
- unit: report what the evidence states — "USD millions", "USD billions", "percent", "count", "other".
- value must be a plain number — no units, no currency symbols, no commas.
- source_quote must be copied verbatim from the evidence and must contain the numeric value.
- Match the column or period closest to the requested time period.
- Do not invent values not present in the evidence.

Evidence:
{evidence_text}
"""


_FEEDBACK_PROMPT = """\
Re-extract ONE financial line item from the evidence text below.

The verifier found that the current extracted facts make the formula disagree with
the claimed answer. Your job is only to check whether THIS role used the wrong
row, period, sign, or as-reported unit.

Role: {role_name}
Acceptable row labels (any of these match): {aliases}
Time period needed: {period}
Formula context: this variable appears in {formula}

Claimed answer value: {claimed_value}
Current formula result from extracted facts: {computed_value}
Allowed tolerance: {tolerance}
UNSAT core: {unsat_core}

Current extracted facts:
{current_facts}

Previous extraction for this role:
{previous_fact}

Attempt: {attempt}

Return JSON only, no markdown:
{{
  "value": <number - canonical USD millions for monetary, as-reported for ratios/percents/counts>,
  "unit": "<USD millions|percent|ratio|count|other>",
  "source_quote": "<verbatim excerpt from the evidence that contains the number>",
  "period": "<period of this value, e.g. 2022 or Q3 2023>",
  "row_label": "<exact row label from the table or text>"
}}

If there is no better evidence-grounded value for this role, return:
{{"found": false, "reason": "no_better_alternative"}}

Rules:
- Use the mismatch only as a diagnostic signal. Do NOT solve backwards from the
  claimed value, and do NOT choose a number merely because it would make the
  formula pass.
- Prefer an alternate row/column only when it better matches the role name,
  aliases, requested period, and formula context.
- Do not reuse the previous extraction unless it is truly the only grounded
  value; in that case return found=false.
- value must be copied from evidence semantics, not inferred.
- Do not convert units. If a table header or caption says amounts are in
  millions or thousands, report that unit. If a row label says "(billions)",
  report the printed value and unit from that row.
- Do not change sign unless the evidence itself presents the value as negative
  or in parentheses.
- source_quote must be copied verbatim from the evidence and must contain the
  numeric value.

Evidence:
{evidence_text}
"""


def extract_facts_parallel(
    claim_spec: ClaimSpec,
    evidence_text: str,
    llm_client,
    max_workers: int = 4,
) -> dict[str, GroundedFact | None]:
    """Extract all roles concurrently. Returns {role_name: GroundedFact | None}."""
    if not claim_spec.roles:
        return {}
    results: dict[str, GroundedFact | None] = {}
    workers = min(len(claim_spec.roles), max_workers)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(extract_fact, role, evidence_text, claim_spec.formula, llm_client): role.name
            for role in claim_spec.roles
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                results[name] = future.result()
            except Exception:
                results[name] = None
    return results


def extract_fact(
    role: RoleSpec,
    evidence_text: str,
    formula: str,
    llm_client,
) -> GroundedFact | None:
    """Extract a single fact. Returns None if not found in evidence."""
    prompt = _PROMPT.format(
        role_name=role.name,
        aliases=", ".join(role.aliases) if role.aliases else role.name,
        period=role.period or "most recent available",
        formula=formula or "unknown",
        evidence_text=evidence_text,
    )
    raw = llm_client.chat(
        [ChatMessage(role="user", content=prompt)],
        temperature=0.0,
        stage="fact_extraction",
    ).strip()

    data = json.loads(extract_json(raw))
    if data.get("found") is False or "value" not in data:
        return None

    try:
        value = float(str(data["value"]).replace(",", "").replace("$", "").strip())
    except (ValueError, TypeError):
        return None

    return GroundedFact(
        name=role.name,
        value=value,
        unit=str(data.get("unit", "")).strip(),
        source_quote=str(data.get("source_quote", "")).strip(),
        period=str(data.get("period", role.period)).strip(),
        row_label=str(data.get("row_label", "")).strip(),
        concept=getattr(role, "concept", "") or "",
    )


def extract_fact_with_feedback(
    role: RoleSpec,
    evidence_text: str,
    formula: str,
    llm_client,
    *,
    claimed_value: float,
    computed_value: float | None,
    tolerance: float,
    current_facts: dict[str, GroundedFact],
    previous_fact: GroundedFact | None,
    attempt: int,
    unsat_core: list[str] | None = None,
) -> GroundedFact | None:
    """Re-extract a fact with verifier feedback after an UNSAT result.

    The feedback prompt is intentionally separate from the first-pass extractor:
    first pass remains a plain evidence lookup; retry gets the computed mismatch
    and previous extraction so the model can search for an alternate row/period
    instead of repeating the same answer.
    """
    prompt = _FEEDBACK_PROMPT.format(
        role_name=role.name,
        aliases=", ".join(role.aliases) if role.aliases else role.name,
        period=role.period or "most recent available",
        formula=formula or "unknown",
        claimed_value=claimed_value,
        computed_value=computed_value if computed_value is not None else "unavailable",
        tolerance=tolerance,
        unsat_core=" ".join(unsat_core or []) if unsat_core else "(none)",
        current_facts=_format_current_facts(current_facts),
        previous_fact=_format_previous_fact(previous_fact),
        attempt=attempt,
        evidence_text=evidence_text,
    )
    raw = llm_client.chat(
        [ChatMessage(role="user", content=prompt)],
        temperature=0.0,
        stage="fact_extraction_feedback",
    ).strip()

    data = json.loads(extract_json(raw))
    if data.get("found") is False or "value" not in data:
        return None

    try:
        value = float(str(data["value"]).replace(",", "").replace("$", "").strip())
    except (ValueError, TypeError):
        return None

    return GroundedFact(
        name=role.name,
        value=value,
        unit=str(data.get("unit", "")).strip(),
        source_quote=str(data.get("source_quote", "")).strip(),
        period=str(data.get("period", role.period)).strip(),
        row_label=str(data.get("row_label", "")).strip(),
        concept=getattr(role, "concept", "") or "",
    )


def _format_current_facts(facts: dict[str, GroundedFact]) -> str:
    if not facts:
        return "(none)"
    lines = []
    for name in sorted(facts):
        fact = facts[name]
        lines.append(
            "- {name}: value={value}, unit={unit}, period={period}, row_label={row_label}, "
            "source_quote={source_quote}".format(
                name=name,
                value=fact.value,
                unit=fact.unit or "",
                period=fact.period or "",
                row_label=fact.row_label or "",
                source_quote=fact.source_quote or "",
            )
        )
    return "\n".join(lines)


def _format_previous_fact(fact: GroundedFact | None) -> str:
    if fact is None:
        return "(none)"
    return (
        "value={value}, unit={unit}, period={period}, row_label={row_label}, "
        "source_quote={source_quote}"
    ).format(
        value=fact.value,
        unit=fact.unit or "",
        period=fact.period or "",
        row_label=fact.row_label or "",
        source_quote=fact.source_quote or "",
    )
