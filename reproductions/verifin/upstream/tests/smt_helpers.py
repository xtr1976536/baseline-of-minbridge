from verifiqa.formulas.evaluator import (
    format_number,
    formula_assertion_smt,
    formula_domain_constraints_smt,
)


def render_counterexample_smt(claim, schema):
    missing = [name for name in schema.required_evidence if name not in claim.variables]
    if missing:
        raise ValueError(f"missing_evidence_variable:{missing[0]}")
    metric_var = f"computed_{schema.metric}"
    lines = ["(set-logic QF_NRA)", "(set-option :produce-unsat-cores true)", "(set-option :produce-models true)", ""]
    for variable in schema.allowed_variables:
        lines.append(f"(declare-const {variable} Real)")
    lines.append("")
    for name in schema.required_evidence:
        value = claim.variables[name]
        lines.append(f"(assert (! (= {name} {format_number(value)}) :named evidence_{name}))")
    lines.append("")
    lines.append(
        f"(assert (! {formula_assertion_smt(metric_var, schema.formula, schema.computed_unit or schema.claim_unit)} :named formula_{schema.metric}))"
    )
    for index, constraint in enumerate(
        formula_domain_constraints_smt(metric_var, schema.formula, schema.computed_unit or schema.claim_unit)
    ):
        lines.append(f"(assert (! {constraint} :named domain_{schema.metric}_{index}))")
    claimed = format_number(claim.claimed_value)
    tolerance = format_number(schema.tolerance)
    lines.append("")
    lines.append(f"(assert (! (<= (- {metric_var} {claimed}) {tolerance}) :named claim_upper))")
    lines.append(f"(assert (! (<= (- {claimed} {metric_var}) {tolerance}) :named claim_lower))")
    lines.append("")
    lines.append("(check-sat)")
    lines.append("(get-unsat-core)")
    lines.append("(get-model)")
    return "\n".join(lines)
