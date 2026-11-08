"""Replay stored SMT obligations under a numerical-tolerance sweep.

This is deliberately narrower than a generic "four-threshold" sensitivity
figure.  The reported runs store enough information to vary the numerical
tolerance exactly, but they do not store calibrated concept, formula-authority,
or ambiguity scores.  The sweep therefore changes only the two named claim
bounds in each stored SMT program and re-solves the otherwise identical
obligation.
"""

from __future__ import annotations

import concurrent.futures
import json
import math
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Iterable

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D

try:
    from scripts import paper_scoring
except ImportError:  # Direct execution: ``python scripts/safety_....py``.
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import paper_scoring


RUNS = {
    # Same answer model in both panels; these are the current Qwen3-30B runs.
    "XBRLBench": "latest/mc-qwen-30b-latest",
    "FinanceBench": "latest/fb_qwen3-30b_updated2_det_smt_run3_new",
}
TOTALS = {"XBRLBench": 600, "FinanceBench": 67}
DATASET_KEYS = {"XBRLBench": "xbrlfiling", "FinanceBench": "financebench"}
MULTIPLIERS = (0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 25.0, 50.0, 100.0, 250.0, 1000.0)

_NUMBER = r"-?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
_CLAIM_BOUND = re.compile(
    rf"(\(assert\s+\(!\s+\(<=\s+\(-[^\n]+?\)\s+)({_NUMBER})"
    rf"(\)\s+:named\s+claim_(?:upper|lower)\)\))"
)
_OPTIONAL_QUERY = re.compile(r"\(get-unsat-core\)|\(get-model\)")

INK = "#17212B"
BLUE = "#28618F"
BLUE_DARK = "#173F60"
AMBER = "#D89B2B"
MUTED = "#5B6573"
GRID = "#D7DCE2"


def _resolve_root(root: Path | str | None = None) -> Path:
    candidates = []
    if root is not None:
        candidates.append(Path(root))
    candidates.extend((Path.cwd(), Path.cwd().parent, Path("/content/verifiqa")))
    for candidate in candidates:
        candidate = candidate.resolve()
        if (candidate / "results" / RUNS["XBRLBench"] / "results.jsonl").is_file():
            return candidate
    raise FileNotFoundError(
        "Could not locate the verifiqa repository and its reported result files."
    )


def _read_rows(root: Path, run: str) -> list[dict[str, Any]]:
    path = root / "results" / run / "results.jsonl"
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _policy_path(root: Path) -> Path:
    for relative_path in (
        "publication_assets_source/results/scoring_policy.json",
        "results/scoring_policy.json",
    ):
        candidate = root / relative_path
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"No canonical scoring policy found under {root}")


def _load_scoring_assets(root: Path) -> tuple[dict[str, Any], dict]:
    policy_path = _policy_path(root)
    policy = paper_scoring.load_policy(policy_path)
    manual_name = policy["candidate_correctness"].get(
        "manual_adjudications", "manual_adjudications.json"
    )
    adjudications = paper_scoring.load_manual_adjudications(
        policy_path.parent / manual_name
    )
    return policy, adjudications


def _candidate_correct(
    dataset: str,
    row: dict[str, Any],
    policy: dict[str, Any],
    adjudications: dict,
) -> bool | None:
    return paper_scoring.candidate_is_correct(
        row,
        DATASET_KEYS[dataset],
        policy,
        adjudications,
    )


def _scaled_smt(smtlib: str, multiplier: float) -> tuple[str, float]:
    matches = list(_CLAIM_BOUND.finditer(smtlib))
    if len(matches) != 2:
        raise ValueError(f"expected two named claim bounds, found {len(matches)}")
    base_tolerances = [float(match.group(2)) for match in matches]
    if not math.isclose(base_tolerances[0], base_tolerances[1], rel_tol=0.0, abs_tol=1e-8):
        raise ValueError(f"claim bounds disagree: {base_tolerances}")
    scaled = base_tolerances[0] * float(multiplier)
    rewritten = _CLAIM_BOUND.sub(
        lambda match: f"{match.group(1)}{scaled:.17g}{match.group(3)}",
        smtlib,
    )
    return _OPTIONAL_QUERY.sub("", rewritten), base_tolerances[0]


