from __future__ import annotations

import sys
import os
from typing import Any, Dict, List, Optional
from pydantic import ValidationError

from .prompts import (
    QUESTION_ANALYSIS_PROMPTS,
    QUESTION_ANALYSIS_WITH_FORMULA_PROMPTS,
    INDICATOR_RECOGNITION_PROMPTS
)
from .Base import OQAResult, extract_json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.LLMClient import create_llm


class QuestionAnalyzerOperator:

    def __init__(self, config=None):
        if config is None:
            self.llm = create_llm()
        else:
            self.llm = create_llm(config['model_name'])

    def _build_oqa_user_prompt(self, query: str, context: Optional[str] = None) -> str:
        return f"""Query:
{query}

Context:
{context}

Return JSON only.
"""

    def _build_oqa_with_formula_prompt(self, query: str, context: str,
                                       target_indicator: str, formula_info: Dict) -> str:
        formulas_text = ""
        if formula_info and formula_info.get('formulas'):
            for i, f in enumerate(formula_info['formulas']):
                expr = f.get('expression', '')
                if expr:
                    formulas_text += f"  Formula {i + 1}: {expr}\n"

        if not formulas_text:
            formulas_text = "  (No formula found - this is a leaf indicator that should be directly retrieved)"

        return f"""Query:
{query}

Target Indicator: {target_indicator}

Formula from Knowledge Graph:
{formulas_text}

Definition: {formula_info.get('definition', 'N/A') if formula_info else 'N/A'}

Context (Document):
{context}

IMPORTANT: Output ONLY the direct components from the formula above as subgoals.
Do NOT look for deeper sub-components in the document.

Return JSON only.
"""

    def recognize_indicator(self, query: str) -> Dict[str, str]:
        """识别问题中的目标指标"""
        messages = [
            {"role": "system", "content": INDICATOR_RECOGNITION_PROMPTS},
            {"role": "user", "content": f"Question: {query}\n\nReturn JSON only."},
        ]

        raw = self.llm.invoke(messages).content
        try:
            data = extract_json(raw)
            return {
                "target_indicator": data.get("target_indicator", ""),
                "entity_scope": data.get("entity_scope", "unknown"),
                "temporal_scope": data.get("temporal_scope", "unknown")
            }
        except Exception:
            return {
                "target_indicator": "",
                "entity_scope": "unknown",
                "temporal_scope": "unknown"
            }

    def run(self, query: str, context: str, formula_context: Dict = None) -> OQAResult:
        """
        分析问题并生成结构化的查询计划

        Args:
            query: 用户问题
            context: 文档上下文
            formula_context: 知识图谱公式信息，格式:
                {
                    "target_indicator": "Gross Profit",
                    "definition": "...",
                    "formulas": [{"expression": "Gross Profit = Net Sales - Cost of Sales", "code": "..."}],
                    "dependencies": ["Net Sales", "Cost of Sales"]
                }

        Returns:
            OQAResult: 结构化的查询分析结果
        """
        # if formula_context and formula_context.get('formulas'):
        #     target = formula_context.get('target_indicator', '')
        #     messages = [
        #         {"role": "system", "content": QUESTION_ANALYSIS_WITH_FORMULA_PROMPTS},
        #         {"role": "user", "content": self._build_oqa_with_formula_prompt(
        #             query, context, target, formula_context
        #         )},
        #     ]
        # else:
        messages = [
            {"role": "system", "content": QUESTION_ANALYSIS_PROMPTS},
            {"role": "user", "content": self._build_oqa_user_prompt(query, context)},
        ]

        raw = self.llm.invoke(messages).content
        print(raw)
        data = extract_json(raw)

        try:
            return OQAResult.model_validate(data)
        except ValidationError as e:
            raise ValueError(f"OQA JSON does not match schema: {e}\nRAW={raw}") from e

    def run_with_kg(self, query: str, context: str, kg) -> OQAResult:
        """
        带知识图谱的问题分析（自动识别指标并查询公式）

        Args:
            query: 用户问题
            context: 文档上下文
            kg: FinanceKnowledgeGraph 实例

        Returns:
            OQAResult: 结构化的查询分析结果
        """
        indicator_info = self.recognize_indicator(query)
        target_indicator = indicator_info.get("target_indicator", "")

        formula_context = None
        if target_indicator and kg:
            term_data = kg.get_term_by_name(target_indicator)
            if term_data:
                deps = kg.get_calculated_by_targets(target_indicator)
                formula_context = {
                    "target_indicator": term_data['name'],
                    "definition": term_data.get('definition', ''),
                    "formulas": term_data.get('formulas', []),
                    "dependencies": deps
                }

        return self.run(query, context, formula_context)