from typing import Literal
from agents.states import WorkflowState, PathStatus


def after_question_analysis(state: WorkflowState) -> Literal["evidence_seeking", "multipath_compute", "error"]:
    success = state.get("success", False)
    oqa_result = state.get("oqa_result")
    formula_context = state.get("formula_context")

    if not success or oqa_result is None:
        return "error"

    if formula_context and formula_context.get("formulas"):
        return "multipath_compute"

    return "evidence_seeking"


def after_evidence_seeking(state: WorkflowState) -> Literal["execution", "multipath_decomposition", "error"]:
    # print(state)
    evidence_output = state.get("evidence_output")
    pending = state.get("pending_decomposition", [])
    all_bindings = state.get("all_var_bindings", {})
    depth = state.get("decomposition_depth", 0)
    max_depth = state.get("max_decomposition_depth", 3)

    if evidence_output is not None and evidence_output.found and not pending:
        return "execution"

    if all_bindings and not pending:
        return "execution"

    if pending and depth < max_depth:
        return "multipath_decomposition"

    if all_bindings:
        return "execution"

    return "error"


def after_multipath_decomposition(state: WorkflowState) -> Literal["evidence_seeking", "execution", "error"]:
    current_subgoals = state.get("current_subgoals", [])
    success = state.get("success", False)
    all_bindings = state.get("all_var_bindings", {})

    if current_subgoals:
        return "evidence_seeking"

    if all_bindings:
        return "execution"

    return "error"


def after_multipath_compute(state: WorkflowState) -> Literal["path_evaluation", "answer", "error"]:
    success = state.get("success", False)
    final_value = state.get("final_value")
    all_path_results = state.get("all_path_results", {})

    if success and final_value is not None:
        return "answer"

    successful_count = sum(
        1 for pr in all_path_results.values()
        if (isinstance(pr, PathStatus) and pr.status == PathStatus.COMPLETED) or
        (hasattr(pr, 'status') and pr.status == PathStatus.COMPLETED)
    )

    if successful_count > 0:
        return "path_evaluation"

    return "error"


def after_execution(state: WorkflowState) -> Literal["answer", "path_evaluation", "error"]:
    success = state.get("success", False)
    final_value = state.get("final_value")
    all_path_results = state.get("all_path_results", {})

    if len(all_path_results) > 1:
        successful = [
            pr for pr in all_path_results.values()
            if hasattr(pr, 'status') and pr.status == PathStatus.COMPLETED
        ]
        if len(successful) > 1:
            return "path_evaluation"

    if success and final_value is not None:
        return "answer"

    return "error"


def after_path_evaluation(state: WorkflowState) -> Literal["answer", "error"]:
    success = state.get("success", False)
    final_value = state.get("final_value")

    if success and final_value is not None:
        return "answer"

    return "error"