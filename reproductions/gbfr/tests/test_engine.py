import asyncio
from dataclasses import asdict

import pytest

from gbfr.engine import GBFR, grounded, vote
from gbfr.graph import Formula, Metric, MetricGraph, Operand, operand_goal
from gbfr.types import AssetError, Constraints, Goal, ProtocolError
from .helpers import ScriptedClient


CONTEXT = "Company A 2024. Net Sales: 100. COGS: 60. Profit Margin: 0.4. Double Profit: 80."


def test_parallel_all_formulas_shared_operand_once(graph, constraints):
    client = ScriptedClient(constraints, {"Revenue": (100, "Net Sales: 100"),
                            "Cost": (60, "COGS: 60"), "Profit Margin": (0.4, "Profit Margin: 0.4"),
                            "Double Profit": (80, "Double Profit: 80")})
    result = asyncio.run(GBFR(graph, client).predict("Find gross profit", CONTEXT))
    assert result.status == "answered" and result.value == 40
    es = [prompt for task, prompt in client.calls if task == "OES"]
    assert sum('"metric": "Revenue"' in p for p in es) == 1
    assert client.max_active >= 2
    verification = [p for task, p in client.calls if task == "Verify"]
    assert len(verification) == 1
    assert "gp:revenue-cost" in verification[0] and "gp:margin" in verification[0]
    assert "double:gp:inverse:Gross Profit" in verification[0]


def test_direct_evidence_short_circuits_decomposition(graph, constraints):
    client = ScriptedClient(constraints, {"Gross Profit": (40, "Gross Profit: 40")})
    result = asyncio.run(GBFR(graph, client).predict("Find gross profit", "Gross Profit: 40"))
    assert result.value == 40
    assert not any(task in {"Verify", "OPE.metric"} for task, _ in client.calls)


def test_missing_all_paths_propagates_abstention(graph, constraints):
    client = ScriptedClient(constraints)
    result = asyncio.run(GBFR(graph, client).predict("Find gross profit", CONTEXT))
    assert result.status == "abstained" and result.value is None
    assert not any(task == "OPE.final" for task, _ in client.calls)


def test_missing_first_formula_still_explores_others(graph, constraints):
    client = ScriptedClient(constraints, {"Revenue": (100, "Net Sales: 100"),
                                           "Profit Margin": (0.4, "Profit Margin: 0.4")})
    result = asyncio.run(GBFR(graph, client).predict("Find gross profit", CONTEXT))
    assert result.value == 40


def test_judge_rejection_is_not_ignored(graph, constraints):
    client = ScriptedClient(constraints, {"Revenue": (100, "Net Sales: 100"), "Cost": (60, "COGS: 60")},
                            reject={"gp:revenue-cost"})
    result = asyncio.run(GBFR(graph, client).predict("Find gross profit", CONTEXT))
    assert result.status == "abstained"


def test_no_cross_document_negative_cache(graph, constraints):
    client = ScriptedClient(constraints)
    model = GBFR(graph, client)
    async def run():
        first = await model.predict("Find gross profit", "No data")
        client.evidence["Gross Profit"] = (40, "Gross Profit: 40")
        second = await model.predict("Find gross profit", "Gross Profit: 40")
        return first, second
    first, second = asyncio.run(run())
    assert first.status == "abstained" and second.value == 40


def test_memo_key_includes_time(graph, constraints):
    prior = {**constraints, "temporal_scope": "2023"}
    plan = {"reasoning_type": "ComparativeReasoning", "operator": "difference", "precision": "unknown",
            "subgoals": [{"metric": "Revenue", "constraints": constraints}, {"metric": "Revenue", "constraints": prior}]}
    client = ScriptedClient(constraints, {("Revenue", "2024"): (100, "Revenue 2024: 100"),
                                         ("Revenue", "2023"): (80, "Revenue 2023: 80")}, plan=plan)
    asyncio.run(GBFR(graph, client).predict("Compare years", "Revenue 2024: 100; Revenue 2023: 80"))
    assert sum(task == "OES" for task, _ in client.calls) == 2


def test_explicit_boolean_comparison_runs_through_all_main_operators(graph, constraints):
    plan = {"reasoning_type": "ComparativeReasoning", "operator": "compare", "precision": "unknown",
            "subgoals": [{"metric": "Revenue", "constraints": constraints},
                         {"metric": "Cost", "constraints": constraints}]}
    class ComparisonClient(ScriptedClient):
        async def complete(self, task, prompt):
            if task == "OPE.final":
                return 'def compute(vars):\n    return {"value": vars["v1"] > vars["v2"], "trace": {}}'
            return await super().complete(task, prompt)
    client = ComparisonClient(constraints, {"Revenue": (100, "Revenue: 100"), "Cost": (60, "Cost: 60")}, plan=plan)
    result = asyncio.run(GBFR(graph, client).predict("Is Revenue larger? Answer True or False.", "Revenue: 100; Cost: 60"))
    assert result.status == "answered" and result.value == 1
    assert result.meta["unit"] == "boolean"


def test_inverse_inputs_cannot_recursively_resolve(graph, constraints):
    client = ScriptedClient(constraints, {"Revenue": (100, "Net Sales: 100")})
    asyncio.run(GBFR(graph, client).predict("Find gross profit", CONTEXT))
    # Double Profit must not recursively resolve Gross Profit, which would deadlock.
    assert sum(task == "OES" and '"metric": "Double Profit"' in p for task, p in client.calls) == 1


