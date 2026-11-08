#!/usr/bin/env python3
"""Rebuild the compact, publication-facing verification metrics notebook."""

from __future__ import annotations

import argparse
from pathlib import Path

import nbformat


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "notebooks/verification_key_metrics.ipynb"


def build_notebook() -> nbformat.NotebookNode:
    cells = [
        nbformat.v4.new_markdown_cell(
            """# VeriFin paper metrics

This notebook is the compact, executable audit companion for the paper. It
uses the complete 600-question XBRLBench and 67-question FinanceBench
populations, recomputes outcomes from per-question results, and applies only
candidate-specific manual adjudications. `scripts/paper_scoring.py` is the
canonical implementation."""
        ),
        nbformat.v4.new_markdown_cell("## Load the locked policy and artifacts"),
        nbformat.v4.new_code_cell(
            """from pathlib import Path
import json
import sys

import pandas as pd

ROOT = Path.cwd()
if not (ROOT / "results").exists() and (ROOT.parent / "results").exists():
    ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.paper_scoring import (
    load_jsonl,
    load_manual_adjudications,
    load_policy,
    score_all,
    validate_dataset_ids,
)

policy_path = ROOT / "results/scoring_policy.json"
if not policy_path.is_file():
    policy_path = ROOT / "publication_assets_source/results/scoring_policy.json"
policy = load_policy(policy_path)
adjudications = load_manual_adjudications(
    policy_path.parent / policy["candidate_correctness"]["manual_adjudications"]
)
scored = pd.DataFrame(score_all(ROOT, policy, adjudications))
scored"""
        ),
        nbformat.v4.new_markdown_cell("## Confirm dataset grain and denominators"),
        nbformat.v4.new_code_cell(
            """dataset_profile = []
for dataset_key, spec in policy["datasets"].items():
    rows = load_jsonl(ROOT / spec["source_path"])
    ids = validate_dataset_ids(rows, dataset_key, spec)
    dataset_profile.append({
        "dataset": dataset_key,
        "rows": len(rows),
        "unique_ids": len(ids),
        "denominator": spec["denominator"],
    })
dataset_profile = pd.DataFrame(dataset_profile)
assert dataset_profile["rows"].tolist() == [600, 67]
assert (dataset_profile["rows"] == dataset_profile["unique_ids"]).all()
dataset_profile"""
        ),
        nbformat.v4.new_markdown_cell("## Recompute the paper outcome table"),
        nbformat.v4.new_code_cell(
            """columns = ["dataset", "group", "run", "TA", "FA", "TR", "FR", "AB"]
outcomes = scored[columns].copy()
available = outcomes.dropna(subset=["TA"]).copy()
assert ((available[["TA", "FA", "TR", "FR", "AB"]].sum(axis=1))
        == available["dataset"].map({"xbrlfiling": 600, "financebench": 67})).all()

metrics_path = ROOT / "results/paper_metrics.csv"
if not metrics_path.is_file():
    # The private working tree keeps release-only support files in the
    # publication staging area; a built public release places this at results/.
    metrics_path = ROOT / "publication_assets_source/results/paper_metrics.csv"
frozen = pd.read_csv(metrics_path)
frozen_available = frozen.dropna(subset=["TA"]).copy()
reconciled = available.merge(
    frozen_available,
    on=["dataset", "group", "run", "TA", "FA", "TR", "FR", "AB"],
    how="outer",
    indicator=True,
)
assert (reconciled["_merge"] == "both").all()
assert ((frozen["dataset"] == "financebench")
        & (frozen["run"] == "gpt-5.5")
        & frozen["TA"].isna()).sum() == 1
frozen"""
        ),
        nbformat.v4.new_markdown_cell("## Headline safety comparison"),
        nbformat.v4.new_code_cell(
            """headline = frozen[frozen["group"].isin(["answer_models", "baselines"])].copy()
verifin_available = headline[headline["group"] == "answer_models"].dropna(subset=["FA"])
assert (verifin_available["FA"] == 0).all()

headline[[
    "dataset", "group", "run", "n", "TA", "FA", "TR", "FR", "AB",
    "precision_pct", "decision_accuracy_pct", "coverage_pct",
]].reset_index(drop=True)"""
        ),
        nbformat.v4.new_markdown_cell(
            """## Candidate-specific adjudication audit

The entries below normalize units or composite targets. They do **not** make an
arbitrary candidate correct merely because its question ID is listed. The
AMCOR restructuring question admits both the literal gold percentage and the
paper's grounded-dollar normalization; its caveat should remain visible."""
        ),
        nbformat.v4.new_code_cell(
            """manual_document = json.loads(
    (policy_path.parent / policy["candidate_correctness"]["manual_adjudications"])
    .read_text(encoding="utf-8")
)
manual_review = pd.DataFrame([
    {
        "id": row["id"],
        "allowed_targets": ", ".join(
            f"{target['value']:g} {target['unit']}" for target in row["allowed_targets"]
        ),
        "reason": row["reason"],
        "caveat": row.get("caveat", ""),
    }
    for row in manual_document["records"]
])
manual_review"""
        ),
        nbformat.v4.new_markdown_cell("## Known artifact gaps"),
        nbformat.v4.new_code_cell(
            """gaps = pd.DataFrame([
    {
        "artifact": "FinanceBench / GPT-5.5",
        "status": "missing",
        "publication treatment": "Do not infer or manually enter per-question results.",
    },
    {
        "artifact": "Fin-o1 checkpoint identity",
        "status": "not embedded in result files",
        "publication treatment": "Use identity-pending label until the immutable checkpoint is recovered.",
    },
    {
        "artifact": "XBRLBench annotation license",
        "status": "author choice pending",
        "publication treatment": "Add the chosen dataset license before public redistribution.",
    },
])
gaps"""
        ),
    ]
    notebook = nbformat.v4.new_notebook(cells=cells)
    notebook.metadata["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    notebook.metadata["language_info"] = {"name": "python", "version": "3"}
    nbformat.validate(notebook)
    return notebook


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    notebook = build_notebook()
    nbformat.write(notebook, args.output)
    print(f"Wrote {len(notebook.cells)} cells to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
