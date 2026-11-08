from gbfr.graph_recovery import SourceIndex, bind_formula, strongly_connected, reciprocal_equation_families, expanded_abbreviation, bind_reference_code, compare_bound_expressions, classify_source_disagreement
from gbfr.graph import Formula, Operand


def record(name, *, aliases=None, formulas=None, related=None):
    return {"term_en": {"name": name, "aliases": {"english": aliases or []}},
            "formula_en": formulas or [], "related_concepts_en": related or []}


def test_scc_reports_real_cycle_nodes_separately_from_downstream_blocking():
    nodes = {"A", "B", "C", "D"}
    edges = {("A", "B"), ("B", "A"), ("B", "C")}
    assert strongly_connected(nodes, edges) == [["A", "B"]]


def test_explicit_canonical_name_wins_over_ambiguous_alias():
    idx = SourceIndex([record("Revenue"), record("Other", aliases=["Revenue"])])
    assert idx.resolve("Revenue")["metric"] == "Revenue"


def test_competing_aliases_are_never_selected_arbitrarily():
    idx = SourceIndex([record("First", aliases=["Common"]), record("Second", aliases=["Common"])])
    assert idx.resolve("Common")["status"] == "ambiguous"


def test_formula_binding_uses_only_explicit_names_and_preserves_hyphens():
    idx = SourceIndex([
        record("Result", formulas=["Result = Non-current Assets - Current Liabilities"],
               related=[{"concept": "Non-current Assets"}, {"concept": "Current Liabilities"}]),
        record("Non-current Assets"), record("Current Liabilities"),
    ])
    candidate = bind_formula(idx, 0, 0)
    assert candidate["status"] == "syntactically_bound"
    assert candidate["expression"] == "x0 - x1"
    assert candidate["semantic_validation"] == "pending"


def test_formula_cancellation_does_not_delete_required_source_operands():
    f = Formula("test", "Result", "a-(a-b)", [Operand("a", "A"), Operand("b", "B")], "Result=A-(A-B)")
    expression, symbols = f.symbolic()
    assert str(expression) == "b" and set(symbols) == {"a", "b"}


def test_reciprocal_formula_detection_does_not_choose_canonical_direction():
    candidates = [
        {"status": "syntactically_bound", "target": "Profit", "expression": "r-c", "source_record": 0,
         "source_formula_index": 0, "source_formula": "Profit=Revenue-Cost",
         "operands": [{"symbol": "r", "metric": "Revenue"}, {"symbol": "c", "metric": "Cost"}]},
        {"status": "syntactically_bound", "target": "Revenue", "expression": "p+c", "source_record": 1,
         "source_formula_index": 0, "source_formula": "Revenue=Profit+Cost",
         "operands": [{"symbol": "p", "metric": "Profit"}, {"symbol": "c", "metric": "Cost"}]},
    ]
    result = reciprocal_equation_families(candidates, ["Profit", "Revenue", "Cost"])
    assert len(result["families"]) == 1
    assert result["families"][0]["canonical_direction"] is None


def test_abbreviation_expansion_does_not_strip_accounting_qualifiers():
    assert expanded_abbreviation("Return on Equity (ROE)") == "Return on Equity"
    assert expanded_abbreviation("Revenue (IFRS)") is None


def test_reference_code_is_analyzed_without_executing_it():
    target = record("Profit", formulas=["Profit = Revenue - Cost"])
    target["code"] = ['def profit(revenue, cost):\n    result = revenue-cost\n    return result']
    idx = SourceIndex([target, record("Revenue"), record("Cost")])
    code = bind_reference_code(idx, 0, 0)
    assert code["status"] == "syntactically_bound"
    target["related_concepts_en"] = [{"concept": "Revenue"}, {"concept": "Cost"}]
    formula = bind_formula(idx, 0, 0)
    assert compare_bound_expressions(formula, code) == "symbolically_equivalent"


def test_reference_code_cannot_execute_side_effects_or_ignore_branching():
    target = record("Profit", formulas=["Profit = Revenue"])
    target["code"] = ['def profit(revenue):\n    open("secret", "w")\n    return revenue']
    idx = SourceIndex([target, record("Revenue")])
    assert bind_reference_code(idx, 0, 0)["status"] == "requires_review"
    target["code"] = ['def profit(revenue):\n    if revenue < 0:\n        return 0\n    return revenue']
    assert bind_reference_code(idx, 0, 0)["status"] == "requires_review"


def candidate(expression, metric="Net Income"):
    return {"status": "syntactically_bound", "target": "Result", "source_formula": "test",
            "expression": expression, "operands": [{"symbol": "x", "metric": metric}]}


def test_only_paper_explicit_aliases_can_resolve_expression_identity():
    result = classify_source_disagreement(candidate("x", "Net Income"), candidate("x", "Net Profit"))
    assert result["category"] == "equivalent_under_explicit_paper_aliases"
    assert result["paper_alias_bindings"]["Net Profit"]["canonical"] == "Net Income"
    assert classify_source_disagreement(candidate("x", "Net Income 2023"), candidate("x", "Net Profit 2024"))["category"] == "input_metric_identity_needs_review"


def test_factor_of_100_is_diagnostic_and_not_an_automatic_unit_fix():
    result = classify_source_disagreement(candidate("x"), candidate("100*x"))
    assert result["category"] == "constant_factor_needs_unit_review"
    assert result["reference_code_divided_by_formula"] == "100"
    assert result["automatic_conversion_applied"] is False
