import os
import re
import json
import logging
from typing import List, Dict, Set, Optional, Any, Tuple
from py2neo import Graph

from .Base import (
    IndicatorNode,
    DecompositionPath,
    DecompositionOutput,
    NodeStatus,
    PathStatus
)

logger = logging.getLogger("EBFR")


class FinanceKnowledgeGraph:
    def __init__(self, uri: str = "bolt://localhost:7687",
                 user: str = "neo4j", password: str = "",
                 lang: str = "zh"):
        self.graph = Graph(uri, auth=(user, password))
        self.lang = lang
        self._term_cache: Dict[str, Dict] = {}

        if lang == "en":
            self.term_label = "FinanceTerm_en"
            self.concept_label = "FinanceConcept_en"
            self.calculated_by_rel = "CALCULATED_BY_EN"
            self.prop_name = "name_en"
            self.prop_definition = "definition_en"
            self.prop_formulas = "formulas_en"
            self.prop_aliases_zh = "aliases_zh_en"
            self.prop_aliases_en = "aliases_en_en"
            self.prop_aliases_abbr = "aliases_abbr_en"
        else:
            self.term_label = "FinanceTerm"
            self.concept_label = "FinanceConcept"
            self.calculated_by_rel = "CALCULATED_BY"
            self.prop_name = "name"
            self.prop_definition = "definition"
            self.prop_formulas = "formulas"
            self.prop_aliases_zh = "aliases_zh"
            self.prop_aliases_en = "aliases_en"
            self.prop_aliases_abbr = "aliases_abbr"

    def get_term_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        if name in self._term_cache:
            return self._term_cache[name]

        query = f"""
        MATCH (t:{self.term_label} {{{self.prop_name}: $name}})
        RETURN t.{self.prop_name} as name, 
               t.{self.prop_definition} as definition, 
               t.{self.prop_formulas} as formulas, 
               t.{self.prop_aliases_zh} as aliases_zh,
               t.{self.prop_aliases_en} as aliases_en, 
               t.{self.prop_aliases_abbr} as aliases_abbr
        """
        result = self.graph.run(query, name=name).data()

        if not result:
            query_alias = f"""
            MATCH (t:{self.term_label})
            WHERE t.{self.prop_aliases_zh} CONTAINS $name 
               OR t.{self.prop_aliases_en} CONTAINS $name 
               OR t.{self.prop_aliases_abbr} CONTAINS $name
               OR toLower(t.{self.prop_name}) = toLower($name)
            RETURN t.{self.prop_name} as name, 
                   t.{self.prop_definition} as definition,
                   t.{self.prop_formulas} as formulas, 
                   t.{self.prop_aliases_zh} as aliases_zh,
                   t.{self.prop_aliases_en} as aliases_en, 
                   t.{self.prop_aliases_abbr} as aliases_abbr
            LIMIT 1
            """
            result = self.graph.run(query_alias, name=name).data()

        if result:
            term_data = result[0]
            term_data['formulas'] = json.loads(term_data['formulas']) if term_data['formulas'] else []
            term_data['aliases_zh'] = json.loads(term_data['aliases_zh']) if term_data['aliases_zh'] else []
            term_data['aliases_en'] = json.loads(term_data['aliases_en']) if term_data['aliases_en'] else []
            term_data['aliases_abbr'] = json.loads(term_data['aliases_abbr']) if term_data['aliases_abbr'] else []
            self._term_cache[name] = term_data
            return term_data

        return None

    def get_calculated_by_targets(self, term_name: str) -> List[str]:
        query = f"""
        MATCH (t:{self.term_label} {{{self.prop_name}: $name}})-[:{self.calculated_by_rel}]->(dep)
        RETURN DISTINCT dep.{self.prop_name} as dep_name
        """
        result = self.graph.run(query, name=term_name).data()
        return [r['dep_name'] for r in result if r['dep_name']]

    def is_leaf_node(self, term_name: str) -> bool:
        term = self.get_term_by_name(term_name)
        if not term:
            return True
        if not term['formulas']:
            return True
        deps = self.get_calculated_by_targets(term_name)
        return len(deps) == 0

    def get_all_term_names(self) -> List[str]:
        query = f"""
        MATCH (t:{self.term_label})
        RETURN t.{self.prop_name} as name
        """
        result = self.graph.run(query).data()
        return [r['name'] for r in result if r['name']]

    def clear_cache(self):
        self._term_cache.clear()

    def test_connection(self) -> bool:
        try:
            count_query = f"MATCH (t:{self.term_label}) RETURN count(t) as count"
            result = self.graph.run(count_query).data()
            count = result[0]['count'] if result else 0
            print(f"[KG] Connected to {self.term_label}, found {count} terms")
            return count > 0
        except Exception as e:
            print(f"[KG] Connection failed: {e}")
            return False


