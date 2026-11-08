"""Per-model confusion-matrix + metrics table for verifier runs.

Reads one or more results.jsonl files (one per model / config) and prints a
side-by-side table:

    precision | catch-rate | accuracy | abstention | false-accepts

Confusion buckets (the paper's soundness story):
  true_accept  : VERIFIED,  answer matches gold           (LLM right,  approved)
  true_catch   : VIOLATED,  answer != gold                (LLM wrong,  caught)     <- the guardrail working
  false_accept : VERIFIED,  answer != gold                (LLM wrong,  MISSED)     <- must be 0 (soundness)
  false_reject : VIOLATED,  answer matches gold           (LLM right,  rejected)   <- coverage cost
  abstain      : ABSTAIN / UNVERIFIED_FORMULA             (no verdict)

Usage:
    python scripts/model_comparison.py \
        "Qwen3-4B=results/mc_calc_qwen3_4b/results.jsonl" \
        "Qwen2.5-32B=results/mc_calc_qwen32b/results.jsonl" \
        "Claude=results/agent_multicompany_provable_calc/results.jsonl"

    # or pass bare dirs/files; the label defaults to the dir name
    python scripts/model_comparison.py results/agent_multicompany_provable_calc [--csv out.csv]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def _nums(text) -> list[float]:
    # require a leading digit so lone commas/dots in free-text gold answers don't
    # produce empty matches (FinanceBench gold can be a sentence).
    out = []
    for x in re.findall(r"-?\d[\d,]*\.?\d*", str(text or "")):
        try:
            out.append(abs(float(x.replace(",", ""))))
        except ValueError:
            pass
    return out


def _matches_gold(claimed, gold) -> bool | None:
    if claimed is None:
        return None
    targets = _nums(gold)
    if not targets:
        return None
    c = abs(float(claimed))
    return any(abs(c - g) <= max(1.0, g * 0.01) for g in targets)


def _has_flag(obj, key) -> bool:
    """Recursively test whether `key` appears truthy anywhere in a nested dict/list."""
    if isinstance(obj, dict):
        if obj.get(key):
            return True
        return any(_has_flag(v, key) for v in obj.values())
    if isinstance(obj, list):
        return any(_has_flag(v, key) for v in obj)
    return False


def load_gold_map(path: Path) -> dict:
    """id -> answer-correctness (bool) from a reference run's unit-aware flag.

    Baselines judge the same candidate answers (by id), so an answer's correctness is
    a property of the answer, not the method. Using one map from the reference run
    (e.g. the VerifiQA run) scores every method identically and avoids the naive
    numeric matcher, which mis-scores FinanceBench gold (mixed billions/millions/absolute).
    """
    m = {}
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        rid = r.get("id") or r.get("financebench_id")
        amg = r.get("answer_matches_gold")
        if rid and isinstance(amg, bool):
            m[rid] = amg
    return m


def score(path: Path, gold_map: dict | None = None) -> dict:
    b = {"true_accept": 0, "true_catch": 0, "false_reject": 0,
         "false_accept": 0, "abstain": 0, "unverified": 0, "total": 0}
    wrong_caught = wrong_missed = wrong_abst = 0
    smt_repaired = ans_repaired = 0
    gold_wrong = 0   # errors defined by the shared gold map (method-independent)
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        b["total"] += 1
        if _has_flag(r.get("diagnostics"), "smt_invalid_repaired"):
            smt_repaired += 1
        if isinstance(r.get("repair"), dict) and r["repair"].get("repaired"):
            ans_repaired += 1
        st = r.get("status", "")
        cv = r.get("claimed_value")
        gold = r.get("gold_answer") or r.get("answer")
        rid = r.get("id") or r.get("financebench_id")
        # With --gold-from, use the shared unit-aware correctness map (consistent across
        # methods). Otherwise fall back to the naive numeric match (stable default).
        if gold_map is not None and rid in gold_map:
            ok = gold_map[rid]
            if ok is False:
                gold_wrong += 1
        else:
            ok = _matches_gold(cv, gold)
        # Abstentions: ABSTAIN and UNVERIFIED_FORMULA are both "no verdict"; fold them
        # together so the visible buckets sum to n. A VERIFIED/VIOLATED row with no
        # numeric claim is not a real decision either -> also an abstention (keeps FA <= errs).
        if st in ("ABSTAIN", "UNVERIFIED_FORMULA") or cv is None:
            b["abstain"] += 1
        elif st == "VERIFIED":
            b["true_accept" if ok else "false_accept"] += 1
        elif st == "VIOLATED":
            b["true_catch" if ok is False else "false_reject"] += 1
        else:
            b["abstain"] += 1
        # catch-rate universe: model emitted a wrong numeric answer
        if cv is not None and ok is False:
            if st == "VIOLATED":
                wrong_caught += 1
            elif st == "VERIFIED":
                wrong_missed += 1
            else:
                wrong_abst += 1
    verified = b["true_accept"] + b["false_accept"]
    decided = verified + b["true_catch"] + b["false_reject"]
    # Catch-rate is measured only over wrong answers the verifier actually decided
    # on (VIOLATED or VERIFIED). A wrong answer that was abstained is counted purely
    # as an abstention, never as a missed catch.
    decided_wrong = wrong_caught + wrong_missed
    total_wrong = decided_wrong + wrong_abst
    b["precision"] = b["true_accept"] / verified if verified else None
    b["accuracy"] = (b["true_accept"] + b["true_catch"]) / decided if decided else None
    b["abstention"] = b["abstain"] / b["total"] if b["total"] else None
    b["catch_rate"] = wrong_caught / decided_wrong if decided_wrong else None
    # With a shared gold map every method sees the same fixed error set, so report that
    # count (identical across methods) rather than each method's own emitted-wrong count.
    b["n_errors"] = gold_wrong if gold_map is not None else total_wrong
    b["wrong_caught"] = wrong_caught
    b["wrong_missed"] = wrong_missed
    b["smt_repaired"] = smt_repaired      # abstentions recovered by invalid-SMT retry
    b["ans_repaired"] = ans_repaired      # VIOLATEDs flipped to VERIFIED by answer retry
    return b


def _resolve(arg: str) -> tuple[str, Path]:
    label, _, spec = arg.partition("=")
    if not spec:  # no explicit label
        spec, label = label, ""
    p = Path(spec)
    if p.is_dir():
        p = p / "results.jsonl"
    if not label:
        label = p.parent.name
    return label, p


def _fmt(x, pct=False) -> str:
    if x is None:
        return "  n/a"
    return f"{100*x:5.1f}%" if pct else f"{x:5d}"


def main(argv: list[str]) -> None:
    csv_path = None
    gold_map = None
    args = []
    it = iter(argv)
    for a in it:
        if a == "--csv":
            csv_path = Path(next(it))
        elif a == "--gold-from":
            gold_map = load_gold_map(Path(next(it)))
        else:
            args.append(a)
    if not args:
        print(__doc__)
        return

    rows = []
    for a in args:
        label, path = _resolve(a)
        if not path.exists():
            print(f"skip (missing): {path}", file=sys.stderr)
            continue
        rows.append((label, score(path, gold_map)))

    w = max((len(l) for l, _ in rows), default=8)
    H = ["model", "n", "prec", "catch", "acc", "abst", "TA", "TC", "FR", "FA", "ABST", "errs"]
    print(f"{'model':<{w}}  " + "  ".join(f"{h:>6}" for h in H[1:]))
    print("-" * (w + 2 + 8 * len(H[1:])))
    for label, b in rows:
        cells = [
            f"{b['total']:>6}",
            _fmt(b["precision"], True), _fmt(b["catch_rate"], True),
            _fmt(b["accuracy"], True), _fmt(b["abstention"], True),
            f"{b['true_accept']:>6}", f"{b['true_catch']:>6}",
            f"{b['false_reject']:>6}", f"{b['false_accept']:>6}",
            f"{b['abstain']:>6}", f"{b['n_errors']:>6}",
        ]
        print(f"{label:<{w}}  " + "  ".join(cells))
    print()
    print("prec=precision  catch=catch-rate on wrong answers  acc=decision accuracy")
    print("TA=true-accept TC=true-catch FR=false-reject FA=FALSE-ACCEPT(want 0) ABST=abstain errs=#wrong answers")

    if any(b.get("smt_repaired") or b.get("ans_repaired") for _, b in rows):
        print("\nrepair recovery (--repair):")
        for label, b in rows:
            if b.get("smt_repaired") or b.get("ans_repaired"):
                print(f"  {label:<{w}}  invalid-SMT recovered={b['smt_repaired']}  "
                      f"answer-repaired (VIOLATED->VERIFIED)={b['ans_repaired']}")

    if csv_path:
        import csv
        with csv_path.open("w", newline="") as fh:
            wtr = csv.writer(fh)
            wtr.writerow(["model", "n", "precision", "catch_rate", "accuracy", "abstention",
                          "true_accept", "true_catch", "false_reject", "false_accept",
                          "abstain", "n_errors", "wrong_caught", "wrong_missed"])
            for label, b in rows:
                wtr.writerow([label, b["total"], b["precision"], b["catch_rate"], b["accuracy"],
                              b["abstention"], b["true_accept"], b["true_catch"], b["false_reject"],
                              b["false_accept"], b["abstain"], b["n_errors"], b["wrong_caught"],
                              b["wrong_missed"]])
        print(f"\nwrote {csv_path}")


if __name__ == "__main__":
    main(sys.argv[1:])
