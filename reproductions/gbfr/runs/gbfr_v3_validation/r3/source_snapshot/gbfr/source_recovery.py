"""Verify remaining benchmarks against their immutable official releases."""
from __future__ import annotations

from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path

from .data import sha256, write_json
from .metrics import parse_number
from .reconciliation import negative_lineage, whitespace
from .types import AssetError


FINANCE_REPOSITORY = "BUPT-Reasoning-Lab/FinanceReasoning"
FINANCE_COMMIT = "b0fe6455396f831955e4eb988472b4a563403bc5"
FINANCE_FILES = {
    "easy.json": ("data/FinanceReasoning/easy.json", "53890ee130f33759cf53cc71943248671e27e6035e75e4234373587784e56dd9"),
    "medium.json": ("data/FinanceReasoning/medium.json", "98098f9b54c0a8c6192b3f3f8b7afe514b0fef2b0972ff0fe63ff43202c20e22"),
    "hard.json": ("data/FinanceReasoning/hard.json", "ca8c055ef104176131da2e0f533897350cde3b93c4754575b09c7c7fbd046d9f"),
    "functions-article-all.json": ("data/functions/functions-article-all.json", "1c1d11ef6173208da0014b6bbb71cc8e2aa2683da9ba1ada4bf9e593fb4c7293"),
}
CF_REPOSITORY = "TongjiFinLab/CFBenchmark"
CF_COMMIT = "982788b50539cb617f3826704d4ef4b5747f7430"
CF_FILES = {
    "金融指标计算.json": "f273c9b11c81082221982dc1adb2e3d8d0e997ed49df34a1da1641694ffd6311",
    "金融数值提取.json": "05cc4ce18a16b0c13a436fb9ba94fcd28b9202db363915d9548608ea9fa68407",
    "金融数据检查.json": "597e250364953158a97dfd4bf48b8c4a22b95caeeac9492be8b2493fd0a6602c",
}


def cf_gold_arithmetic_checks() -> list[dict]:
    """Explicit arithmetic proofs for the two known, pinned-source disagreements.

    These are review evidence, not silent rewrites of the paper's scoring labels.
    Both the official and GBFR labels stay unchanged in their source snapshots.
    """
    income = Decimal("-214.8") * Decimal(10_000)
    sales = Decimal("5.799") * Decimal(100_000_000)
    ros = income / sales
    base_quote, target_quote = Decimal("6.4515"), Decimal("6.7261")
    cny_depreciation = (1-target_quote**-1 / base_quote**-1) * 100
    usd_appreciation = (target_quote-base_quote)/base_quote*100
    return [
        {"file": "金融指标计算.json", "index": 18, "metric": "ROS",
         "source_formula": "Net income / Sales revenue",
         "operands": {"net_income": "-214.8 万元", "sales": "5.799 亿元"},
         "normalized_operands_CNY": {"net_income": str(income), "sales": str(sales)},
         "computed_ratio": str(ros), "computed_at_requested_precision": str(ros.quantize(Decimal(".0001"), rounding=ROUND_HALF_UP)),
         "matching_official_option": "C", "official_declared_correct_option": "B",
         "gbfr_released_label": "-0.037", "conclusion": "Neither released scoring label equals the supplied formula with consistent currency scale"},
        {"file": "金融指标计算.json", "index": 66, "metric": "CNY depreciation against USD",
         "operands_CNY_per_USD": {"2021": str(base_quote), "2022": str(target_quote)},
         "comparison_basis": "Value of one CNY in USD, measured against its 2021 value",
         "computed_depreciation_percent": str(cny_depreciation),
         "computed_at_two_decimals_percent": str(cny_depreciation.quantize(Decimal(".01"), rounding=ROUND_HALF_UP)),
         "usd_appreciation_percent_on_the_opposite_quote": str(usd_appreciation),
         "official_declared_label": "4.08%", "gbfr_released_label": "4.26%",
         "conclusion": "Official label matches CNY depreciation; GBFR label matches appreciation of the opposite USD quote"},
    ]


def fetch_pinned(directory: Path, repository: str, commit: str, files: dict, *, offline=False):
    for name, (relative, expected) in files.items():
        path = directory / name
        if not path.exists():
            if offline:
                raise AssetError("Missing pinned primary source: " + str(path))
            import httpx
            response = httpx.get(f"https://raw.githubusercontent.com/{repository}/{commit}/{relative}",
                                 timeout=60, follow_redirects=True)
            response.raise_for_status()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(response.content)
        if sha256(path) != expected:
            raise AssetError("Primary source hash mismatch: " + str(path))