"""
修复后的 FormulaParser 类
请将此代码替换 ProblemDecomposition.py 中原有的 FormulaParser 类（第 168-310 行左右）
"""


class FormulaParser:
    """公式解析器，从公式表达式中提取依赖变量"""

    def __init__(self, kg: FinanceKnowledgeGraph = None, lang: str = "zh"):
        self.kg = kg
        self.lang = lang

    def extract_variables_from_expression(self, expression: str) -> List[str]:
        """
        从公式表达式中提取变量名

        策略：
        1. 首先直接按数学运算符分割（主要方法，不依赖知识图谱）
        2. 如果结果太少，再尝试知识图谱匹配作为补充

        中文例子：
            "营运资本=流动资产-流动负债" -> ["流动资产", "流动负债"]
        英文例子：
            "Working Capital = Current Assets - Current Liabilities" -> ["Current Assets", "Current Liabilities"]
            "Cost of Sales = Beginning Inventory Cost + Purchases During the Period - Ending Inventory Cost"
            -> ["Beginning Inventory Cost", "Purchases During the Period", "Ending Inventory Cost"]
        """
        if not expression:
            return []

        # 移除等号左边的部分
        if '=' in expression:
            expression = expression.split('=', 1)[1].strip()

        if self.lang == "en":
            return self._extract_variables_en(expression)
        else:
            return self._extract_variables_zh(expression)

    def _extract_variables_zh(self, expression: str) -> List[str]:
        """中文公式变量提取"""
        # 运算符包括：+ - × ÷ * / ( ) [ ] 等（注意：不包含空格！）
        operators = r'[\+\-\×\÷\*\/\(\)\[\]\d\.\,\%]+'
        parts = re.split(operators, expression)

        variables = []
        for part in parts:
            part = part.strip()
            if part and not part.isdigit():
                variables.append(part)

        return variables

    def _extract_variables_en(self, expression: str) -> List[str]:
        """
        英文公式变量提取

        策略：先直接按数学运算符分割，保留完整的多词术语
        然后用知识图谱匹配作为补充（如果结果太少）
        """
        # 方法1：直接按数学运算符分割（主要方法）
        # 运算符：+ - × ÷ * / ( ) 以及百分号，但不包括空格！
        math_operators = r'[\+\-\×\÷\*\/\(\)]'
        parts = re.split(math_operators, expression)

        variables = []
        seen = set()
        for part in parts:
            # 清理：去除首尾空格、数字、百分号等
            part = part.strip()
            # 移除开头和结尾的数字和百分号
            part = re.sub(r'^[\d\.\,\%\s]+', '', part)
            part = re.sub(r'[\d\.\,\%\s]+$', '', part)
            part = part.strip()

            # 跳过空字符串、纯数字、太短的字符串
            if not part:
                continue
            if part.replace('.', '').replace(',', '').isdigit():
                continue
            if len(part) <= 1:
                continue
            # 跳过常见的非指标词
            if part.lower() in ['the', 'of', 'and', 'or', 'a', 'an', 'for', 'in', 'on', 'at', 'to', 'by']:
                continue

            if part not in seen:
                variables.append(part)
                seen.add(part)

        # 方法2：如果方法1结果太少，尝试知识图谱匹配作为补充
        if len(variables) < 2 and self.kg:
            try:
                known_terms = self.kg.get_all_term_names()
                if known_terms:
                    # 按长度降序排列，确保长术语优先匹配
                    sorted_terms = sorted(known_terms, key=len, reverse=True)
                    kg_variables = []
                    remaining = expression
                    for term in sorted_terms:
                        pattern = re.compile(re.escape(term), re.IGNORECASE)
                        if pattern.search(remaining):
                            kg_variables.append(term)
                            remaining = pattern.sub(' ', remaining)

                    # 去重
                    kg_seen = set()
                    unique_kg_vars = []
                    for v in kg_variables:
                        if v not in kg_seen:
                            unique_kg_vars.append(v)
                            kg_seen.add(v)

                    # 如果知识图谱匹配结果更多，使用它
                    if len(unique_kg_vars) > len(variables):
                        variables = unique_kg_vars
            except Exception:
                pass

        logger.debug(f"Parsed formula '{expression}' -> variables: {variables}")
        return variables

    @staticmethod
    def extract_variables_from_code(code: str) -> List[str]:
        """
        从 Python 代码中提取函数参数作为变量名

        例如：
            "def working_capital(current_assets, current_liabilities):..."
            -> ["current_assets", "current_liabilities"]
        """
        if not code:
            return []

        # 匹配函数定义中的参数
        match = re.search(r'def\s+\w+\s*\(([^)]*)\)', code)
        if match:
            params_str = match.group(1)
            params = [p.strip() for p in params_str.split(',')]
            return [p for p in params if p and not p.startswith('*')]

        return []

    @staticmethod
    def match_variables_to_terms(expr_vars: List[str],
                                 available_terms: List[str],
                                 kg: FinanceKnowledgeGraph) -> Dict[str, str]:
        """
        将公式中的变量名匹配到图谱中的术语名称

        返回：{公式变量名: 图谱术语名}
        """
        var_to_term = {}

        for var in expr_vars:
            # 首先尝试精确匹配
            if var in available_terms:
                var_to_term[var] = var
                continue

            # 尝试通过别名匹配
            term_data = kg.get_term_by_name(var)
            if term_data:
                var_to_term[var] = term_data['name']
                continue

            # 模糊匹配：检查是否是某个术语的子串或别名的子串
            for term in available_terms:
                term_data = kg.get_term_by_name(term)
                if term_data:
                    all_names = ([term_data['name']] +
                                 term_data.get('aliases_zh', []) +
                                 term_data.get('aliases_en', []))
                    for name in all_names:
                        if var.lower() in name.lower() or name.lower() in var.lower():
                            var_to_term[var] = term_data['name']
                            break
                if var in var_to_term:
                    break

        return var_to_term