@pytest.mark.parametrize('has_parent',[False,True])
def test_inverse_checks_parent_before_requesting_unneeded_siblings(constraints,has_parent):
    graph=MetricGraph([Metric('Leaf',[],'','atomic',[]),Metric('Sibling',[],'','atomic',[]),
        Metric('Target',[],'','derived',[Formula('t','Target','x',[Operand('x','Leaf')],'Target = Leaf')]),
        Metric('Parent',[],'','derived',[Formula('p','Parent','a+s',[Operand('a','Target'),Operand('s','Sibling')],'Parent = Target + Sibling')])])
    plan={'reasoning_type':'DirectRetrieval','operator':'sum','precision':'unknown',
          'subgoals':[{'metric':'Target','constraints':constraints}]}
    evidence={'Sibling':(4,'Sibling: 4')}
    if has_parent:
        evidence['Parent']=(9,'Parent: 9')
    client=ScriptedClient(constraints,evidence,plan=plan)
    r=asyncio.run(GBFR(graph,client).predict('Find Target','Parent: 9; Sibling: 4'))
    if has_parent:
        assert r.value==5
    else:
        assert r.status=='abstained'
        assert not any(task=='OES' and '"metric": "Sibling"' in prompt for task,prompt in client.calls)


def test_grounding_rejects_invented_value_and_span(constraints):
    goal = Goal("Revenue", Constraints.parse(constraints))
    binding = {"metric": "Revenue", "constraints": constraints, "confidence": 1,
               "value": 90, "context": "Revenue: 100"}
    with pytest.raises(ProtocolError):
        grounded(binding, goal, "Revenue: 100", [])
    binding.update(value=100, context="Revenue: 100 invented")
    with pytest.raises(ProtocolError):
        grounded(binding, goal, "Revenue: 100", [])


def test_negative_accounting_parentheses(constraints):
    goal = Goal("Revenue", Constraints.parse(constraints))
    binding = {"metric": "Revenue", "constraints": constraints, "confidence": 1,
               "value": -100, "context": "Revenue: (100)"}
    assert grounded(binding, goal, "Revenue: (100)", []) == -100


def test_chinese_units_and_terminal_punctuation_are_numeric_evidence(constraints):
    goal = Goal("Revenue", Constraints.parse(constraints))
    for snippet in ["Revenue: 5.514亿元", "Revenue: 5.514."]:
        binding = {"metric": "Revenue", "constraints": constraints, "confidence": 1,
                   "value": 5.514, "context": snippet}
        assert grounded(binding, goal, snippet, []) == 5.514


def test_six_hop_recursion_has_no_arbitrary_depth_cutoff(constraints):
    nodes = [Metric("Leaf", [], "", "atomic", [])]
    for i in range(1, 7):
        dependency = "Leaf" if i == 1 else f"Level {i-1}"
        nodes.append(Metric(f"Level {i}", [], "", "derived", [
            Formula(f"level:{i}", f"Level {i}", "x+1", [Operand("x", dependency)], f"Level {i} = {dependency}+1")]))
    graph = MetricGraph(nodes)
    plan = {"reasoning_type": "DirectRetrieval", "operator": "sum", "precision": "unknown",
            "subgoals": [{"metric": "Level 6", "constraints": constraints}]}
    client = ScriptedClient(constraints, {"Leaf": (10, "Leaf: 10")}, plan=plan)
    result = asyncio.run(GBFR(graph, client).predict("Find Level 6", "Leaf: 10"))
    assert result.value == 16
    assert sum(task == "Verify" for task, _ in client.calls) == 6


def test_tied_consensus_abstains_and_plurality_does_not_average():
    candidates = [{"path_id": str(i), "value": v, "meta": {}} for i, v in enumerate([1, 2])]
    assert vote(candidates) is None
    candidates.append({"path_id": "3", "value": 1, "meta": {}})
    assert vote(candidates)["value"] == 1


def test_explicit_units_are_normalized_for_vote():
    assert vote([{"path_id": "a", "value": 20, "meta": {"unit": "percentage"}},
                 {"path_id": "b", "value": .2, "meta": {"unit": "ratio"}}]) is not None


def test_cycles_are_rejected():
    a = Metric("A", [], "", "derived", [Formula("a", "A", "x", [Operand("x", "B")], "A=B")])
    b = Metric("B", [], "", "derived", [Formula("b", "B", "x", [Operand("x", "A")], "B=A")])
    with pytest.raises(AssetError, match="cycle"):
        MetricGraph([a, b])


def test_log_formula_is_symbolic_and_can_be_uniquely_inverted():
    graph = MetricGraph([
        Metric("Input", [], "", "atomic", []),
        Metric("Log Value", [], "", "derived", [Formula(
            "log:input", "Log Value", "log(x)", [Operand("x", "Input")], "Log Value = log(Input)")]),
    ])
    inverses = graph.inverses("Input")
    assert len(inverses) == 1 and "exp(parent_value)" in inverses[0].expression


def test_relative_year_roles_and_meta_do_not_change_entity(constraints):
    operand = Operand("begin", "Total Equity", {"temporal_scope": "$year-1", "meta": {"unit": None}})
    goal = operand_goal(operand, Constraints.parse(constraints))
    assert goal.constraints.temporal_scope == "2023"
    assert goal.constraints.entity_scope == "Company A"


def test_no_parametric_formula_fallback(graph, constraints):
    plan = {"reasoning_type": "DirectRetrieval", "operator": "sum", "precision": "unknown",
            "subgoals": [{"metric": "Unregistered Financial Indicator", "constraints": constraints}]}
    client = ScriptedClient(constraints, plan=plan)
    result = asyncio.run(GBFR(graph, client).predict("Find Unregistered Financial Indicator", CONTEXT))
    assert result.status == "abstained"
    assert not any(task == "OPE.metric" for task, _ in client.calls)
