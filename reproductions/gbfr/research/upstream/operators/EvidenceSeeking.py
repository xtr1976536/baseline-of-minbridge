from typing import List, Dict, Optional, Any
from pydantic import ValidationError
import sys
import os

from .Base import EvidenceItem, EvidenceSeekingOutput, extract_json
from .prompts import EVIDENCE_SEEKING_PROMPTS

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.LLMClient import create_llm


class EvidenceSeekingOperator:
    def __init__(self, config=None):
        if config is None:
            self.llm = create_llm()
        else:
            self.llm = create_llm(config['model_name'])

    def _format_var_line(self, var: str, metric: str, constraints: Dict[str, Any], aliases: List[str]) -> str:
        meta = constraints.get("meta", {})
        entity_scope = constraints.get("entity_scope")
        temporal_scope = constraints.get("temporal_scope")

        currency = meta.get("currency", None) if meta else None
        scale = meta.get("scale", None) if meta else None
        unit = meta.get("unit", None) if meta else None

        alias_str = ", ".join([a for a in aliases if a]) if aliases else "none"
        return (
            f'[{var}] Metric: {metric}. '
            f'Constraints: entity_scope="{entity_scope or "unknown"}"; '
            f'temporal_scope="{temporal_scope or "unknown"}"; '
            f'meta: currency="{currency if currency is not None else "null"}", '
            f'scale="{scale if scale is not None else "null"}", '
            f'unit="{unit if unit is not None else "null"}". '
            f'Aliases: {alias_str}.'
        )

    def _build_user_prompt(self, context: str, nl_lines: List[str]) -> str:
        var_list = "\n".join(f"- {ln}" for ln in nl_lines)
        return (
            "Context:\n"
            f"{context}\n\n"
            "Variables to resolve:\n"
            f"{var_list}\n\n"
            "Return JSON only."
        )

    def run(self, context: str, subgoals: List[Any]) -> EvidenceSeekingOutput:
        nl_lines: List[str] = []
        for idx, sg in enumerate(subgoals, start=1):
            metric = sg.get("metric")
            var = f"var{idx}"
            constraints = sg.get("constraints", {})
            aliases = []
            nl_lines.append(self._format_var_line(var, metric, constraints, aliases))

        messages = [
            {"role": "system", "content": EVIDENCE_SEEKING_PROMPTS},
            {"role": "user", "content": self._build_user_prompt(context=context, nl_lines=nl_lines)},
        ]

        raw = self.llm.invoke(messages).content
        data = extract_json(raw)

        try:
            out = EvidenceSeekingOutput.model_validate(data)
        except ValidationError as e:
            raise ValueError(f"Evidence seeking JSON does not match schema: {e}\nRAW={raw}") from e

        if out.missing_vars:
            out.found = False
        else:
            out.found = bool(out.var_bindings)

        return out