class ProblemDecompositionOperator:
    def __init__(self, knowledge_graph: FinanceKnowledgeGraph, lang: str = None):
        self.kg = knowledge_graph
        self.lang = lang if lang else (knowledge_graph.lang if knowledge_graph else "zh")
        self.parser = FormulaParser(kg=knowledge_graph, lang=self.lang)

    def get_formula_for_indicator(self, indicator_name: str) -> Optional[Dict]:
        term_data = self.kg.get_term_by_name(indicator_name)
        if not term_data:
            return None
        formulas = term_data.get('formulas', [])
        return {
            'name': term_data['name'],
            'definition': term_data.get('definition', ''),
            'formulas': formulas,
            'formula_expr': formulas[0].get('expression', '') if formulas else ''
        }

    def get_all_formulas(self, indicator_name: str) -> List[Dict]:
        term_data = self.kg.get_term_by_name(indicator_name)
        if not term_data:
            return []
        return term_data.get('formulas', [])

    def run(self, *, target: str, known: Set[str] = None,
            max_depth: int = 5) -> DecompositionOutput:
        known = known or set()

        term_data = self.kg.get_term_by_name(target)
        if not term_data:
            logger.error(f"Target indicator '{target}' not found in knowledge graph")
            return DecompositionOutput(
                target_indicator=target,
                success=False,
                error_msg=f"Target indicator '{target}' not found in knowledge graph"
            )

        formulas = term_data.get('formulas', [])
        if not formulas:
            logger.info(f"Target indicator '{target}' has no formula, treating as leaf node")
            root = IndicatorNode(
                name=term_data['name'],
                definition=term_data.get('definition', ''),
                level=0,
                is_leaf=True,
                aliases_zh=term_data.get('aliases_zh', []),
                aliases_en=term_data.get('aliases_en', []),
                aliases_abbr=term_data.get('aliases_abbr', [])
            )
            return DecompositionOutput(
                target_indicator=target,
                paths=[DecompositionPath(
                    path_id=0,
                    root=root,
                    formula_expr="",
                    formula_code="",
                    total_nodes=1,
                    max_depth=0,
                    leaf_nodes=[target]
                )]
            )

        all_deps = self.kg.get_calculated_by_targets(term_data['name'])

        paths = []
        for path_id, formula in enumerate(formulas):
            expr = formula.get('expression', '')
            code = formula.get('code', '')

            logger.info(f"Decomposing path {path_id}: {expr}")

            expr_vars = self.parser.extract_variables_from_expression(expr)
            var_to_term = self.parser.match_variables_to_terms(expr_vars, all_deps, self.kg)

            root = IndicatorNode(
                name=term_data['name'],
                definition=term_data.get('definition', ''),
                formula_expr=expr,
                formula_code=code,
                level=0,
                is_leaf=False,
                aliases_zh=term_data.get('aliases_zh', []),
                aliases_en=term_data.get('aliases_en', []),
                aliases_abbr=term_data.get('aliases_abbr', [])
            )

            stats = {'total_nodes': 1, 'max_depth': 0, 'leaf_nodes': []}

            matched_terms = list(var_to_term.values())
            for dep_term in matched_terms:
                if dep_term in known:
                    child = self._create_leaf_node(dep_term, level=1)
                    root.children.append(child)
                    stats['total_nodes'] += 1
                    stats['max_depth'] = max(stats['max_depth'], 1)
                    stats['leaf_nodes'].append(dep_term)
                else:
                    child = self._decompose_recursive(
                        term_name=dep_term,
                        current_level=1,
                        max_depth=max_depth,
                        known=known,
                        visited=set([term_data['name']]),
                        stats=stats
                    )
                    root.children.append(child)

            path = DecompositionPath(
                path_id=path_id,
                root=root,
                formula_expr=expr,
                formula_code=code,
                total_nodes=stats['total_nodes'],
                max_depth=stats['max_depth'],
                leaf_nodes=stats['leaf_nodes']
            )
            paths.append(path)

        return DecompositionOutput(
            target_indicator=target,
            paths=paths,
            success=True
        )

    def _decompose_recursive(self, term_name: str, current_level: int,
                             max_depth: int, known: Set[str],
                             visited: Set[str], stats: Dict) -> IndicatorNode:
        stats['total_nodes'] += 1
        stats['max_depth'] = max(stats['max_depth'], current_level)

        if term_name in visited:
            logger.warning(f"Circular dependency detected: {term_name}")
            return self._create_leaf_node(term_name, current_level, note="Circular dependency")

        if current_level >= max_depth:
            stats['leaf_nodes'].append(term_name)
            return self._create_leaf_node(term_name, current_level, note="Max depth reached")

        term_data = self.kg.get_term_by_name(term_name)
        if not term_data:
            stats['leaf_nodes'].append(term_name)
            return self._create_leaf_node(term_name, current_level, note="Not found in KG")

        if self.kg.is_leaf_node(term_name):
            stats['leaf_nodes'].append(term_name)
            return IndicatorNode(
                name=term_data['name'],
                definition=term_data.get('definition', ''),
                level=current_level,
                is_leaf=True,
                aliases_zh=term_data.get('aliases_zh', []),
                aliases_en=term_data.get('aliases_en', []),
                aliases_abbr=term_data.get('aliases_abbr', [])
            )

        formulas = term_data.get('formulas', [])
        formula = formulas[0] if formulas else {}
        expr = formula.get('expression', '')
        code = formula.get('code', '')

        node = IndicatorNode(
            name=term_data['name'],
            definition=term_data.get('definition', ''),
            formula_expr=expr,
            formula_code=code,
            level=current_level,
            is_leaf=False,
            aliases_zh=term_data.get('aliases_zh', []),
            aliases_en=term_data.get('aliases_en', []),
            aliases_abbr=term_data.get('aliases_abbr', [])
        )

        new_visited = visited | {term_name}
        all_deps = self.kg.get_calculated_by_targets(term_name)
        expr_vars = self.parser.extract_variables_from_expression(expr)
        var_to_term = self.parser.match_variables_to_terms(expr_vars, all_deps, self.kg)

        for dep_term in var_to_term.values():
            if dep_term in known:
                child = self._create_leaf_node(dep_term, current_level + 1)
                node.children.append(child)
                stats['total_nodes'] += 1
                stats['max_depth'] = max(stats['max_depth'], current_level + 1)
                stats['leaf_nodes'].append(dep_term)
            else:
                child = self._decompose_recursive(
                    term_name=dep_term,
                    current_level=current_level + 1,
                    max_depth=max_depth,
                    known=known,
                    visited=new_visited,
                    stats=stats
                )
                node.children.append(child)

        if not node.children:
            node.is_leaf = True
            stats['leaf_nodes'].append(term_name)

        return node

    def _create_leaf_node(self, term_name: str, level: int, note: str = "") -> IndicatorNode:
        term_data = self.kg.get_term_by_name(term_name)
        if term_data:
            return IndicatorNode(
                name=term_data['name'],
                definition=term_data.get('definition', '') + (f" [{note}]" if note else ""),
                level=level,
                is_leaf=True,
                aliases_zh=term_data.get('aliases_zh', []),
                aliases_en=term_data.get('aliases_en', []),
                aliases_abbr=term_data.get('aliases_abbr', [])
            )
        else:
            return IndicatorNode(
                name=term_name,
                definition=note,
                level=level,
                is_leaf=True
            )

    def decompose_missing(self, missing_vars: List[str], original_subgoals: List = None,
                          context: str = "") -> List[Dict]:
        if not missing_vars:
            return []

        new_subgoals = []
        original_constraints = {}
        if original_subgoals:
            for sg in original_subgoals:
                if hasattr(sg, 'metric') and hasattr(sg, 'constraints'):
                    original_constraints[sg.metric] = sg.constraints
                elif isinstance(sg, dict):
                    original_constraints[sg.get('metric', '')] = sg.get('constraints', {})

        for var_name in missing_vars:
            term_data = self.kg.get_term_by_name(var_name) if self.kg else None

            if term_data and term_data.get('formulas'):
                formulas = term_data['formulas']
                formula = formulas[0] if formulas else {}
                expr = formula.get('expression', '')

                expr_vars = self.parser.extract_variables_from_expression(expr)
                all_deps = self.kg.get_calculated_by_targets(term_data['name']) if self.kg else []
                var_to_term = self.parser.match_variables_to_terms(expr_vars, all_deps, self.kg)

                for dep_var, dep_term in var_to_term.items():
                    inherited = original_constraints.get(var_name, {})
                    if isinstance(inherited, dict):
                        constraints = inherited
                    elif hasattr(inherited, '__dict__'):
                        constraints = {
                            "temporal_scope": getattr(inherited, 'temporal_scope', None),
                            "entity_scope": getattr(inherited, 'entity_scope', None),
                            "meta": {
                                "currency": getattr(inherited.meta, 'currency', None) if hasattr(inherited, 'meta') else None,
                                "scale": getattr(inherited.meta, 'scale', None) if hasattr(inherited, 'meta') else None,
                                "unit": getattr(inherited.meta, 'unit', None) if hasattr(inherited, 'meta') else None
                            }
                        }
                    else:
                        constraints = {"temporal_scope": None, "entity_scope": None, "meta": {}}

                    new_subgoals.append({
                        "metric": dep_term,
                        "constraints": constraints
                    })
            else:
                inherited = original_constraints.get(var_name, {})
                if isinstance(inherited, dict):
                    constraints = inherited
                elif hasattr(inherited, '__dict__'):
                    constraints = {
                        "temporal_scope": getattr(inherited, 'temporal_scope', None),
                        "entity_scope": getattr(inherited, 'entity_scope', None),
                        "meta": {}
                    }
                else:
                    constraints = {"temporal_scope": None, "entity_scope": None, "meta": {}}

                new_subgoals.append({
                    "metric": var_name,
                    "constraints": constraints
                })

        return new_subgoals


