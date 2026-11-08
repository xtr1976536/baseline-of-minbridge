"""Appendix F text extracted from the supplied PDF, with explicit slot filling.

The paper leaves {format} and {example} unresolved. The schemas below instantiate
those slots; no unpublished few-shot examples are invented.
"""
from pathlib import Path

from .types import dumps


DIRECTORY = Path(__file__).with_name("prompts")

EVIDENCE_FORMAT = dumps({
    "found": True,
    "var_bindings": {"v1": {
        "metric": "requested metric", "constraints": {
            "temporal_scope": "copy input", "entity_scope": "copy input",
            "meta": {"currency": "copy input", "scale": "copy input", "unit": "copy input"}},
        "value": 123.0, "context": "source evidence showing the metric's own label and its printed number",
        "source_label":"copy the actual label in the document",
        "observed_meta": {"currency": None, "scale": None, "unit": None},
        'context_spans': [],
        "confidence": 1.0,
    }}, "missing_vars": [], "notes": None,
}) + ('\nobserved_meta describes ONLY explicitly printed currency/scale/unit of the raw value; use null when unknown. '
      'Do not inherit a derived ratio unit onto a monetary input. Do not scale the extracted value.'
      ' Quote the source_label in its original language. Explain any clear alias or translation in notes, as required above. '
      'Never collapse adjusted/unadjusted, current/non-current or other financial qualifiers; a different known metric is not a semantic alias. '
      'For tables, put the copied period/entity header and the labelled data row in context_spans so their coordinate can be checked. '
      'These may be separate source spans; typography, whitespace and Markdown need not be identical. '
      'Do not put another metric\'s value under the requested label. Never turn a formula result into extracted evidence. '
      'Scale is a multiplicative reporting unit such as thousand or million; shares, years and per-share describe unit, not scale. '
      '\nIf missing: {"found":false,"var_bindings":{},"missing_vars":["v1"],"notes":"reason"}')

VERIFY_FORMAT = dumps({"path_decisions": [{
    "path_id": "copy candidate path_id", "decision": "VALID or INVALID", "justification": "short reason",
}]}) + "\nReturn exactly one decision for EVERY supplied path, with no new paths or values."


def render(name: str, **slots) -> str:
    text = (DIRECTORY / (name + ".txt")).read_text(encoding="utf-8")
    # Single pass prevents evidence containing {query} etc. from becoming instructions.
    import re
    return re.sub(r"\{([a-z_]+)\}", lambda m: str(slots[m[1]]) if m[1] in slots else m[0], text)
