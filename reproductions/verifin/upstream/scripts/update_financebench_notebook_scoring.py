#!/usr/bin/env python3
"""Apply publication-safety migrations to the analysis notebook.

This is a one-purpose, idempotent notebook migration. It preserves cell order
while making every manual adjudication candidate-specific, avoiding an
unsupported Fin-o1 checkpoint-size claim, and pointing baseline analyses at
the locked one-pool runs. Outputs are cleared whenever a cell changes because
the previous rendered values are then stale.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import nbformat


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NOTEBOOK = ROOT / "notebooks/agent_financebench_result_metrics.ipynb"

TARGET_BLOCK = '''ADJUDICATED_TARGETS = {
    "financebench_id_04672": (8700.0,),
    "financebench_id_04980": (4600.0,),
    "financebench_id_00882": (8400.0,),
    "financebench_id_02024": (1959.0,),
    "financebench_id_01930": (0.0,),
    "financebench_id_01936": (87.0, 93.0),
}
_NO_ADJUDICATION = object()
def _adjudicated_ok(rid, cv):
    if rid not in ADJUDICATED_TARGETS:
        return _NO_ADJUDICATION
    if cv is None:
        return None
    return any(abs(abs(float(cv)) - abs(target)) <= max(1.0, 0.01 * abs(target))
               for target in ADJUDICATED_TARGETS[rid])
'''

DEFINITION_RE = re.compile(r"KNOWN_CORRECT\s*=\s*\{.*?\}\n", re.DOTALL)
NON_NUMERIC_RE = re.compile(r"NON_NUMERIC\s*=\s*\{.*?\}\n", re.DOTALL)

RUN_REPLACEMENTS = {
    # Replace longer names first so ``fb_base_judge_formula`` is not partially
    # consumed by ``fb_base_judge``.
    "base_judge_haiku_on_haiku": "onepool/xbrl_judge",
    "base_judge_grounded_haiku": "onepool/xbrl_judge_formula",
    "fb_base_judge_formula": "onepool/fb_judge_formula",
    "base_none_haiku": "onepool/xbrl_none",
    "base_pot_haiku": "onepool/xbrl_pot",
    "fb_base_judge": "onepool/fb_judge",
    "fb_base_none": "onepool/fb_none",
    "fb_base_pot": "onepool/fb_pot",
}

CANONICAL_MODEL_CELL = '''from pathlib import Path
import sys

import pandas as pd

ROOT = Path.cwd()
if not (ROOT / "results").exists() and (ROOT.parent / "results").exists():
    ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.paper_scoring import load_manual_adjudications, load_policy, score_all

policy_path = ROOT / "results/scoring_policy.json"
if not policy_path.is_file():
    policy_path = ROOT / "publication_assets_source/results/scoring_policy.json"
policy = load_policy(policy_path)
adjudications = load_manual_adjudications(
    policy_path.parent / policy["candidate_correctness"]["manual_adjudications"]
)
scored = {
    (row["dataset"], row["run"]): row
    for row in score_all(ROOT, policy, adjudications)
    if row["group"] == "answer_models"
}

MODEL_ORDER = [
    ("GPT-5.5", "gpt-5.5"),
    ("Claude Haiku 4.5", "claude-haiku-4.5"),
    ("Fin-o1", "fino1-identity-pending"),
    ("Qwen3-30B", "qwen3-30b"),
    ("Llama-3.1-8B", "llama-3.1-8b"),
    ("Qwen2.5-7B", "qwen2.5-7b"),
]

def _model_metrics(dataset, run):
    row = scored[(dataset, run)]
    if row["status"] == "missing":
        return {"Prec": None, "FA": None, "FR": None, "Abst": None}
    accepted = row["TA"] + row["FA"]
    n = policy["datasets"][dataset]["denominator"]
    return {
        "Prec": round(100 * row["TA"] / accepted, 1) if accepted else float("nan"),
        "FA": row["FA"],
        "FR": row["FR"],
        "Abst": round(100 * row["AB"] / n, 1),
    }

rows = []
for label, run in MODEL_ORDER:
    xbrl = _model_metrics("xbrlfiling", run)
    finance = _model_metrics("financebench", run)
    rows.append({
        "Answer model": label,
        ("XBRLFiling", "Prec"): xbrl["Prec"],
        ("XBRLFiling", "FA"): xbrl["FA"],
        ("XBRLFiling", "FR"): xbrl["FR"],
        ("XBRLFiling", "Abst"): xbrl["Abst"],
        ("FinanceBench", "Prec"): finance["Prec"],
        ("FinanceBench", "FA"): finance["FA"],
        ("FinanceBench", "FR"): finance["FR"],
        ("FinanceBench", "Abst"): finance["Abst"],
    })

models_both = pd.DataFrame(rows).set_index("Answer model")
models_both.columns = pd.MultiIndex.from_tuples(models_both.columns)
print(models_both.to_string())

def _cell(value, count=False):
    if value is None or pd.isna(value):
        return "{--}"
    return f"{int(value)}" if count else f"{float(value):.1f}"

print("\\n% ---- tab:models LaTeX (recomputed from canonical result files) ----")
for label, _ in MODEL_ORDER:
    row = models_both.loc[label]
    cells = []
    for dataset in ("XBRLFiling", "FinanceBench"):
        cells.extend([
            _cell(row[(dataset, "Prec")]),
            _cell(row[(dataset, "FA")], count=True),
            _cell(row[(dataset, "FR")], count=True),
            _cell(row[(dataset, "Abst")]),
        ])
    print(label.replace(" ", "~") + " & " + " & ".join(cells) + r" \\\\")

models_both
'''

FROZEN_TOLERANCE_CELL = '''# Plot the locked tolerance-sweep points without re-solving SMT obligations.
# To perform a new replay intentionally, run scripts/safety_coverage_tolerance.py
# in an environment with the Z3 executable available.
import runpy
from pathlib import Path

import pandas as pd

ROOT = Path.cwd()
if not (ROOT / "results").exists() and (ROOT.parent / "results").exists():
    ROOT = ROOT.parent

points_path = ROOT / "figures/safety_coverage_tolerance_sweep_points.csv"
safety_coverage_points = pd.read_csv(points_path)
assert set(safety_coverage_points["Dataset"]) == {"XBRLBench", "FinanceBench"}
assert set(safety_coverage_points["Tolerance multiplier"]) == {
    0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0,
    25.0, 50.0, 100.0, 250.0, 1000.0,
}

_safety_namespace = runpy.run_path(
    str(ROOT / "scripts" / "safety_coverage_tolerance.py")
)
_safety_coverage_figure = _safety_namespace["plot_safety_coverage"](
    safety_coverage_points,
    ROOT / "figures/safety_coverage_tolerance_sweep",
)
'''


def migrate_source(source: str) -> str:
    if "KNOWN_CORRECT" in source:
        source, replacements = DEFINITION_RE.subn(TARGET_BLOCK, source, count=1)
        if replacements != 1:
            raise ValueError("could not replace KNOWN_CORRECT definition")
        source = source.replace(
            "    if kc and rid in KNOWN_CORRECT: return True\n",
            "    adjudicated = _adjudicated_ok(rid, cv) if kc else _NO_ADJUDICATION\n"
            "    if adjudicated is not _NO_ADJUDICATION: return adjudicated\n",
        )
        source = source.replace(
            "    if _rid(r) in KNOWN_CORRECT: return True\n",
            "    adjudicated = _adjudicated_ok(_rid(r), r.get(\"claimed_value\"))\n"
            "    if adjudicated is not _NO_ADJUDICATION: return adjudicated\n",
        )
        source = source.replace(
            "    if rid in KNOWN_CORRECT: return True\n",
            "    adjudicated = _adjudicated_ok(rid, cv)\n"
            "    if adjudicated is not _NO_ADJUDICATION: return adjudicated\n",
        )
        if "KNOWN_CORRECT" in source:
            raise ValueError("unmigrated KNOWN_CORRECT reference remains")
    if "NON_NUMERIC" in source:
        if "NON_NUMERIC = set()" not in source:
            source, replacements = NON_NUMERIC_RE.subn(
                "NON_NUMERIC = set()  # all 67 questions remain in scope\n",
                source,
                count=1,
            )
            if replacements != 1:
                raise ValueError("could not replace NON_NUMERIC definition")
    source = source.replace(
        "mc_calc_qwen3-30b_updated_schema_det_smt_schema_fixed_run1",
        "latest/mc-qwen-30b-latest",
    )
    for old, new in sorted(
        RUN_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True
    ):
        source = source.replace(old, new)
    source = source.replace(
        "Violated Claims Caught by VeriFin",
        "Wrong Claims Caught by VeriFin (%)",
    )
    # The result artifacts do not embed the immutable Fin-o1 model ID. Their
    # directory names and earlier plotting labels disagree, so the public
    # notebook must use a size-neutral label until provenance is recovered.
    return (
        source.replace("Fin-o1-30B", "Fin-o1")
        .replace("Fino1 8B", "Fin-o1")
        .replace(r"Fino1\n8B", "Fin-o1")
    )


def migrate_markdown(source: str) -> str:
    source = source.replace(
        "the four questions without a numerical candidate",
        "the three questions without a parsed numerical candidate",
    )
    source = source.replace(
        "The present artifacts\nrepresent method-specific end-to-end outcomes; a same-candidate verifier claim\nrequires replaying VeriFin on the frozen baseline candidate manifest.",
        "All methods use the same frozen Claude Haiku 4.5 raw-answer text for each\nquestion. The baseline runner reparses that text, recovering numeric values in\n7 XBRLFiling and 6 FinanceBench cases where the source VeriFin artifact stored a\nnull `claimed_value`; parsing is therefore part of each evaluated method.",
    )
    return source


def migrate_notebook(path: Path) -> int:
    notebook = nbformat.read(path, as_version=4)
    changed = 0
    for cell in notebook.cells:
        if cell.cell_type == "code":
            migrated = migrate_source(cell.source)
        elif cell.cell_type == "markdown":
            migrated = migrate_markdown(cell.source)
        else:
            continue
        if migrated != cell.source:
            cell.source = migrated
            if cell.cell_type == "code":
                cell.outputs = []
                cell.execution_count = None
            changed += 1

    fixed_cells = {
        2: """## Across answer models (both datasets) — `tab:models`

