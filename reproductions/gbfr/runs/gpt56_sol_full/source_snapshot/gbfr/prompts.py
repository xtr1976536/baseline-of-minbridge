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
        "value": 123.0, "context": "verbatim evidence including labels/headers; use one continuous span or separate complete copied sentences, never paraphrase",
        "observed_meta": {"currency": None, "scale": None, "unit": None},
        'context_spans': [],
        'label_alignment':{'source_label':'exact original-language label/header','kind':'literal or registered_alias or translation or semantic_alias',
                           'explanation':'explain a translation or alias, otherwise null'},
        "confidence": 1.0,
    }}, "missing_vars": [], "notes": None,
}) + ('\nobserved_meta describes ONLY explicitly printed currency/scale/unit of the raw value; use null when unknown. '
      'Do not inherit a derived ratio unit onto a monetary input. Do not scale the extracted value.'
      ' For a Chinese/English translation, quote the actual source_label and explicitly explain the translation in label_alignment; preserve all metric qualifiers. '
      'If metric and source label use different languages, kind MUST be translation and explanation MUST be nonempty. '
      'A translation is a semantic claim by OES, not a new registered FMKG alias. '
      'For other clear contextual wording of the SAME metric, use semantic_alias with an explicit explanation and exact quoted source_label. '
      'Never collapse adjusted/unadjusted, current/non-current or other financial qualifiers; a different known metric is not a semantic alias. '
      'For tables, include the complete original header row and target data row (all cells and pipes) in context_spans when they are disjoint; do not return only a header name or a bare numeric cell. '
      'Every context_span must be verbatim. For non-tables use [] if context already contains both label and value.'
      '\nIf missing: {"found":false,"var_bindings":{},"missing_vars":["v1"],"notes":"reason"}')

VERIFY_FORMAT = dumps({"path_decisions": [{
    "path_id": "copy candidate path_id", "decision": "VALID or INVALID", "justification": "short reason",
}]}) + "\nReturn exactly one decision for EVERY supplied path, with no new paths or values."


def render(name: str, **slots) -> str:
    text = (DIRECTORY / (name + ".txt")).read_text(encoding="utf-8")
    # Single pass prevents evidence containing {query} etc. from becoming instructions.
    import re
    return re.sub(r"\{([a-z_]+)\}", lambda m: str(slots[m[1]]) if m[1] in slots else m[0], text)
