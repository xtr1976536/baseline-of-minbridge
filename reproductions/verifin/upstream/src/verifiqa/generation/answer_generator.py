from __future__ import annotations

import json
from typing import Iterable

from verifiqa.generation.llm_client import ChatMessage
from verifiqa.types import EvidenceChunk, RetrievalPlan


_PROMPT = """\
Answer the financial question using only the retrieved filing evidence below.

Return exactly one JSON object and nothing else. The full response must be
parseable by json.loads after stripping whitespace. No markdown fences, no prose
outside JSON, no second JSON object, no alternate answers, and no initial/final
answer narrative.

Required response shape:
{{
  "answer": "<one concise final answer with the relevant numeric value and calculation when possible>"
}}

Rules:
- These benchmark questions ask for a numeric final answer. The answer string
  must contain the final numeric value whenever the evidence contains enough
  numbers to compute or look up it.
- Do not use outside knowledge.
- Do not invent missing numbers.
- If the retrieved evidence is insufficient after checking all visible numeric
  relationships, say that in the answer.
- Financial QA text can contain OCR/tokenization artifacts in possessives,
  dates, and punctuation. Do not reject the question solely because a token like
  "2019s" looks like a date if the evidence clearly provides the requested
  company, metric, year, and arithmetic relationship.
- If the evidence states a value and its percentage of another requested value,
  compute the requested value from value / percentage.
- The retrieval plan lists the required facts and acceptable aliases. If a
  retrieved table row matches an alias, use it as evidence for that fact.
- If deterministic calculation guidance is provided, use that formula and those
  operands as the authority for the requested calculation.
- For deterministic XBRL subtotal guidance, use the first/leftmost numeric
  column in the rendered evidence as the current filing period, even if its
  calendar-year header differs from the fiscal-year label in the question.
- Prefer STRUCTURED TABLE ROWS over raw page text. They bind row labels,
  columns/periods, values, statement type, and unit scale.
- If a structured row contains the requested row and column, use that value
  instead of reparsing the raw page text.
- For per-share shareholder-recovery questions, if the retrieved evidence
  provides a reported per-share equity metric such as tangible book value per
  share, TBVPS, or book value per share, answer from that reported per-share
  value instead of decomposing gross assets by shares.
- Keep the answer short.
- You must evaluate any arithmetic yourself. Never leave an unevaluated
  expression (e.g. "119815 + (-19697)" or "a = b + c") as the answer — always
  compute it and end the answer string with the single resulting number.
  Bad:  "119815 + (-1 * 19697)"
  Good: "119815 - 19697 = 100118"
- Do not include contradictory numbers or self-corrections in the answer string.
- Do not output ```json or any code fence.

Question:
{question}

Retrieval plan:
{retrieval_plan}

Deterministic calculation guidance:
{formula_context}
{feedback}
Retrieved filing evidence:
{evidence}
"""


class AnswerGenerator:
    """Generate the natural-language answer directly from retrieved filing text."""

    def __init__(self, llm_client):
        self.llm_client = llm_client

    def generate(
        self,
        question: str,
        evidence_chunks: Iterable[EvidenceChunk],
        retrieval_plan: RetrievalPlan | None = None,
        formula_context: str | None = None,
        feedback: str | None = None,
    ) -> str:
        evidence = _format_evidence(evidence_chunks)
        feedback_block = (
            f"\nFeedback on your previous attempt:\n{feedback}\n" if feedback else ""
        )
        prompt = _PROMPT.format(
            question=question,
            retrieval_plan=_format_retrieval_plan(retrieval_plan),
            formula_context=formula_context or "No deterministic formula guidance.",
            feedback=feedback_block,
            evidence=evidence,
        )
        content = self.llm_client.chat(
            [ChatMessage(role="user", content=prompt)],
            temperature=0.0,
            stage="answer_generation",
        ).strip()
        if not content:
            raise ValueError("empty_llm_answer")

        data = json.loads(_extract_json(content))
        answer = str(data.get("answer", "")).strip()
        if not answer:
            raise ValueError("missing_answer_field")
        return answer


def _format_evidence(evidence_chunks: Iterable[EvidenceChunk]) -> str:
    parts = []
    for chunk in evidence_chunks:
        page = "" if chunk.page is None else f" page={chunk.page}"
        parts.append(f"[{chunk.chunk_id}{page}]\n{chunk.text}")
    return "\n\n".join(parts)


def _format_retrieval_plan(plan: RetrievalPlan | None) -> str:
    if plan is None or not plan.facts:
        return "No explicit plan."
    lines = []
    if plan.metric:
        lines.append(f"metric: {plan.metric}")
    for fact in plan.facts:
        aliases = ", ".join(fact.aliases) if fact.aliases else ""
        parts = [f"- {fact.name}"]
        if fact.period:
            parts.append(f"period={fact.period}")
        if fact.statement:
            parts.append(f"statement={fact.statement}")
        if aliases:
            parts.append(f"aliases=[{aliases}]")
        lines.append(" ".join(parts))
    if plan.reason:
        lines.append(f"reason: {plan.reason}")
    return "\n".join(lines)


def _extract_json(text: str) -> str:
    decoder = json.JSONDecoder()
    start = text.find("{")
    while start != -1:
        try:
            _, end = decoder.raw_decode(text[start:])
            return text[start: start + end]
        except json.JSONDecodeError:
            start = text.find("{", start + 1)
    raise ValueError("no JSON object in answer")