All FinanceBench metrics use the complete 67-question population. Counts are
recomputed from per-question artifacts with candidate-specific adjudications.
GPT-5.5 has an auditable XBRLBench run; no FinanceBench GPT-5.5 artifact is
available and that entry must remain missing.""",
        4: CANONICAL_MODEL_CELL,
        5: """## Across all answer models — `tab:models-full`

Full outcome breakdown (TA/FA/TR/FR/AB) with precision, decision accuracy, and
coverage over all 600 XBRLBench and all 67 FinanceBench questions. The canonical
scorer is `scripts/paper_scoring.py`; FinanceBench GPT-5.5 remains unavailable.""",
    }
    for index, source in fixed_cells.items():
        cell = notebook.cells[index]
        if cell.source == source:
            continue
        cell.source = source
        if cell.cell_type == "code":
            cell.outputs = []
            cell.execution_count = None
        changed += 1

    tolerance_cells = [
        cell
        for cell in notebook.cells
        if cell.cell_type == "code"
        and (
            "run_safety_coverage" in cell.source
            or "safety_coverage_tolerance_sweep_points.csv" in cell.source
        )
    ]
    if len(tolerance_cells) != 1:
        raise ValueError(
            "expected exactly one tolerance-sweep replay cell; found "
            f"{len(tolerance_cells)}"
        )
    tolerance_cell = tolerance_cells[0]
    if tolerance_cell.source != FROZEN_TOLERANCE_CELL:
        tolerance_cell.source = FROZEN_TOLERANCE_CELL
        tolerance_cell.outputs = []
        tolerance_cell.execution_count = None
        changed += 1

    nbformat.validate(notebook)
    nbformat.write(notebook, path)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notebook", nargs="?", type=Path, default=DEFAULT_NOTEBOOK)
    args = parser.parse_args()
    changed = migrate_notebook(args.notebook)
    print(f"Updated {changed} code cells in {args.notebook}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
