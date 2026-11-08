"""Arithmetic consistency of Table 1 rates and Table 4 denominators.

This is conditional on the paper's single fixed-test-set accuracy definition.
It does not infer undocumented repeated-run averages or change reference scores.
"""
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

from .data import EXPECTED
from .runner import PAPER_RESULTS


def compatible_correct_counts(percent, denominator: int, rounding=ROUND_HALF_UP) -> list[int]:
    if denominator <= 0:
        raise ValueError("Positive denominator required")
    target = Decimal(str(percent)).quantize(Decimal(".01"))
    return [k for k in range(denominator+1)
            if (Decimal(100)*k/denominator).quantize(Decimal(".01"), rounding=rounding) == target]


def audit_main_table() -> dict:
    cells = []
    for backbone, datasets in PAPER_RESULTS.items():
        for dataset, (total, abstention) in datasets.items():
            for metric, percent, denominator in [
                ("total_accuracy", total, EXPECTED[dataset]["total"]),
                ("abstention_accuracy", abstention, EXPECTED[dataset]["counterfactual"]),
            ]:
                candidates = compatible_correct_counts(percent, denominator)
                cells.append({"backbone": backbone, "dataset": dataset, "metric": metric,
                              "reported_percent": percent, "denominator_table4": denominator,
                              "compatible_integer_correct_counts": candidates,
                              "compatible_if_truncated_instead": compatible_correct_counts(percent, denominator, ROUND_DOWN),
                              "single_fixed_test_set_rounding_consistent": bool(candidates)})
    return {"assumption": "Single fixed test set; accuracy = 100 * integer correct count / stated denominator",
            "rounding": "Two decimal places, nearest (ROUND_HALF_UP); truncation also checked separately",
            "cells": cells, "inconsistent_cell_count": sum(not c["single_fixed_test_set_rounding_consistent"] for c in cells),
            "action": "Do not adjust labels, denominators, or reference scores to force a match; aggregation details may be missing"}


def audit_directed_degree_claims(nodes: int, edges: int, reported_in_degree, reported_out_degree) -> dict:
    if nodes <= 0 or edges < 0:
        raise ValueError("Invalid graph size")
    expected = Decimal(edges) / nodes
    rounded = expected.quantize(Decimal(".1"), rounding=ROUND_HALF_UP)
    incoming = Decimal(str(reported_in_degree))
    outgoing = Decimal(str(reported_out_degree))
    return {"assumption": "In/out degree averaged over all nodes of the same directed graph and same dependency edges",
            "nodes": nodes, "edges": edges, "required_average_in_degree": str(expected),
            "required_average_out_degree": str(expected), "required_at_one_decimal": str(rounded),
            "reported_average_in_degree": str(incoming), "reported_average_out_degree": str(outgoing),
            "consistent_under_stated_assumption": rounded == incoming == outgoing,
            "identity": "sum(indegree)=sum(outdegree)=number_of_directed_edges",
            "needed_clarification": "If different subgraphs/edge filters or averaging populations were used, those definitions are required"}
