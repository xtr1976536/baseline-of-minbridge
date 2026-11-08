"""End-to-end financial dependency example from Figures 1--2 (scripted LLM)."""
import asyncio

import pytest

from gbfr.engine import GBFR
from gbfr.graph import Formula, Metric, MetricGraph, Operand
from .helpers import ScriptedClient


def build_roe_graph():
    money = {"meta": {"currency": "USD", "scale": "millions", "unit": None}}
    return MetricGraph([
        Metric("Net Income", ["Net Profit"], "", "atomic", []),
        Metric("Final Equity", ["Total Equity"], "", "atomic", []),
        Metric("Initial Equity", [], "", "derived", [Formula(
            "initial:prior-end", "Initial Equity", "e", [
                Operand("e", "Final Equity", {"temporal_scope": "$year-1"})],
            "Initial Equity = prior-year Final Equity")]),
        Metric("Average Equity", [], "", "derived", [Formula(
            "avg:equity", "Average Equity", "(b+e)/2", [Operand("b", "Initial Equity"), Operand("e", "Final Equity")],
            "Average Equity = (Initial Equity + Final Equity)/2")]),
        Metric("ROE", ["Return on Equity"], "", "derived", [Formula(
            "roe:ni-equity", "ROE", "i/a", [Operand("i", "Net Income", money), Operand("a", "Average Equity", money)],
            "ROE = Net Income / Average Equity", meta={"currency": None, "scale": None, "unit": "ratio"})]),
    ])


@pytest.mark.parametrize("include_2022", [False, True])
def test_roe_growth_abstains_exactly_when_prior_equity_is_missing(include_2022):
    meta = {"currency": None, "scale": None, "unit": "ratio"}
    c24 = {"temporal_scope": "2024", "entity_scope": "Company A", "meta": meta}
    c23 = {**c24, "temporal_scope": "2023"}
    plan = {"reasoning_type": "ComparativeReasoning", "operator": "change ratio", "precision": "percentage",
            "subgoals": [{"metric": "ROE", "constraints": c24}, {"metric": "ROE", "constraints": c23}]}
    evidence = {("Net Income", "2024"): (500, "Net Profit 2024: 500"),
                ("Net Income", "2023"): (420, "Net Profit 2023: 420"),
                ("Final Equity", "2024"): (2500, "Total Equity 2024: 2500"),
                ("Final Equity", "2023"): (2200, "Total Equity 2023: 2200")}
    if include_2022:
        evidence[("Final Equity", "2022")] = (1900, "Total Equity 2022: 1900")
    context = "; ".join(text for _, text in evidence.values())
    client = ScriptedClient(c24, evidence, plan=plan)
    result = asyncio.run(GBFR(build_roe_graph(), client).predict("Compute Company A's ROE growth in 2024 over 2023", context))
    if include_2022:
        expected = ((500 / ((2500+2200)/2)) - (420 / ((2200+1900)/2))) / (420 / ((2200+1900)/2))
        assert result.value == pytest.approx(expected)
    else:
        assert result.status == "abstained" and result.value is None
        assert not any(task == "OPE.final" for task, _ in client.calls)