def _solve_one(
    z3_path: str,
    dataset: str,
    row: dict[str, Any],
    multiplier: float,
    policy: dict[str, Any],
    adjudications: dict,
) -> dict[str, Any]:
    smtlib, base_tolerance = _scaled_smt(row["smtlib"], multiplier)
    completed = subprocess.run(
        [z3_path, "-in"],
        input=smtlib,
        text=True,
        capture_output=True,
        timeout=15,
        check=False,
    )
    verdict = next(
        (
            line.strip()
            for line in completed.stdout.splitlines()
            if line.strip() in {"sat", "unsat", "unknown"}
        ),
        None,
    )
    if verdict is None:
        raise RuntimeError(
            f"Z3 returned no verdict for {row.get('id')}: "
            f"{completed.stderr.strip()[:240]}"
        )
    return {
        "Dataset": dataset,
        "Question ID": row.get("id") or row.get("financebench_id"),
        "Multiplier": float(multiplier),
        "Base tolerance": base_tolerance,
        "Solver verdict": verdict,
        "Candidate correct": _candidate_correct(
            dataset, row, policy, adjudications
        ),
        "Stored solver status": str(row.get("solver_status") or "").upper(),
    }


def replay_tolerance_sweep(
    root: Path | str | None = None,
    multipliers: Iterable[float] = MULTIPLIERS,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return aggregate curve points and question-level solver replay records."""

    root = _resolve_root(root)
    policy, adjudications = _load_scoring_assets(root)
    z3_path = shutil.which("z3")
    if not z3_path:
        raise FileNotFoundError(
            "The numerical-tolerance sweep requires the Z3 executable on PATH."
        )

    rows_by_dataset = {
        dataset: _read_rows(root, run)
        for dataset, run in RUNS.items()
    }
    for dataset, rows in rows_by_dataset.items():
        expected = TOTALS[dataset]
        if len(rows) != expected or len({row["id"] for row in rows}) != expected:
            raise AssertionError(
                f"{dataset}: expected {expected} unique rows, found {len(rows)}"
            )

    jobs = [
        (z3_path, dataset, row, float(multiplier))
        for dataset, rows in rows_by_dataset.items()
        for row in rows
        if row.get("smtlib")
        for multiplier in multipliers
    ]
    workers = min(12, max(2, os.cpu_count() or 2))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        replay_records = list(
            pool.map(
                lambda args: _solve_one(
                    *args, policy=policy, adjudications=adjudications
                ),
                jobs,
            )
        )
    replay = pd.DataFrame(replay_records)

    # The deployed point must reproduce every saved deterministic solver verdict.
    deployed = replay[replay["Multiplier"] == 1.0]
    mismatches = deployed[
        deployed["Solver verdict"].str.upper() != deployed["Stored solver status"]
    ]
    if not mismatches.empty:
        raise AssertionError(
            "The kappa=1 replay does not reproduce the stored run:\n"
            + mismatches.head().to_string(index=False)
        )

    points = []
    for dataset in RUNS:
        total = TOTALS[dataset]
        panel = replay[replay["Dataset"] == dataset]
        for multiplier in multipliers:
            subset = panel[panel["Multiplier"] == float(multiplier)]
            accepted = subset[subset["Solver verdict"] == "sat"]
            true_accepts = int((accepted["Candidate correct"] == True).sum())  # noqa: E712
            false_accepts = int(len(accepted) - true_accepts)
            accept_count = int(len(accepted))
            points.append(
                {
                    "Dataset": dataset,
                    "Tolerance multiplier": float(multiplier),
                    "Questions": total,
                    "SMT obligations": int(len(subset)),
                    "Accepted": accept_count,
                    "TA": true_accepts,
                    "FA": false_accepts,
                    "Correct-accept yield": 100.0 * true_accepts / total,
                    "False-accept risk": (
                        100.0 * false_accepts / accept_count
                        if accept_count
                        else float("nan")
                    ),
                }
            )
    points_df = pd.DataFrame(points)

    # Locks the paper's deployed operating point to the main results.
    deployed_expected = {
        "XBRLBench": {"TA": 304, "FA": 0, "Accepted": 304},
        "FinanceBench": {"TA": 24, "FA": 0, "Accepted": 24},
    }
    for dataset, expected in deployed_expected.items():
        row = points_df[
            (points_df["Dataset"] == dataset)
            & (points_df["Tolerance multiplier"] == 1.0)
        ].iloc[0]
        observed = {key: int(row[key]) for key in expected}
        if observed != expected:
            raise AssertionError((dataset, observed, expected))

    return points_df, replay


def _zero_fa_upper_95(accepted: int) -> float:
    """One-sided exact 95% binomial upper bound when zero events are observed."""

    return 100.0 * (1.0 - 0.05 ** (1.0 / accepted)) if accepted else 100.0


def plot_safety_coverage(
    points: pd.DataFrame,
    output_stem: Path | str,
) -> plt.Figure:
    """Plot correct-accept yield against selective false-accept risk."""

    with plt.rc_context(
        {
            "font.family": "serif",
            "font.serif": [
                "Times New Roman",
                "Times",
                "Liberation Serif",
                "DejaVu Serif",
            ],
            "font.size": 7.4,
            "axes.linewidth": 0.65,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "figure.dpi": 180,
            "savefig.dpi": 600,
        }
    ):
        fig, axes = plt.subplots(
            1,
            2,
            figsize=(7.08, 2.72),
            sharey=True,
        )

        for ax, dataset in zip(axes, RUNS):
            panel = points[points["Dataset"] == dataset].sort_values(
                "Tolerance multiplier"
            )
            x = panel["Correct-accept yield"].to_numpy()
            y = panel["False-accept risk"].to_numpy()

            ax.plot(x, y, color=BLUE, linewidth=1.25, zorder=3)
            ax.scatter(
                x,
                y,
                s=18,
                facecolor="white",
                edgecolor=BLUE,
                linewidth=0.8,
                zorder=4,
            )

            deployed = panel[panel["Tolerance multiplier"] == 1.0].iloc[0]
            default_x = float(deployed["Correct-accept yield"])
            default_y = float(deployed["False-accept risk"])
            default_upper = _zero_fa_upper_95(int(deployed["Accepted"]))
            ax.vlines(
                default_x,
                default_y,
                default_upper,
                color=MUTED,
                linewidth=0.85,
                linestyles=(0, (2, 2)),
                zorder=2,
            )
            ax.hlines(
                default_upper,
                default_x - 0.12,
                default_x + 0.12,
                color=MUTED,
                linewidth=0.85,
                zorder=2,
            )
            ax.scatter(
                [default_x],
                [default_y],
                marker="D",
                s=45,
                facecolor=BLUE,
                edgecolor=BLUE_DARK,
                linewidth=0.9,
                zorder=6,
            )
            ax.annotate(
                rf"deployed $\kappa=1$"
                + "\n"
                + f"FA=0/{int(deployed['Accepted'])}",
                (default_x, default_y),
                xytext=(5, 28) if dataset == "XBRLBench" else (-6, 6),
                textcoords="offset points",
                ha="left" if dataset == "XBRLBench" else "right",
                va="bottom",
                fontsize=6.7,
                color=BLUE_DARK,
                fontweight="bold",
            )
            ax.annotate(
                f"95% upper bound {default_upper:.1f}%",
                (default_x, default_upper),
                xytext=(4, 2),
                textcoords="offset points",
                ha="left",
                va="bottom",
                fontsize=6.2,
                color=MUTED,
            )

            nonzero = panel[panel["FA"] > 0]
            if not nonzero.empty:
                first = nonzero.iloc[0]
                ax.scatter(
                    [first["Correct-accept yield"]],
                    [first["False-accept risk"]],
                    marker="o",
                    s=27,
                    facecolor=AMBER,
                    edgecolor="#855E16",
                    linewidth=0.8,
                    zorder=6,
                )
                ax.annotate(
                    rf"first observed FA: $\kappa={first['Tolerance multiplier']:g}$",
                    (
                        first["Correct-accept yield"],
                        first["False-accept risk"],
                    ),
                    xytext=(5, 13) if dataset == "XBRLBench" else (-3, 17),
                    textcoords="offset points",
                    ha="left" if dataset == "XBRLBench" else "right",
                    va="bottom",
                    fontsize=6.4,
                    color="#855E16",
                )

            last = panel.iloc[-1]
            ax.annotate(
                rf"$\kappa={last['Tolerance multiplier']:g}$",
                (
                    last["Correct-accept yield"],
                    last["False-accept risk"],
                ),
                xytext=(-4, -5),
                textcoords="offset points",
                ha="right",
                va="top",
                fontsize=6.3,
                color=BLUE_DARK,
            )

            ax.set_title(
                f"{dataset} ($n={TOTALS[dataset]}$)",
                loc="left",
                fontsize=8.2,
                fontweight="bold",
                color=INK,
                pad=7,
            )
            ax.set_xlabel(
                r"Correct-accept yield, $\mathrm{TA}/N$ (\%)",
                fontsize=7.1,
                color=INK,
                labelpad=5,
            )
            ax.grid(color=GRID, linewidth=0.45, alpha=0.85, zorder=1)
            ax.axhline(0, color="#8C96A3", linewidth=0.65, zorder=2)
            ax.tick_params(
                axis="both",
                labelsize=6.8,
                colors=MUTED,
                width=0.5,
                length=2.5,
            )
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color("#98A1AC")
            ax.spines["bottom"].set_color("#98A1AC")

            x_min = math.floor(float(panel["Correct-accept yield"].min()) - 1.0)
            x_max = math.ceil(float(panel["Correct-accept yield"].max()) + 1.0)
            ax.set_xlim(x_min, x_max)

        axes[0].set_ylabel(
            r"False-accept risk, $\mathrm{FA}/(\mathrm{TA}+\mathrm{FA})$ (\%)",
            fontsize=7.1,
            color=INK,
            labelpad=5,
        )
        axes[0].set_ylim(-1.6, 36.5)
        axes[0].set_yticks([0, 5, 10, 15, 20, 25, 30, 35])

        handles = [
            Line2D(
                [0],
                [0],
                color=BLUE,
                marker="o",
                markerfacecolor="white",
                markeredgecolor=BLUE,
                linewidth=1.15,
                markersize=4,
                label=r"tolerance sweep ($\kappa\times$ base)",
            ),
            Line2D(
                [0],
                [0],
                linestyle="none",
                marker="D",
                markerfacecolor=BLUE,
                markeredgecolor=BLUE_DARK,
                markersize=5,
                label=r"deployed $\kappa=1$",
            ),
            Line2D(
                [0],
                [0],
                color=MUTED,
                linestyle=(0, (2, 2)),
                linewidth=0.9,
                label="deployed-point one-sided exact 95% upper bound",
            ),
        ]
        fig.legend(
            handles=handles,
            loc="upper center",
            bbox_to_anchor=(0.5, 1.01),
            ncol=3,
            frameon=False,
            handletextpad=0.45,
            columnspacing=1.35,
            fontsize=6.8,
        )
        fig.subplots_adjust(
            left=0.09,
            right=0.993,
            bottom=0.245,
            top=0.79,
            wspace=0.18,
        )

        output_stem = Path(output_stem)
        output_stem.parent.mkdir(parents=True, exist_ok=True)
        export_options = {
            "bbox_inches": "tight",
            "pad_inches": 0.02,
            "facecolor": "white",
        }
        fig.savefig(f"{output_stem}.pdf", **export_options)
        fig.savefig(f"{output_stem}.svg", **export_options)
        fig.savefig(f"{output_stem}.png", dpi=600, **export_options)
        return fig


def run_safety_coverage(
    root: Path | str | None = None,
    *,
    show: bool = True,
) -> tuple[pd.DataFrame, plt.Figure]:
    root = _resolve_root(root)
    points, replay = replay_tolerance_sweep(root)
    output_stem = root / "figures" / "safety_coverage_tolerance_sweep"
    points.to_csv(f"{output_stem}_points.csv", index=False)
    figure = plot_safety_coverage(points, output_stem)
    display_columns = [
        "Dataset",
        "Tolerance multiplier",
        "Accepted",
        "TA",
        "FA",
        "Correct-accept yield",
        "False-accept risk",
    ]
    print(points[display_columns].to_string(index=False, float_format=lambda x: f"{x:.2f}"))
    if show:
        plt.show()
    return points, figure


if __name__ == "__main__":
    run_safety_coverage()
