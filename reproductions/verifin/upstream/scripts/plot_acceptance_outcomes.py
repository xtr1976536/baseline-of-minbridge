"""Plot the full-denominator acceptance outcomes used in the ICAIF paper.

The figure retains every benchmark question: N=600 for XBRLBench and N=67
for FinanceBench. A missing numerical candidate is therefore part of the
"not admitted" remainder rather than being removed from the denominator.

The four baselines use the canonical one-pool protocol: each evaluates the
same raw answer text produced by the Claude Haiku answer-generator run. A
baseline may reparse that text to a different ``claimed_value``, so the chart
reports the stored end-to-end decisions rather than claiming identical parsed
candidates. Candidate correctness and all manual adjudications come from the
canonical paper scorer and scoring policy.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch
from matplotlib.ticker import PercentFormatter

try:
    from scripts import paper_scoring
except ImportError:  # Direct execution: ``python scripts/plot_....py``.
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import paper_scoring


METHODS = (
    "Raw LLM",
    "LLM judge",
    "Judge + formula",
    "PoT",
    "VeriFin",
)

RUNS = {
    "XBRLBench": {
        "Raw LLM": {
            "group": "baselines",
            "run": "direct-llm",
            "source_path": "results/onepool/xbrl_none",
        },
        "LLM judge": {
            "group": "baselines",
            "run": "llm-judge",
            "source_path": "results/onepool/xbrl_judge",
        },
        "Judge + formula": {
            "group": "baselines",
            "run": "judge-plus-formula",
            "source_path": "results/onepool/xbrl_judge_formula",
        },
        "PoT": {
            "group": "baselines",
            "run": "program-of-thought",
            "source_path": "results/onepool/xbrl_pot",
        },
        "VeriFin": {
            "group": "answer_models",
            "run": "claude-haiku-4.5",
            "source_path": "results/mc_calc_detsmt_v2_haiku",
        },
    },
    "FinanceBench": {
        "Raw LLM": {
            "group": "baselines",
            "run": "direct-llm",
            "source_path": "results/onepool/fb_none",
        },
        "LLM judge": {
            "group": "baselines",
            "run": "llm-judge",
            "source_path": "results/onepool/fb_judge",
        },
        "Judge + formula": {
            "group": "baselines",
            "run": "judge-plus-formula",
            "source_path": "results/onepool/fb_judge_formula",
        },
        "PoT": {
            "group": "baselines",
            "run": "program-of-thought",
            "source_path": "results/onepool/fb_pot",
        },
        "VeriFin": {
            "group": "answer_models",
            "run": "claude-haiku-4.5",
            "source_path": "results/fb_detsmt_v2_haiku",
        },
    },
}

DATASET_KEYS = {"XBRLBench": "xbrlfiling", "FinanceBench": "financebench"}
DATASET_TOTALS = {"XBRLBench": 600, "FinanceBench": 67}

EXPECTED_COUNTS = {
    ("XBRLBench", "Raw LLM"): (508, 92, 0),
    ("XBRLBench", "LLM judge"): (195, 26, 379),
    ("XBRLBench", "Judge + formula"): (480, 75, 45),
    ("XBRLBench", "PoT"): (444, 6, 150),
    ("XBRLBench", "VeriFin"): (455, 0, 145),
    ("FinanceBench", "Raw LLM"): (46, 18, 3),
    ("FinanceBench", "LLM judge"): (22, 7, 38),
    ("FinanceBench", "Judge + formula"): (34, 13, 20),
    ("FinanceBench", "PoT"): (40, 4, 23),
    ("FinanceBench", "VeriFin"): (28, 0, 39),
}

CORRECT = "#286A78"
INCORRECT = "#D97706"
INCORRECT_EDGE = "#8D4A00"
NOT_ADMITTED = "#E4E7EB"
INK = "#17212B"
MUTED = "#5B6573"
OURS_BG = "#E7F3F1"
GRID = "#CBD0D6"

FIGURE_WIDTH_IN = 7.08
FIGURE_HEIGHT_IN = 3.05


def _policy_path(root: Path) -> Path | None:
    for relative_path in (
        "publication_assets_source/results/scoring_policy.json",
        "results/scoring_policy.json",
    ):
        candidate = root / relative_path
        if candidate.is_file():
            return candidate
    return None


def _resolve_root(root: Path | None = None) -> Path:
    candidates = []
    if root is not None:
        candidates.append(Path(root))
    candidates.append(Path(__file__).resolve().parents[1])
    cwd = Path.cwd()
    candidates.extend((cwd, *cwd.parents, cwd / "verifiqa"))
    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.expanduser().resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if (
            (candidate / "scripts/paper_scoring.py").is_file()
            and _policy_path(candidate) is not None
        ):
            return candidate
    raise FileNotFoundError(
        "Could not locate scripts/paper_scoring.py and the canonical scoring "
        "policy. Run from a private or public VeriFin repository, or pass its "
        "root to main()."
    )


def _load_scoring_assets(root: Path) -> tuple[dict, dict]:
    policy_path = _policy_path(root)
    if policy_path is None:
        raise FileNotFoundError(f"No canonical scoring policy found under {root}")
    policy = paper_scoring.load_policy(policy_path)
    manual_name = policy["candidate_correctness"].get(
        "manual_adjudications", "manual_adjudications.json"
    )
    adjudications = paper_scoring.load_manual_adjudications(
        policy_path.parent / manual_name
    )
    return policy, adjudications


def _acceptance_counts(
    root: Path,
    dataset_label: str,
    dataset_key: str,
    run: dict,
    denominator: int,
    expected_ids: set[str],
    policy: dict,
    adjudications: dict,
) -> tuple[int, int, int]:
    group = run["group"]
    run_name = run["run"]
    run_spec = policy["canonical_runs"][dataset_key][group][run_name]
    policy_source = run_spec.get("source_path")
    if policy_source != run["source_path"]:
        raise AssertionError(
            f"{dataset_label}/{run_name}: policy source {policy_source!r} "
            f"does not match the figure source {run['source_path']!r}."
        )

    path = root / policy_source / "results.jsonl"
    rows = paper_scoring.load_jsonl(path)
    paper_scoring.validate_run_ids(
        rows, expected_ids, dataset_key, run_name
    )
    counts = paper_scoring.score_rows(
        rows, dataset_key, policy, adjudications
    )
    if sum(counts.values()) != denominator:
        raise AssertionError(
            f"{dataset_label}/{run_name}: outcomes do not sum to N."
        )
    declared = run_spec.get("counts")
    if counts != declared:
        raise AssertionError(
            f"{dataset_label}/{run_name}: canonical scorer returned {counts}, "
            f"but the policy declares {declared}."
        )

    return (
        counts["TA"],
        counts["FA"],
        counts["TR"] + counts["FR"] + counts["AB"],
    )


def load_acceptance_outcomes(root: Path) -> pd.DataFrame:
    policy, adjudications = _load_scoring_assets(root)
    records: list[dict] = []
    for dataset, runs in RUNS.items():
        dataset_key = DATASET_KEYS[dataset]
        dataset_spec = policy["datasets"][dataset_key]
        denominator = dataset_spec["denominator"]
        if denominator != DATASET_TOTALS[dataset]:
            raise AssertionError(
                f"{dataset}: policy denominator {denominator} does not match "
                f"the figure denominator {DATASET_TOTALS[dataset]}."
            )
        dataset_rows = paper_scoring.load_jsonl(
            root / dataset_spec["source_path"]
        )
        expected_ids = paper_scoring.validate_dataset_ids(
            dataset_rows, dataset_key, dataset_spec
        )
        for method in METHODS:
            counts = _acceptance_counts(
                root,
                dataset,
                dataset_key,
                runs[method],
                denominator,
                expected_ids,
                policy,
                adjudications,
            )
            expected = EXPECTED_COUNTS[(dataset, method)]
            if counts != expected:
                raise AssertionError(
                    f"{dataset}/{method}: observed {counts}, expected {expected}. "
                    "Re-audit the paper counts before regenerating the figure."
                )
            records.append(
                {
                    "Dataset": dataset,
                    "Method": method,
                    "Correct accepted": counts[0],
                    "Incorrect accepted": counts[1],
                    "Not admitted": counts[2],
                    "Questions": denominator,
                }
            )

    outcomes = pd.DataFrame.from_records(records)
    totals = outcomes[
        ["Correct accepted", "Incorrect accepted", "Not admitted"]
    ].sum(axis=1)
    if not totals.equals(outcomes["Questions"]):
        raise AssertionError("At least one plotted row does not sum to N.")
    return outcomes


def make_figure(
    outcomes: pd.DataFrame,
    output_stem: Path,
) -> plt.Figure:
    with plt.rc_context(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [
                "Arial",
                "Helvetica Neue",
                "Helvetica",
                "DejaVu Sans",
            ],
            "font.size": 8.0,
            "axes.linewidth": 0.7,
            "hatch.linewidth": 0.65,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "pdf.compression": 9,
            "svg.fonttype": "none",
            "figure.dpi": 180,
            "savefig.dpi": 1200,
            "text.antialiased": True,
        }
    ):
        figure, axes = plt.subplots(
            1,
            2,
            figsize=(FIGURE_WIDTH_IN, FIGURE_HEIGHT_IN),
            sharex=True,
            sharey=True,
            gridspec_kw={"wspace": 0.105},
        )

        for panel_index, (axis, dataset) in enumerate(
            zip(axes, ("XBRLBench", "FinanceBench"))
        ):
            panel = (
                outcomes.loc[outcomes["Dataset"] == dataset]
                .set_index("Method")
                .reindex(METHODS)
            )
            denominator = int(panel["Questions"].iloc[0])
            y_positions = np.arange(len(METHODS))
            correct = panel["Correct accepted"].to_numpy(dtype=int)
            incorrect = panel["Incorrect accepted"].to_numpy(dtype=int)
            not_admitted = panel["Not admitted"].to_numpy(dtype=int)
            correct_pct = 100.0 * correct / denominator
            incorrect_pct = 100.0 * incorrect / denominator
            not_admitted_pct = 100.0 * not_admitted / denominator
            accepted_pct = correct_pct + incorrect_pct

            our_index = METHODS.index("VeriFin")
            axis.axhspan(
                our_index - 0.45,
                our_index + 0.45,
                color=OURS_BG,
                zorder=0,
            )
            axis.barh(
                y_positions,
                np.full(len(METHODS), 100.0),
                height=0.58,
                color=NOT_ADMITTED,
                edgecolor="white",
                linewidth=0.45,
                zorder=2,
            )
            axis.barh(
                y_positions,
                correct_pct,
                height=0.58,
                color=CORRECT,
                edgecolor="white",
                linewidth=0.45,
                zorder=3,
            )
            axis.barh(
                y_positions,
                incorrect_pct,
                left=correct_pct,
                height=0.58,
                color=INCORRECT,
                edgecolor=INCORRECT_EDGE,
                linewidth=0.45,
                hatch="////",
                zorder=4,
            )

            for row_index, (
                true_accepts,
                false_accepts,
                remainder,
                true_accept_pct,
                false_accept_pct,
                remainder_pct,
                total_accept_pct,
            ) in enumerate(
                zip(
                    correct,
                    incorrect,
                    not_admitted,
                    correct_pct,
                    incorrect_pct,
                    not_admitted_pct,
                    accepted_pct,
                )
            ):
                axis.text(
                    true_accept_pct / 2.0,
                    row_index,
                    f"{true_accepts}",
                    ha="center",
                    va="center",
                    fontsize=7.35,
                    fontweight="bold" if row_index == our_index else "normal",
                    color="white",
                    zorder=5,
                )

                if false_accepts > 0:
                    if total_accept_pct >= 94.0:
                        axis.text(
                            true_accept_pct + false_accept_pct / 2.0,
                            row_index,
                            f"FA={false_accepts}",
                            ha="center",
                            va="center",
                            fontsize=6.75,
                            fontweight="bold",
                            color="white",
                            zorder=6,
                        )
                    else:
                        axis.annotate(
                            f"FA={false_accepts}",
                            xy=(
                                true_accept_pct + false_accept_pct / 2.0,
                                row_index,
                            ),
                            xytext=(
                                min(total_accept_pct + 1.35, 97.0),
                                row_index,
                            ),
                            ha="left",
                            va="center",
                            fontsize=6.65,
                            fontweight="bold",
                            color=INCORRECT_EDGE,
                            arrowprops={
                                "arrowstyle": "-",
                                "color": INCORRECT_EDGE,
                                "lw": 0.55,
                                "shrinkA": 1.0,
                                "shrinkB": 1.0,
                            },
                            zorder=6,
                        )
                else:
                    axis.text(
                        min(true_accept_pct + 1.35, 94.0),
                        row_index,
                        "FA=0",
                        ha="left",
                        va="center",
                        fontsize=6.9,
                        fontweight="bold",
                        color=INCORRECT_EDGE,
                        zorder=6,
                    )

                if remainder_pct >= 18.0:
                    axis.text(
                        98.2,
                        row_index,
                        f"{remainder}",
                        ha="right",
                        va="center",
                        fontsize=7.0,
                        color=MUTED,
                        zorder=5,
                    )

            axis.set_title(
                f"{dataset}  ($n={denominator}$)",
                loc="left",
                fontsize=8.8,
                fontweight="bold",
                color=INK,
                pad=6.0,
            )
            axis.set_xlim(0.0, 100.0)
            axis.set_xticks((0, 25, 50, 75, 100))
            axis.xaxis.set_major_formatter(
                PercentFormatter(xmax=100, decimals=0)
            )
            axis.grid(
                axis="x",
                color=GRID,
                linewidth=0.45,
                alpha=0.82,
                zorder=1,
            )
            axis.set_axisbelow(True)
            axis.tick_params(
                axis="x",
                length=2.5,
                width=0.6,
                colors=MUTED,
                labelsize=7.15,
            )
            axis.tick_params(axis="y", length=0, pad=5.0)
            axis.spines[["top", "right", "left"]].set_visible(False)
            axis.spines["bottom"].set_color("#AEB5BE")
            if panel_index == 0:
                axis.set_yticks(
                    y_positions,
                    METHODS,
                    fontsize=7.55,
                    color=INK,
                )
                for tick, method in zip(axis.get_yticklabels(), METHODS):
                    if method == "VeriFin":
                        tick.set_color(CORRECT)
                        tick.set_fontweight("bold")

        axes[0].invert_yaxis()

        figure.legend(
            handles=(
                Patch(
                    facecolor=CORRECT,
                    edgecolor="none",
                    label="Correct accepted",
                ),
                Patch(
                    facecolor=INCORRECT,
                    edgecolor=INCORRECT_EDGE,
                    linewidth=0.45,
                    hatch="////",
                    label="Incorrect accepted (FA)",
                ),
                Patch(
                    facecolor=NOT_ADMITTED,
                    edgecolor="none",
                    label="Not admitted",
                ),
            ),
            loc="upper center",
            bbox_to_anchor=(0.535, 0.985),
            ncol=3,
            frameon=False,
            fontsize=7.35,
            handlelength=1.45,
            columnspacing=1.30,
        )
        figure.supxlabel(
            "Share of all benchmark questions",
            x=0.56,
            y=0.035,
            fontsize=7.8,
            color=INK,
        )
        figure.subplots_adjust(
            left=0.143,
            right=0.995,
            top=0.80,
            bottom=0.205,
        )

        output_stem = Path(output_stem)
        output_stem.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(
            output_stem.with_suffix(".pdf"),
            facecolor="white",
        )
        figure.savefig(
            output_stem.with_suffix(".svg"),
            facecolor="white",
        )
        figure.savefig(
            output_stem.with_suffix(".png"),
            dpi=1200,
            facecolor="white",
        )
        return figure


def main(
    root: Path | None = None,
    *,
    show: bool = True,
) -> tuple[pd.DataFrame, plt.Figure]:
    resolved_root = _resolve_root(root)
    outcomes = load_acceptance_outcomes(resolved_root)
    output_stem = resolved_root / "figures" / "acceptance_outcomes"
    figure = make_figure(outcomes, output_stem)
    outcomes.to_csv(
        resolved_root / "figures" / "acceptance_outcomes_data.csv",
        index=False,
    )
    print(outcomes.to_string(index=False))
    print(f"Saved {output_stem.with_suffix('.pdf')}")
    print(f"Saved {output_stem.with_suffix('.svg')}")
    print(f"Saved {output_stem.with_suffix('.png')}")
    return outcomes, figure


if __name__ == "__main__":
    main()
