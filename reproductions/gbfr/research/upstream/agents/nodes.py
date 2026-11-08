import logging
import re
from typing import Dict, Any, List, Optional, Set, Tuple
from langchain_core.messages import AIMessage

from agents.states import (
    WorkflowState, PathResult, PathStatus,
    ThreeStateCache, CacheStatus, IndicatorTask, SinglePathState
)

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operators.Base import (
    OQAResult, Subgoal, Constraints, MetaAttributes,
    EvidenceSeekingOutput, EvidenceItem,
    PoTProgram, PoTExecutionResult
)

logger = logging.getLogger("EBFR")


class NodeFactory:
    def __init__(self, question_analyzer, evidence_seeker, decomposer,
                 pot_generator, pot_executor, kg=None, lang: str = "en"):
        self.analyzer = question_analyzer
        self.seeker = evidence_seeker
        self.decomposer = decomposer
        self.generator = pot_generator
        self.executor = pot_executor
        self.kg = kg
        self.lang = lang
        self.evidence_cache = ThreeStateCache()
        self.indicator_cache: Dict[str, float] = {}

    def get_all_formulas(self, indicator: str) -> List[Dict]:
        if self.kg:
            term_data = self.kg.get_term_by_name(indicator)
            if term_data:
                return term_data.get('formulas', [])
        return []

    def get_formula_dependencies(self, indicator: str, formula_index: int = 0) -> List[str]:
        if not self.kg:
            return []
        term_data = self.kg.get_term_by_name(indicator)
        if not term_data:
            return []
        formulas = term_data.get('formulas', [])
        if not formulas or formula_index >= len(formulas):
            return []
        formula = formulas[formula_index]
        expr = formula.get('expression', '')
        return self._parse_formula_vars(expr)

    def _parse_formula_vars(self, expression: str) -> List[str]:
        if not expression:
            return []

        if '=' in expression:
            expression = expression.split('=', 1)[1].strip()

        math_operators = r'[\+\-×÷\*\/\(\)]'
        parts = re.split(math_operators, expression)

        variables = []
        seen = set()
        for part in parts:
            part = part.strip()
            part = re.sub(r'^[\d\.\,\%\s]+', '', part)
            part = re.sub(r'[\d\.\,\%\s]+$', '', part)
            part = part.strip()

            if not part:
                continue
            if part.replace('.', '').replace(',', '').isdigit():
                continue
            if len(part) <= 1:
                continue
            if part.lower() in ['the', 'of', 'and', 'or', 'a', 'an', 'for', 'in', 'on', 'at', 'to', 'by']:
                continue

            if part not in seen:
                variables.append(part)
                seen.add(part)

        if len(variables) < 2 and self.kg:
            try:
                known_terms = self.kg.get_all_term_names()
                if known_terms:
                    sorted_terms = sorted(known_terms, key=len, reverse=True)
                    kg_variables = []
                    remaining = expression
                    for term in sorted_terms:
                        pattern = re.compile(re.escape(term), re.IGNORECASE)
                        if pattern.search(remaining):
                            kg_variables.append(term)
                            remaining = pattern.sub(' ', remaining)

                    kg_seen = set()
                    unique_kg_vars = []
                    for v in kg_variables:
                        if v not in kg_seen:
                            unique_kg_vars.append(v)
                            kg_seen.add(v)

                    if len(unique_kg_vars) > len(variables):
                        variables = unique_kg_vars
            except Exception:
                pass

        logger.debug(f"Parsed formula '{expression}' -> variables: {variables}")
        return variables

    def question_analysis_node(self, state: WorkflowState) -> Dict[str, Any]:
        query = state.get("query", "")
        context = state.get("context", "")
        logger.info("Starting new question")
        logger.info(f"query: {query}")
        logger.info(f"context: {context}")
        if not query:
            return {
                "success": False,
                "error_msg": "Missing query",
                "messages": [AIMessage(content="Error: Missing query")]
            }

        try:
            indicator_info = self.analyzer.recognize_indicator(query)
            target_indicator = indicator_info.get("target_indicator", "")
            entity_scope = indicator_info.get("entity_scope", "unknown")
            temporal_scope = indicator_info.get("temporal_scope", "unknown")

            logger.info(f"Recognized target indicator: {target_indicator}")

            formula_context = None
            if target_indicator and self.kg:
                if isinstance(target_indicator, list):
                    target_indicator = str(target_indicator)
                term_data = self.kg.get_term_by_name(target_indicator)
                if term_data:
                    deps = self.kg.get_calculated_by_targets(target_indicator)
                    formula_context = {
                        "target_indicator": term_data['name'],
                        "definition": term_data.get('definition', ''),
                        "formulas": term_data.get('formulas', []),
                        "dependencies": deps
                    }
                    logger.info(f"Found formula context: {formula_context.get('formulas', [])}")

            oqa_result: OQAResult = self.analyzer.run(query, context, formula_context)
            current_subgoals = list(oqa_result.subgoals)

            for sg in current_subgoals:
                if hasattr(sg, 'constraints') and sg.constraints:
                    if not sg.constraints.entity_scope or sg.constraints.entity_scope == "unknown":
                        sg.constraints.entity_scope = entity_scope
                    if not sg.constraints.temporal_scope or sg.constraints.temporal_scope == "unknown":
                        sg.constraints.temporal_scope = temporal_scope
            logger.info(f"Question analysis complete, target: {target_indicator}, type: {oqa_result.reasoning_type}")
            return {
                "target_indicator": target_indicator,
                "formula_context": formula_context,
                "oqa_result": oqa_result,
                "current_subgoals": current_subgoals,
                "decomposition_depth": 0,
                "all_var_bindings": {},
                "all_path_results": {},
                "pending_tasks": [],
                "success": True,
                "messages": [AIMessage(
                    content=f"Question analysis complete, target: {target_indicator}, type: {oqa_result.reasoning_type}")]
            }
        except Exception as e:
            logger.error(f"Question analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error_msg": str(e),
                "messages": [AIMessage(content=f"Question analysis failed: {e}")]
            }

    def evidence_seeking_node(self, state: WorkflowState) -> Dict[str, Any]:
        query = state.get("query", "")
        context = state.get("context", "")
        if context == "" or context == "[]":
            context = query
        current_subgoals = state.get("current_subgoals", [])
        all_var_bindings = state.get("all_var_bindings", {})

        if not current_subgoals:
            return {
                "evidence_output": EvidenceSeekingOutput(
                    found=bool(all_var_bindings),
                    var_bindings=all_var_bindings,
                    missing_vars=[],
                    notes="No new subgoals to search"
                ),
                "pending_decomposition": [],
                "success": bool(all_var_bindings)
            }

        try:
            subgoals_as_dict = []
            for sg in current_subgoals:
                if isinstance(sg, Subgoal):
                    meta = sg.constraints.meta if sg.constraints and sg.constraints.meta else MetaAttributes()
                    subgoals_as_dict.append({
                        "metric": sg.metric,
                        "constraints": {
                            "temporal_scope": sg.constraints.temporal_scope if sg.constraints else None,
                            "entity_scope": sg.constraints.entity_scope if sg.constraints else None,
                            "meta": {
                                "currency": meta.currency,
                                "scale": meta.scale,
                                "unit": meta.unit
                            }
                        }
                    })
                elif isinstance(sg, dict):
                    subgoals_as_dict.append(sg)

            evidence_output: EvidenceSeekingOutput = self.seeker.run(context, subgoals_as_dict)

            new_bindings = dict(all_var_bindings)
            if evidence_output.var_bindings:
                new_bindings.update(evidence_output.var_bindings)
                for var_name, item in evidence_output.var_bindings.items():
                    cache_key = f"{item.metric}_{item.constraints.temporal_scope}_{item.constraints.entity_scope}"
                    self.evidence_cache.complete_query(cache_key, item.value, True)
            logger.info(f'Evidence seeking success: {evidence_output}')
            return {
                "evidence_output": evidence_output,
                "all_var_bindings": new_bindings,
                "pending_decomposition": evidence_output.missing_vars if evidence_output.missing_vars else [],
                "success": True
            }
        except Exception as e:
            logger.error(f"Evidence seeking failed: {e}")
            import traceback
            traceback.print_exc()

            missing = []
            for sg in current_subgoals:
                if isinstance(sg, Subgoal):
                    missing.append(sg.metric)
                elif isinstance(sg, dict):
                    missing.append(sg.get("metric", ""))

            evidence_output = EvidenceSeekingOutput(
                found=False,
                var_bindings={},
                missing_vars=missing,
                notes=str(e)
            )
            logger.info(f'Evidence seeking error: {evidence_output}')

            return {
                "evidence_output": evidence_output,
                "pending_decomposition": missing,
                "success": False,
                "error_msg": str(e)
            }

    def multipath_decomposition_node(self, state: WorkflowState) -> Dict[str, Any]:
        pending = state.get("pending_decomposition", [])
        current_subgoals = state.get("current_subgoals", [])
        depth = state.get("decomposition_depth", 0)
        max_depth = state.get("max_decomposition_depth", 6)
        context = state.get("context", "")
        all_var_bindings = state.get("all_var_bindings", {})
        all_path_results = dict(state.get("all_path_results", {}))
        pattern_general = re.compile(r'^var\d+_')

        if not pending:
            return {"current_subgoals": [], "pending_decomposition": [], "success": True}

        if depth >= max_depth:
            return {
                "current_subgoals": [],
                "pending_decomposition": [],
                "success": False,
                "error_msg": f"Max decomposition depth {max_depth} reached"
            }

        try:
            all_new_subgoals = []
            inherited_constraints = self._get_inherited_constraints(current_subgoals)

            for missing_var in pending:
                if pattern_general.match(missing_var):
                    missing_var = re.sub(r'^var\d+_', '', str(missing_var))
                formulas = self.get_all_formulas(missing_var)

                if not formulas:
                    logger.info(f"No formula found for {missing_var}, treating as leaf")
                    all_new_subgoals.append({
                        "metric": missing_var,
                        "constraints": inherited_constraints
                    })
                    continue

                logger.info(f"Found {len(formulas)} formula(s) for {missing_var}")

                for path_idx, formula in enumerate(formulas):
                    path_id = f"{missing_var}_f{path_idx}_d{depth + 1}"
                    formula_expr = formula.get('expression', '')
                    required_vars = self._parse_formula_vars(formula_expr)

                    logger.info(f"  Path {path_id}: {formula_expr}")
                    logger.info(f"    Required vars: {required_vars}")

                    path_result = PathResult(
                        path_id=path_id,
                        indicator_name=missing_var,
                        formula_expr=formula_expr,
                        formula_index=path_idx,
                        depth=depth + 1,
                        status=PathStatus.ACTIVE,
                        required_vars=required_vars,
                        node_results={},
                        missing_vars=[]
                    )
                    all_path_results[path_id] = path_result

                    for var in required_vars:
                        if var not in [sg.get("metric") if isinstance(sg, dict) else sg.metric
                                       for sg in all_new_subgoals]:
                            all_new_subgoals.append({
                                "metric": var,
                                "constraints": inherited_constraints,
                                "_parent_path": path_id
                            })
            logger.info(f'Multipath decomposition success: {all_new_subgoals}')
            return {
                "current_subgoals": all_new_subgoals,
                "decomposition_depth": depth + 1,
                "pending_decomposition": [],
                "all_path_results": all_path_results,
                "success": True
            }
        except Exception as e:
            logger.error(f"Multipath decomposition failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "current_subgoals": [],
                "pending_decomposition": [],
                "success": False,
                "error_msg": str(e)
            }

    def _get_inherited_constraints(self, subgoals: List) -> Dict:
        for sg in subgoals:
            if isinstance(sg, Subgoal) and sg.constraints and sg.metric:
                meta_dict = {}
                if hasattr(sg.constraints, 'meta') and sg.constraints.meta:
                    meta_obj = sg.constraints.meta
                    meta_dict = {
                        "currency": getattr(meta_obj, 'currency', None),
                        "scale": getattr(meta_obj, 'scale', None),
                        "unit": getattr(meta_obj, 'unit', None),
                    }
                return {
                    "temporal_scope": sg.constraints.temporal_scope,
                    "entity_scope": sg.constraints.entity_scope,
                    "meta": meta_dict
                }
            elif isinstance(sg, dict) and sg.get("constraints"):
                return sg.get("constraints", {})
        return {"temporal_scope": None, "entity_scope": None, "meta": {}}

    def _compute_indicator_recursive(self, indicator: str, context: str,
                                     constraints: Dict, depth: int, max_depth: int,
                                     visited: Set[str], all_path_results: Dict) -> Tuple[bool, Optional[float], int]:
        if indicator in self.indicator_cache:
            logger.info(f"  [Cache hit] {indicator} = {self.indicator_cache[indicator]}")
            return True, self.indicator_cache[indicator], depth

        if indicator in visited:
            logger.warning(f"Circular dependency detected: {indicator}")
            return False, None, depth

        if depth > max_depth:
            logger.warning(f"Max depth reached for {indicator}")
            return False, None, depth

        cache_key = f"{indicator}_{constraints.get('temporal_scope')}_{constraints.get('entity_scope')}"
        cached = self.evidence_cache.get(cache_key)
        if cached and cached.found:
            self.indicator_cache[indicator] = cached.value
            return True, cached.value, depth

        subgoals_dict = [{
            "metric": indicator,
            "constraints": constraints
        }]

        try:
            evidence = self.seeker.run(context, subgoals_dict)
            if evidence.found and evidence.var_bindings:
                for var_name, item in evidence.var_bindings.items():
                    value = item.value
                    self.indicator_cache[indicator] = value

                    self.evidence_cache.complete_query(
                        cache_key,
                        value,
                        True,
                        unit=item.constraints.meta.unit if item.constraints and item.constraints.meta else None,
                        source=item.context[:100] if item.context else ""
                    )

                    logger.info(f"  [Direct found] {indicator}")
                    logger.info(f"    ├─ value: {value}")
                    logger.info(f"    ├─ confidence: {item.confidence}")
                    if item.constraints:
                        logger.info(f"    ├─ temporal_scope: {item.constraints.temporal_scope}")
                        logger.info(f"    ├─ entity_scope: {item.constraints.entity_scope}")
                        if item.constraints.meta:
                            logger.info(
                                f"    ├─ meta: currency={item.constraints.meta.currency}, scale={item.constraints.meta.scale}, unit={item.constraints.meta.unit}")
                    if item.context:
                        snippet = item.context[:100].replace('\n', ' ')
                        logger.info(f"    └─ evidence: \"{snippet}...\"" if len(
                            item.context) > 100 else f"    └─ evidence: \"{snippet}\"")

                    if not hasattr(self, 'full_evidence_items'):
                        self.full_evidence_items = {}
                    self.full_evidence_items[indicator] = item

                    return True, value, depth
            else:
                logger.info(f"[Direct not found] {indicator} - {constraints}")
        except Exception as e:
            logger.debug(f"Direct extraction failed for {indicator}: {e}")

        formulas = self.get_all_formulas(indicator)
        if not formulas:
            logger.info(f"  [Leaf not found] {indicator}")
            return False, None, depth

        new_visited = visited | {indicator}
        successful_results = []

        for path_idx, formula in enumerate(formulas):
            path_id = f"{indicator}_f{path_idx}_d{depth}"
            formula_expr = formula.get('expression', '')
            formula_code = formula.get('code', '')
            required_vars = self._parse_formula_vars(formula_expr)

            logger.info(f"  [Try path] {path_id}: {formula_expr}")

            path_result = PathResult(
                path_id=path_id,
                indicator_name=indicator,
                formula_expr=formula_expr,
                formula_index=path_idx,
                depth=depth,
                status=PathStatus.ACTIVE,
                required_vars=required_vars
            )

            var_values = {}
            all_found = True
            max_child_depth = depth

            for var in required_vars:
                found, value, child_depth = self._compute_indicator_recursive(
                    var, context, constraints, depth + 1, max_depth, new_visited, all_path_results
                )
                if found and value is not None:
                    var_values[var] = value
                    max_child_depth = max(max_child_depth, child_depth)
                else:
                    all_found = False
                    path_result.missing_vars.append(var)
                    break

            if all_found and len(var_values) == len(required_vars):
                try:
                    result = self._execute_formula(formula_expr, formula_code, var_values)
                    if result is not None:
                        path_result.status = PathStatus.COMPLETED
                        path_result.result = result
                        path_result.node_results = var_values
                        path_result.depth = max_child_depth
                        all_path_results[path_id] = path_result
                        successful_results.append((path_id, result, max_child_depth))

                        logger.info(f"  [Path success] {path_id}")
                        logger.info(f"    ├─ formula: {formula_expr}")
                        logger.info(f"    ├─ inputs: {var_values}")
                        logger.info(f"    ├─ result: {indicator} = {result}")
                        logger.info(f"    └─ depth: {max_child_depth}")
                except Exception as e:
                    logger.error(f"Formula execution failed for {path_id}: {e}")
                    path_result.status = PathStatus.BLOCKED
                    path_result.error_msg = str(e)
            else:
                path_result.status = PathStatus.BLOCKED
                all_path_results[path_id] = path_result

        if successful_results:
            successful_results.sort(key=lambda x: x[2])
            best_path_id, best_result, best_depth = successful_results[0]
            self.indicator_cache[indicator] = best_result
            return True, best_result, best_depth

        return False, None, depth

    def _execute_formula(self, formula_expr: str, formula_code: str, var_values: Dict[str, float]) -> Optional[float]:
        if formula_code:
            try:
                local_env = {
                    '__builtins__': {
                        'abs': abs, 'min': min, 'max': max, 'sum': sum,
                        'round': round, 'pow': pow, 'len': len,
                        'float': float, 'int': int,
                        'True': True, 'False': False, 'None': None,
                    }
                }
                exec(formula_code, local_env)
                if 'compute' in local_env:
                    result = local_env['compute'](var_values)
                    print(result)
                    if isinstance(result, dict):
                        return result.get('value')
                    return result
            except Exception as e:
                logger.debug(f"Code execution failed: {e}")

        if '=' in formula_expr:
            expr_part = formula_expr.split('=', 1)[1].strip()

            eval_expr = expr_part
            for var_name, var_value in sorted(var_values.items(), key=lambda x: -len(x[0])):
                eval_expr = eval_expr.replace(var_name, str(var_value))

            eval_expr = eval_expr.replace('×', '*').replace('÷', '/')

            try:
                result = eval(eval_expr, {"__builtins__": {}}, {})
                return result
            except Exception as e:
                logger.debug(f"Expression eval failed: {e}")

        return None

    def multipath_compute_node(self, state: WorkflowState) -> Dict[str, Any]:
        target_indicator = state.get("target_indicator", "")
        context = state.get("context", "")
        oqa_result = state.get("oqa_result")
        max_depth = state.get("max_decomposition_depth", 3)
        all_var_bindings = state.get("all_var_bindings", {})

        if not target_indicator:
            return {
                "success": False,
                "error_msg": "No target indicator identified"
            }

        self.indicator_cache.clear()
        self.evidence_cache.clear()

        for var_name, item in all_var_bindings.items():
            if hasattr(item, 'metric') and hasattr(item, 'value'):
                self.indicator_cache[item.metric] = item.value

        constraints = {}
        if oqa_result and oqa_result.subgoals:
            sg = oqa_result.subgoals[0]
            if hasattr(sg, 'constraints') and sg.constraints:
                meta_dict = {}
                if hasattr(sg.constraints, 'meta') and sg.constraints.meta:
                    meta_obj = sg.constraints.meta
                    meta_dict = {
                        "currency": getattr(meta_obj, 'currency', None),
                        "scale": getattr(meta_obj, 'scale', None),
                        "unit": getattr(meta_obj, 'unit', None),
                    }
                constraints = {
                    "temporal_scope": sg.constraints.temporal_scope,
                    "entity_scope": sg.constraints.entity_scope,
                    "meta": meta_dict
                }

        all_path_results = {}

        logger.info(f"Starting multipath computation for: {target_indicator}")

        found, result, final_depth = self._compute_indicator_recursive(
            target_indicator, context, constraints, 0, max_depth, set(), all_path_results
        )

        if found and result is not None:
            successful_paths = [
                pid for pid, pr in all_path_results.items()
                if pr.status == PathStatus.COMPLETED
            ]

            evidence_items = getattr(self, 'full_evidence_items', {})

            return {
                "final_value": result,
                "all_path_results": all_path_results,
                "successful_paths": successful_paths,
                "evidence_items": evidence_items,
                "indicator_cache": dict(self.indicator_cache),
                "success": True
            }
        else:
            return {
                "all_path_results": all_path_results,
                "evidence_items": getattr(self, 'full_evidence_items', {}),
                "indicator_cache": dict(self.indicator_cache),
                "success": False,
                "error_msg": f"Could not compute {target_indicator}: no successful path found"
            }

    def execution_node(self, state: WorkflowState) -> Dict[str, Any]:
        oqa_result = state.get("oqa_result")
        all_var_bindings = state.get("all_var_bindings", {})
        query = state.get("query", "")
        context = state.get("context", "")
        all_path_results = state.get("all_path_results", {})
        final_value = state.get("final_value")

        if final_value is not None:
            return {"final_value": final_value, "success": True}

        if not oqa_result:
            return {"success": False, "error_msg": "Missing OQA result"}

        if not all_var_bindings:
            return {"success": False, "error_msg": "No evidence found"}

        try:
            merged_evidence = EvidenceSeekingOutput(
                found=True,
                var_bindings=all_var_bindings,
                missing_vars=[],
                notes=None
            )

            var_values = {}
            for var_name, evidence_item in all_var_bindings.items():
                var_values[var_name] = evidence_item.value

            max_retries = 3
            program = None
            exec_result = None

            for attempt in range(max_retries):
                if attempt == 0:
                    program = self.generator.generate_for_solve(
                        query=query,
                        context=context,
                        reasoning_type=oqa_result.reasoning_type,
                        evidences=merged_evidence,
                        precision=oqa_result.precision
                    )
                else:
                    logger.info(f"Retry attempt {attempt + 1} after execution error: {exec_result.error}")
                    program = self.generator.generate_for_solve_with_retry(
                        query=query,
                        context=context,
                        reasoning_type=oqa_result.reasoning_type,
                        evidences=merged_evidence,
                        precision=oqa_result.precision,
                        previous_code=program.program,
                        execution_error=exec_result.error
                    )

                exec_result = self.executor.run(
                    program=program.program,
                    var_values=var_values,
                    path_id=0
                )

                if exec_result.ok and exec_result.value is not None:
                    path_result = PathResult(
                        path_id="main_path",
                        formula_expr="",
                        depth=0,
                        status=PathStatus.COMPLETED,
                        result=exec_result.value,
                        node_results=var_values
                    )
                    all_path_results["main_path"] = path_result

                    return {
                        "program": program,
                        "execution_result": exec_result,
                        "final_value": exec_result.value,
                        "all_path_results": all_path_results,
                        "success": True
                    }

            return {
                "program": program,
                "execution_result": exec_result,
                "success": False,
                "error_msg": f"Execution failed after {max_retries} attempts: {exec_result.error if exec_result else 'Unknown error'}"
            }

        except Exception as e:
            logger.error(f"Execution failed: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error_msg": str(e)}

    def path_evaluation_node(self, state: WorkflowState) -> Dict[str, Any]:
        all_path_results = state.get("all_path_results", {})
        final_value = state.get("final_value")

        if final_value is not None:
            return {
                "final_value": final_value,
                "success": True
            }

        successful_paths = []
        for path_id, path_result in all_path_results.items():
            if isinstance(path_result, PathResult):
                if path_result.status == PathStatus.COMPLETED and path_result.result is not None:
                    successful_paths.append((path_id, path_result))
            elif isinstance(path_result, dict):
                if path_result.get("status") == PathStatus.COMPLETED.value:
                    successful_paths.append((path_id, path_result))

        if not successful_paths:
            return {
                "success": False,
                "error_msg": "All paths failed",
                "selected_path_id": ""
            }

        successful_paths.sort(key=lambda x: x[1].depth if isinstance(x[1], PathResult) else x[1].get("depth", 0))
        best_path_id, best_path = successful_paths[0]

        if isinstance(best_path, PathResult):
            best_result = best_path.result
        else:
            best_result = best_path.get("result")

        return {
            "final_value": best_result,
            "selected_path_id": best_path_id,
            "successful_paths": [p[0] for p in successful_paths],
            "success": True
        }

    def answer_generation_node(self, state: WorkflowState) -> Dict[str, Any]:
        query = state.get("query", "")
        oqa_result = state.get("oqa_result")
        final_value = state.get("final_value")
        success = state.get("success", False)
        error_msg = state.get("error_msg", "")
        target_indicator = state.get("target_indicator", "")

        if not success or final_value is None:
            answer = f"Unable to answer: {error_msg}" if self.lang == "en" else f"无法回答：{error_msg}"
            return {"final_answer": answer, "success": False}

        answer_prompt = f"""
You need to generate the final answer based on the user's question and the calculation result.

User Question:
{query}

Calculation Result:
{final_value}

Reasoning Type: {oqa_result.reasoning_type if oqa_result else 'unknown'}
Operator: {oqa_result.operator if oqa_result else 'unknown'}
Target Indicator: {target_indicator}

Requirements:
1. Understand what the user is asking (a value? a range? a comparison? a percentage?)
2. Extract the information the user really wants from the calculation result
3. Answer in natural, concise language that matches the expected format
4. If result is a dict, extract useful info; if tuple, may represent range; if numeric, use directly
5. Only return the answer itself, no explanation of calculation process

Answer:
"""

        response = self.generator.llm.invoke(answer_prompt)
        final_answer = response.content.strip()

        return {
            "final_answer": final_answer,
            "final_value": final_value,
            "success": True,
            "messages": [AIMessage(content=final_answer)]
        }

    def error_node(self, state: WorkflowState) -> Dict[str, Any]:
        error_msg = state.get("error_msg", "Unknown error")
        all_var_bindings = state.get("all_var_bindings", {})
        all_path_results = state.get("all_path_results", {})

        partial_info = []
        if all_var_bindings:
            values_info = ", ".join([f"{k}={v.value}" for k, v in all_var_bindings.items()])
            partial_info.append(f"Found values: {values_info}")

        if all_path_results:
            for path_id, pr in all_path_results.items():
                if isinstance(pr, PathResult) and pr.node_results:
                    partial_info.append(f"Path {path_id}: {pr.node_results}")

        if partial_info:
            answer = f"Partial result - {'; '.join(partial_info)}. Error: {error_msg}"
        else:
            answer = f"Error: {error_msg}"

        return {
            "final_answer": answer,
            "success": False,
            "messages": [AIMessage(content=answer)]
        }

    def final_node(self, state: WorkflowState) -> Dict[str, Any]:
        return {
            "messages": [AIMessage(content=state.get("final_answer", "Processing complete"))]
        }