def source_audit(upstream: Path, raw_dir: Path, output: Path, *, offline=False) -> dict:
    finance_dir = raw_dir / "finance_reasoning_official"
    cf_dir = raw_dir / "cfbenchmark_official"
    fetch_pinned(finance_dir, FINANCE_REPOSITORY, FINANCE_COMMIT, FINANCE_FILES, offline=offline)
    cf_specs = {name: ("CFBenchmark-OpenFinData/data/金融计算/"+name, expected) for name, expected in CF_FILES.items()}
    fetch_pinned(cf_dir, CF_REPOSITORY, CF_COMMIT, cf_specs, offline=offline)
    finance, snapshots = [], []
    for name in ["easy.json", "medium.json", "hard.json"]:
        official = json.loads((finance_dir / name).read_text(encoding="utf-8"))
        released_path = upstream / "data/FinanceReasoning" / name
        released = json.loads(released_path.read_text(encoding="utf-8"))
        if official != released:
            raise AssetError("FinanceReasoning release differs semantically from pinned official rows: " + name)
        snapshots.append({"file": name, "official_sha256": sha256(finance_dir / name),
                          "gbfr_sha256": sha256(released_path), "json_identical": True, "rows": len(official)})
        finance.extend(official)
    negatives = json.loads((upstream / "data/FinanceReasoning/financereasoning_nsdata.json").read_text(encoding="utf-8"))
    finance_report = {"repository": FINANCE_REPOSITORY, "commit": FINANCE_COMMIT,
        "files": snapshots, "original_count": len(finance), "counterfactual_count": len(negatives),
        "boolean_labels": [{"index": i, "question_id": r.get("question_id"), "question": r["question"],
                            "answer": r["ground_truth"]} for i, r in enumerate(finance) if isinstance(r["ground_truth"], bool)],
        "empty_document_indices": [i for i, r in enumerate(finance) if not r.get("context", "").strip()],
        "negative_lineage": negative_lineage(finance, negatives),
        "full_dataset_preserved": True,
        "boolean_policy": "Preserve native bool labels; evaluate explicit compare results as typed binary answers",
        "empty_document_policy": "Use the verbatim problem statement as document, retaining its source origin"}
    functions_path = finance_dir / "functions-article-all.json"
    library = json.loads(functions_path.read_text(encoding="utf-8"))
    finance_report["function_library"] = {"path": FINANCE_FILES["functions-article-all.json"][0],
                                          "sha256": sha256(functions_path), "rows": len(library)}
    cf_rows, label_edits, input_changes, nonscalar = [], [], [], []
    for filename in ["金融指标计算.json", "金融数值提取.json"]:
        official = json.loads((cf_dir / filename).read_text(encoding="utf-8"))
        released = json.loads((upstream / "data/CFBenchmark" / filename).read_text(encoding="utf-8"))
        if len(official) != len(released):
            raise AssetError("CFBenchmark official/released row counts differ: " + filename)
        for i, (original, transformed) in enumerate(zip(official, released)):
            choice = original["answer"]
            correct_choice_text = original[choice]
            if correct_choice_text.strip() != transformed["answer"].strip():
                label_edits.append({"file": filename, "index": i, "id": original["id"],
                                    "official_option": choice, "official_answer": correct_choice_text,
                                    "gbfr_answer": transformed["answer"], "question": transformed["question"]})
            original_text = original["question"].replace("请给出正确选项。", "")
            released_text = transformed["question"] + "\n" + transformed.get("context", "")
            if transformed.get("solution"):
                released_text += "\n" + transformed["solution"]
            if "".join(original_text.split()) != "".join(released_text.split()):
                input_changes.append({"file": filename, "index": i, "id": original["id"],
                                      "issue": "input_differs_beyond_whitespace_and_removed_choice_instruction"})
            if parse_number(correct_choice_text) is None:
                nonscalar.append({"file": filename, "index": i, "id": original["id"],
                                  "question": transformed["question"], "official_answer": correct_choice_text,
                                  "gbfr_answer": transformed["answer"],
                                  "reason": "not_a_supported_single_scalar_financial_answer"})
            cf_rows.append(transformed)
    cf_negatives = json.loads((upstream / "data/CFBenchmark/cfben_nsdata.json").read_text(encoding="utf-8"))
    cf_report = {"repository": CF_REPOSITORY, "commit": CF_COMMIT,
                 "source_files": [{"file": name, "sha256": digest} for name, digest in CF_FILES.items()],
                 "candidate_original_count": len(cf_rows), "counterfactual_count": len(cf_negatives),
                 "selection_identity": "70 indicator-calculation + 70 numeric-extraction rows from the official release",
                 "gold_label_edits_in_gbfr_release": label_edits, "input_transform_exceptions": input_changes,
                 "nonscalar_label_review": nonscalar, "negative_lineage": negative_lineage(cf_rows, cf_negatives),
                 "paper_ready": False,
                 "unresolved": "Paper numeric-only filtering and Table 4's 140 originals cannot both be verified from this mixed-answer release"}
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "finance_reasoning_source.json", finance_report)
    write_json(output / "cfbenchmark_source.json", cf_report)
    write_json(output / "cfbenchmark_gold_arithmetic.json", {
        "official_repository": CF_REPOSITORY, "official_commit": CF_COMMIT,
        "checks": cf_gold_arithmetic_checks(), "scoring_labels_automatically_modified": False})
    return {"FinanceReasoning": finance_report, "CFBenchmark": cf_report}
