"""Paper's relative 0.2% error bound, preserving sign and scale."""
from decimal import Decimal
import math


def correct(prediction, gold):
    if type(gold) is bool or type(prediction) is bool:
        return type(prediction) is bool and type(gold) is bool and prediction == gold
    if type(prediction) not in (int, float) or not math.isfinite(prediction):
        return False
    pred, target = Decimal(str(prediction)), Decimal(str(gold))
    return abs(pred-target) <= abs(target) * Decimal("0.002")


def summarize(records, labels):
    by_id = {r["question_id"]: r for r in records}
    if len(by_id) != len(records) or not set(by_id) <= labels.keys():
        raise ValueError("Duplicate or unknown prediction IDs")
    hits = sum(r["status"] == "ok" and correct(r["answer"], labels[qid]) for qid, r in by_id.items())
    api_errors = sum(r["status"] == "api_error" for r in records)
    return {"expected": len(labels), "recorded": len(records), "correct": hits,
            "accuracy": hits/len(labels), "api_errors": api_errors,
            "model_or_execution_failures": sum(r["status"] not in ("ok", "api_error") for r in records),
            "complete": len(records) == len(labels) and api_errors == 0,
            "relative_error_tolerance": 0.002}
