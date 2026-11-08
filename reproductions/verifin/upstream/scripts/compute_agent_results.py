#!/usr/bin/env python3
"""Score solver SAT/UNSAT verdicts against gold answers from results.jsonl."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from verifiqa.eval.metrics import numeric_answer_accuracy
from verifiqa.formulas.evaluator import evaluate_formula


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute solver SAT/UNSAT accuracy from agent results.jsonl."
    )
    parser.add_argument(
        "results_jsonl",
        nargs="?",
        type=Path,
        help="Path to results.jsonl. If omitted, uses latest results/*/results.jsonl.",
    )
    parser.add_argument(
        "--write-summary",
        action="store_true",
        help="Write summary.json next to results.jsonl.",
    )
    parser.add_argument(
        "--write-annotated",
        type=Path,
        default=None,
        help="Optional path for an annotated JSONL copy with correctness fields.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON only.",
    )
    parser.add_argument(
        "--answer-field",
        default="answer",
        help="Row field containing the answer being verified (default: answer).",
    )
    parser.add_argument(
        "--gold-field",
        default="auto",
        help="Row field containing the gold answer (default: auto: gold_answer then raw_answer).",
    )
    args = parser.parse_args()

    path = args.results_jsonl or latest_results_path()
    rows = load_rows(path)
    for row in rows:
        annotate_row_performance(row, answer_field=args.answer_field, gold_field=args.gold_field)
    summary = summarize_rows(rows)

    if args.write_summary:
        summary_path = path.with_name("summary.json")
        summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        summary["summary_path"] = str(summary_path)

    if args.write_annotated is not None:
        write_jsonl(args.write_annotated, rows)
        summary["annotated_path"] = str(args.write_annotated)

    if args.json:
        print(json.dumps({"results_path": str(path), "summary": summary}, indent=2))
    else:
        print_report(path, summary, rows)


def latest_results_path() -> Path:
    candidates = [path for path in (ROOT / "results").glob("*/results.jsonl") if path.is_file()]
    if not candidates:
        raise SystemExit("No results/*/results.jsonl files found")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def load_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise SystemExit(f"Results file not found: {path}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def annotate_row_performance(
    row: dict[str, Any],
    *,
    answer_field: str = "answer",
    gold_field: str = "auto",
) -> None:
    answer = str(row.get(answer_field) or "")
    gold = gold_answer(row, gold_field)
    row["gold_answer"] = gold
    row["answer_matches_gold"] = (
        numeric_answer_accuracy(answer, str(gold)) if gold not in (None, "") else None
    )

    computed, computed_error = recompute_value(row)
    row["computed_value"] = computed
    row["computed_error"] = computed_error

    actual_solver_status = solver_status(row)
    row["actual_solver_status"] = actual_solver_status
    row["expected_solver_status"] = expected_solver_status(row)
    row["verifier_decision"] = solver_decision(actual_solver_status)
    if row["answer_matches_gold"] is None:
        row["solver_correct"] = None
        row["solver_correct_reason"] = "no_gold_answer"
        return

    if actual_solver_status not in {"SAT", "UNSAT"}:
        row["solver_correct"] = None
        row["solver_correct_reason"] = "no_solver_verdict"
        row["decision_correct"] = None
        row["decision_correct_reason"] = "no_solver_verdict"
        row["verified_correct"] = None
        return

    correct = actual_solver_status == row["expected_solver_status"]
    row["solver_correct"] = correct
    row["solver_correct_reason"] = (
        "solver_status_matches_gold_expectation"
        if correct
        else "solver_status_differs_from_gold_expectation"
    )

    # Backward-compatible aliases used by older summaries.
    row["decision_correct"] = correct
    row["decision_correct_reason"] = row["solver_correct_reason"]
    row["verified_correct"] = correct if actual_solver_status == "SAT" else None


def gold_answer(row: dict[str, Any], gold_field: str) -> Any:
    if gold_field != "auto":
        return row.get(gold_field)
    for field in ("gold_answer", "raw_answer", "reference_answer", "gold"):
        value = row.get(field)
        if value not in (None, ""):
            return value
    return None


def expected_solver_status(row: dict[str, Any]) -> str | None:
    if row.get("answer_matches_gold") is True:
        return "SAT"
    if row.get("answer_matches_gold") is False:
        return "UNSAT"
    return None


def solver_status(row: dict[str, Any]) -> str:
    status = str(row.get("solver_status") or "").upper()
    if status in {"SAT", "UNSAT"}:
        return status
    # Agent status names are aliases for solver verdicts.
    row_status = str(row.get("status") or "").upper()
    if row_status == "VERIFIED":
        return "SAT"
    if row_status == "VIOLATED":
        return "UNSAT"
    return status or row_status or "UNKNOWN"


def solver_decision(status: str) -> str:
    if status == "SAT":
        return "accept"
    if status == "UNSAT":
        return "reject"
    return "abstain"


def recompute_value(row: dict[str, Any]) -> tuple[float | None, str]:
    formula = row.get("formula") or ""
    facts = row.get("facts") or {}
    if not formula or not facts:
        return None, "missing_formula_or_facts"
    try:
        values = {name: fact["value"] for name, fact in facts.items()}
        return float(evaluate_formula(formula, values)), ""
    except Exception as exc:
        return None, f"{type(exc).__name__}:{exc}"


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("status") or "")
        counts[status] = counts.get(status, 0) + 1

    gold_rows = [row for row in rows if row.get("answer_matches_gold") is not None]
    sat_rows = [
        row for row in rows
        if solver_status(row) == "SAT" and row.get("expected_solver_status") is not None
    ]
    unsat_rows = [
        row for row in rows
        if solver_status(row) == "UNSAT" and row.get("expected_solver_status") is not None
    ]
    solver_rows = sat_rows + unsat_rows

    sat_correct = sum(1 for row in sat_rows if row.get("expected_solver_status") == "SAT")
    sat_incorrect = sum(1 for row in sat_rows if row.get("expected_solver_status") != "SAT")
    unsat_correct = sum(1 for row in unsat_rows if row.get("expected_solver_status") == "UNSAT")
    unsat_incorrect = sum(1 for row in unsat_rows if row.get("expected_solver_status") != "UNSAT")
    correct_solver_verdicts = sum(1 for row in solver_rows if row.get("solver_correct") is True)
    incorrect_solver_verdicts = sum(1 for row in solver_rows if row.get("solver_correct") is False)
    accuracy = _safe_div(correct_solver_verdicts, len(solver_rows))

    return {
        "total": len(rows),
        "gold_evaluable": len(gold_rows),
        "all_verifications": len(solver_rows),
        "correct_verifications": correct_solver_verdicts,
        "incorrect_verifications": incorrect_solver_verdicts,
        "solver_verdicts": len(solver_rows),
        "correct_solver_verdicts": correct_solver_verdicts,
        "incorrect_solver_verdicts": incorrect_solver_verdicts,
        "expected_sat": sum(1 for row in gold_rows if row.get("expected_solver_status") == "SAT"),
        "expected_unsat": sum(1 for row in gold_rows if row.get("expected_solver_status") == "UNSAT"),
        "actual_sat": len(sat_rows),
        "actual_unsat": len(unsat_rows),
        "verified": counts.get("VERIFIED", 0),
        "violated": counts.get("VIOLATED", 0),
        "abstain": counts.get("ABSTAIN", 0),
        "unverified_formula": counts.get("UNVERIFIED_FORMULA", 0),
        "verified_correct": sat_correct,
        "verified_incorrect": sat_incorrect,
        "violated_correct": unsat_correct,
        "violated_incorrect": unsat_incorrect,
        "correct_decisions": correct_solver_verdicts,
        "incorrect_decisions": incorrect_solver_verdicts,
        "accuracy": round(accuracy, 4),
        "solver_accuracy": round(accuracy, 4),
        "coverage": round(_safe_div(len(solver_rows), len(gold_rows)), 4),
        "decision_accuracy": round(accuracy, 4),
        "overall_accuracy": round(_safe_div(correct_solver_verdicts, len(gold_rows)), 4),
        "sat_precision": round(_safe_div(sat_correct, len(sat_rows)), 4),
        "unsat_precision": round(_safe_div(unsat_correct, len(unsat_rows)), 4),
        "verification_precision": round(_safe_div(sat_correct, len(sat_rows)), 4),
        "violation_precision": round(_safe_div(unsat_correct, len(unsat_rows)), 4),
    }


def print_report(path: Path, summary: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    print(f"Results: {path}")
    print(json.dumps(summary, indent=2))

    incorrect = [row for row in rows if row.get("solver_correct") is False]
    if incorrect:
        print("\nIncorrect solver verdicts:")
        for row in incorrect:
            print(
                "- {id} actual={actual} expected={expected} status={status} "
                "metric={metric} answer={answer!r} gold={gold!r}".format(
                    id=row.get("id"),
                    actual=row.get("actual_solver_status"),
                    expected=row.get("expected_solver_status"),
                    status=row.get("status"),
                    metric=row.get("metric"),
                    answer=row.get("answer"),
                    gold=row.get("gold_answer"),
                )
            )


def _safe_div(num: int, den: int) -> float:
    return float(num) / float(den) if den else 0.0


if __name__ == "__main__":
    main()