class DecompositionVisualizer:
    @staticmethod
    def print_tree(node: IndicatorNode, prefix: str = "", is_last: bool = True):
        connector = "└── " if is_last else "├── "
        leaf_marker = " 🍃" if node.is_leaf else ""
        formula_info = f" [{node.formula_expr}]" if node.formula_expr and not node.is_leaf else ""
        print(f"{prefix}{connector}{node.name}{leaf_marker}{formula_info}")
        child_prefix = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(node.children):
            DecompositionVisualizer.print_tree(child, child_prefix, i == len(node.children) - 1)

    @staticmethod
    def print_output(output: DecompositionOutput):
        print("=" * 80)
        print(f"Target indicator: {output.target_indicator}")
        print(f"Status: {'Success' if output.success else 'Failed'}")
        if output.error_msg:
            print(f"Error: {output.error_msg}")
        print(f"Number of paths: {len(output.paths)}")
        print("=" * 80)
        for path in output.paths:
            print(f"\n{'─' * 40}")
            print(f"Path {path.path_id}: {path.formula_expr}")
            print(f"Total nodes: {path.total_nodes}, Max depth: {path.max_depth}")
            print(f"Leaf nodes: {', '.join(path.leaf_nodes)}")
            print(f"{'─' * 40}")
            DecompositionVisualizer.print_tree(path.root, "", True)

    @staticmethod
    def to_mermaid(output: DecompositionOutput) -> str:
        lines = ["graph TD"]
        for path in output.paths:
            lines.append(f"    subgraph Path{path.path_id}[\"Path {path.path_id}: {path.formula_expr}\"]")
            node_id_map = {}
            counter = [0]

            def add_node(node: IndicatorNode, parent_id: str = None):
                node_id = f"P{path.path_id}N{counter[0]}"
                counter[0] += 1
                node_id_map[id(node)] = node_id
                shape_start = "((" if node.is_leaf else "["
                shape_end = "))" if node.is_leaf else "]"
                lines.append(f"        {node_id}{shape_start}\"{node.name}\"{shape_end}")
                if parent_id:
                    lines.append(f"        {parent_id} --> {node_id}")
                for child in node.children:
                    add_node(child, node_id)

            add_node(path.root)
            lines.append("    end")
        return "\n".join(lines)

    @staticmethod
    def to_json(output: DecompositionOutput, filepath: str):
        import json
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output.to_dict(), f, ensure_ascii=False, indent=2)
        print(f"Saved to: {filepath}")