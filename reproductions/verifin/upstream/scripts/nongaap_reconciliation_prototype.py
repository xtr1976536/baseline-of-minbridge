"""Prototype: document-sourced formula authority for company-specific non-GAAP metrics.

A non-GAAP metric has no universal formula, so the policy registry can't hold one
(the verifier abstains with `no_policy_for_metric`). But SEC Regulation G requires
the company to publish a *reconciliation* of every non-GAAP measure in the filing.
That reconciliation IS the authoritative formula for that company's metric — and it
is self-verifying: the extracted components, run through the bridge, must reproduce
the company's OWN published non-GAAP total.

This prototype demonstrates the idea end-to-end on the real Amcor FY2023 case
(financebench_id_01930, "Real change in Sales excluding FX, passthrough, one-off
items"), using the actual reconciliation table from the 10-K and the project's Z3
runner. It does NOT touch the pipeline — it's a worked example for the writeup.

Reconciliation table (Amcor FY2023 10-K, "Components of revenue change", Total,
twelve months ended June 30):

    Reported Growth %                       1
    FX %                                   (3)
    Constant Currency Growth %              4     = Reported - FX  (1 - (-3) = 4)
    Raw Material Pass Through %             5
    Items affecting comparability %        (1)
    Comparable Constant Currency Growth %   0     <- the company's PUBLISHED total
"""
from __future__ import annotations

from dataclasses import dataclass, field

from verifiqa.verification.z3_runner import Z3Runner


# --- What the (LLM) reconciliation extractor would emit, as grounded structured data ---
@dataclass
class ReconComponent:
    name: str
    value: float
    sign: str          # "+" or "-": how this row enters the bridge to the non-GAAP total
    source_quote: str  # grounded to the filing reconciliation table


@dataclass
class NonGaapReconciliation:
    metric: str
    company: str
    period: str
    base: ReconComponent                 # the GAAP/anchor line the bridge starts from
    adjustments: list[ReconComponent]     # +/- rows
    published_total: float                # the company's own published non-GAAP figure (also in the table)
    published_total_quote: str
    source: str = "10-K MD&A — Components of revenue change (Reg G reconciliation)"


AMCOR = NonGaapReconciliation(
    metric="comparable_constant_currency_growth_percent",
    company="Amcor plc",
    period="FY2023 vs FY2022 (twelve months ended June 30, 2023)",
    base=ReconComponent(
        "constant_currency_growth_percent", 4.0, "+",
        "Constant Currency Growth %  ... 4",
    ),
    adjustments=[
        ReconComponent("raw_material_pass_through_percent", 5.0, "-",
                       "Raw Material Pass Through %  ... 5"),
        ReconComponent("items_affecting_comparability_percent", -1.0, "-",
                       "Items affecting comparability %  ... (1)"),
    ],
    published_total=0.0,
    published_total_quote="Comparable Constant Currency Growth %  ... 0",
)


def build_smt(recon: NonGaapReconciliation, claimed_value: float, tolerance: float = 0.5) -> str:
    lines: list[str] = ["(set-logic QF_LRA)"]
    terms = [recon.base.name]
    decls = [recon.base, *recon.adjustments]
    for c in decls:
        lines.append(f"(declare-const {c.name} Real)")
    lines += [
        "(declare-const published_total Real)",
        "(declare-const computed Real)",
        "(declare-const claimed_value Real)",
        "",
        "; --- grounded component values from the filing reconciliation table ---",
    ]
    for c in decls:
        lines.append(f"(assert (! (= {c.name} {_smt_num(c.value)}) :named evidence_{c.name}))")
    lines.append(f"(assert (! (= published_total {_smt_num(recon.published_total)}) :named evidence_published_total))")

    # bridge formula extracted from the reconciliation: base +/- adjustments
    expr = recon.base.name
    for c in recon.adjustments:
        op = "+" if c.sign == "+" else "-"
        expr = f"({op} {expr} {c.name})"
    lines += [
        "",
        "; --- formula authority: the bridge published in the filing's reconciliation ---",
        f"(assert (! (= computed {expr}) :named reconciliation_formula))",
        "",
        "; --- reconciliation self-consistency: the bridge must reproduce the company's",
        ";     OWN published non-GAAP total (this is the independent authority check) ---",
        f"(assert (! (<= (- computed published_total) {_smt_num(tolerance)}) :named recon_upper))",
        f"(assert (! (<= (- published_total computed) {_smt_num(tolerance)}) :named recon_lower))",
        "",
        "; --- claim check: the answer must equal the reconciled value ---",
        f"(assert (! (= claimed_value {_smt_num(claimed_value)}) :named claim))",
        f"(assert (! (<= (- claimed_value computed) {_smt_num(tolerance)}) :named claim_upper))",
        f"(assert (! (<= (- computed claimed_value) {_smt_num(tolerance)}) :named claim_lower))",
        "",
        "(check-sat)",
    ]
    return "\n".join(lines)


def _smt_num(x: float) -> str:
    return f"(- {abs(x):g})" if x < 0 else f"{x:g}"


def verify(recon: NonGaapReconciliation, claimed_value: float) -> str:
    smt = build_smt(recon, claimed_value)
    result = Z3Runner().run(smt, label=f"nongaap_{recon.company}")
    return result.solver_status


if __name__ == "__main__":
    print(f"Metric : {AMCOR.metric}")
    print(f"Company: {AMCOR.company}  ({AMCOR.period})")
    print(f"Source : {AMCOR.source}")
    bridge = " - ".join([AMCOR.base.name] + [a.name for a in AMCOR.adjustments])
    print(f"Bridge : comparable_cc_growth = {bridge}")
    print(f"         = 4 - 5 - (-1) = {AMCOR.base.value - sum(a.value for a in AMCOR.adjustments):g}")
    print(f"Company's published total: {AMCOR.published_total:g}  ('{AMCOR.published_total_quote}')")
    print()
    print("--- Verifying the model's answer (0.0, 'flat') against the filed reconciliation ---")
    print(f"  Z3 verdict: {verify(AMCOR, claimed_value=0.0)}   (SAT = verified vs company's own definition)")
    print()
    print("--- Counter-check: a wrong answer (4.0, forgot to subtract pass-through/items) ---")
    print(f"  Z3 verdict: {verify(AMCOR, claimed_value=4.0)}   (UNSAT = correctly rejected)")
