"""Recover paper assets from immutable primary-source history, without an LLM.

The historical exclusion file is evidence of sample identity, not an instruction
to accept every remaining label as a scalar. All semantic exceptions are retained
in a separate review queue. No test gold is used to repair the knowledge graph.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import subprocess

from .data import EXPECTED, OFFICIAL_SOURCES, flatten_official, markdown_table, sha256, write_json
from .metrics import parse_number
from .types import AssetError, dumps


HISTORY_COMMIT = "a0450278c6f91c9707457e4ee8aca8d577fe41c6"
HISTORY_FILES = {
    "data/data_clean.py": "af9fa1b0b58a5833b6a6218b9713b9da4a0a6a16bcf2931b8ea110279b84c033",
    "data/remove_problem.json": "272e4b0b9200efe5f35119c761453e148cea35b60bcd4f9fd1e5a31bc2066915",
}
FINQA_2022 = {
    "repository": "czyssrs/FinQA", "path": "dataset/test.json",
    "commit": "b2eaa7156acb7d12fecc7386b92dd4bf82f9cc52",
    "sha256": "7676262f3e0ba095af272607b52080e4d0ef4215a0b2bad71061b73c29357494",
    "rows": 1050,
}


def whitespace(text) -> str:
    return " ".join(str(text).split())


def signature(question, context, answer) -> str:
    return dumps([whitespace(question), whitespace(context), answer])


def recover_history(upstream: Path, directory: Path, *, offline: bool = False) -> dict[str, Path]:
    """Read git blobs as data only; never import or execute the deleted script."""
    result = {}
    for relative, expected in HISTORY_FILES.items():
        target = directory / HISTORY_COMMIT[:8] / relative
        if not target.exists():
            command = ["git", "-C", str(upstream), "show", HISTORY_COMMIT + ":" + relative]
            blob = subprocess.run(command, capture_output=True)
            if blob.returncode:
                if offline:
                    raise AssetError("Historical source is not present in the checkout: " + relative)
                import httpx
                url = f"https://raw.githubusercontent.com/aolaoban/Graph-Bounded_Financial_Reasoning/{HISTORY_COMMIT}/{relative}"
                response = httpx.get(url, timeout=60, follow_redirects=True)
                response.raise_for_status()
                content = response.content
            else:
                content = blob.stdout
            if hashlib.sha256(content).hexdigest() != expected:
                raise AssetError("Historical source hash mismatch: " + relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        if sha256(target) != expected:
            raise AssetError("Recovered historical source changed: " + str(target))
        result[relative] = target
    return result


def fetch_finqa_2022(directory: Path, *, offline: bool = False) -> Path:
    target = directory / "history" / (FINQA_2022["commit"] + ".json")
    if not target.exists():
        if offline:
            raise AssetError("Missing official FinQA 2022 snapshot")
        import httpx
        url = f"https://raw.githubusercontent.com/{FINQA_2022['repository']}/{FINQA_2022['commit']}/{FINQA_2022['path']}"
        response = httpx.get(url, timeout=60, follow_redirects=True)
        response.raise_for_status()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(response.content)
    if sha256(target) != FINQA_2022["sha256"]:
        raise AssetError("Official FinQA 2022 snapshot hash mismatch")
    return target


def compatible_rows(name: str, native: list[dict]) -> list[dict]:
    """Reconstruct the released serialization solely to join historical identities."""
    if name == "FinQA":
        return [{"question": r["qa"]["question"], "answer": r["qa"]["answer"],
                 "context": " ".join([*r["pre_text"], *r["post_text"]]),
                 "table": markdown_table(r.get("table_ori", r["table"])), "uid": r["id"]}
                for r in native]
    if name == "TAT-QA":
        rows = []
        for group in native:
            for q in group["questions"]:
                answer = q["answer"]
                if isinstance(answer, list):
                    answer = ", ".join(str(a) for a in answer)
                rows.append({"question": q["question"], "answer": str(answer),
                             "context": "\n".join(p["text"] for p in group["paragraphs"]),
                             "table": markdown_table(group["table"]["table"]),
                             "uid": group["table"]["uid"] + "_" + q["uid"]})
        return rows
    raise ValueError(name)


def recover_exclusion_indices(sources: dict[str, list[dict]], exclusions: list[dict]) -> tuple[dict[str, set[int]], list[dict]]:
    """Join by full (question, document, label), preserving duplicate multiplicity.

    One historical entry intentionally has only a question and an empty label.
    It can be resolved only if that pair identifies exactly one unused source row.
    A count target is never used to resolve an ambiguous or missing identity.
    """
    exact, by_question_label = defaultdict(list), defaultdict(list)
    for name, rows in sources.items():
        for i, row in enumerate(rows):
            ref = (name, i)
            context = row.get("context", "") + "\n" + row.get("table", "")
            exact[signature(row["question"], context, row["answer"])].append(ref)
            by_question_label[dumps([whitespace(row["question"]), row["answer"]])].append(ref)
    removed = {name: set() for name in sources}
    evidence = []
    for exclusion_index, item in enumerate(exclusions):
        if "context" in item:
            candidates = exact[signature(item["query"], item["context"], item["answer"])]
            method = "question_context_label_multiset"
        else:
            candidates = by_question_label[dumps([whitespace(item["query"]), item["answer"]])]
            method = "unique_question_label_no_context"
        available = [(name, i) for name, i in candidates if i not in removed[name]]
        if not available or (method == "unique_question_label_no_context" and len(available) != 1):
            raise AssetError(f"Cannot uniquely recover exclusion entry {exclusion_index}")
        # Multiple identical full signatures are exchangeable copies. Consume each
        # source position once, so a duplicated exclusion never deletes extra rows.
        name, i = available[0]
        removed[name].add(i)
        evidence.append({"exclusion_entry": exclusion_index, "dataset": name,
                         "source_index": i, "uid": sources[name][i].get("uid"),
                         "method": method, "identical_remaining_copies": len(available)})
    return removed, evidence


def negative_lineage(positives: list[dict], negatives: list[dict]) -> dict:
    by_q = defaultdict(list)
    by_uid = defaultdict(list)
    for i, r in enumerate(positives):
        by_q[whitespace(r["question"]).casefold()].append(i)
        if r.get("uid"):
            by_uid[r["uid"]].append(i)
    links, unresolved = [], []
    for i, neg in enumerate(negatives):
        original = neg.get("negative_sample_details", {}).get("original_question", "")
        candidates = by_uid.get(neg.get("uid"), []) if neg.get("uid") else []
        method = "uid" if candidates else "original_question"
        if not candidates:
            candidates = by_q[whitespace(original).casefold()]
        # Context/table equality can disambiguate repeated wording. It never sees
        # the model's output or changes a negative sample's label.
        if len(candidates) > 1:
            exact_context = [j for j in candidates
                             if whitespace(positives[j].get("context", "")) == whitespace(neg.get("context", ""))
                             and whitespace(positives[j].get("table", "")) == whitespace(neg.get("table", ""))]
            if exact_context:
                candidates = exact_context
                method += "+context"
        if len(candidates) != 1:
            unresolved.append(i)
        links.append({"negative_index": i, "source_candidates": candidates, "join_method": method})
    return {"links": links, "unique": len(negatives)-len(unresolved), "ambiguous_or_missing": unresolved,
            "interpretation": "Links establish source identity only, not human verification of unanswerability"}


def reconcile_datasets(upstream: Path, official_dir: Path, history_dir: Path, output: Path, *, offline=False) -> dict:
    history = recover_history(upstream, history_dir, offline=offline)
    finqa_path = fetch_finqa_2022(official_dir, offline=offline)
    tatqa_path = official_dir / "TAT-QA.json"
    if sha256(tatqa_path) != OFFICIAL_SOURCES["TAT-QA"]["sha256"]:
        raise AssetError("Official TAT-QA snapshot hash mismatch")
    native = {"FinQA": json.loads(finqa_path.read_text(encoding="utf-8")),
              "TAT-QA": json.loads(tatqa_path.read_text(encoding="utf-8"))}
    sources = {name: compatible_rows(name, rows) for name, rows in native.items()}
    excluded_raw = json.loads(history["data/remove_problem.json"].read_text(encoding="utf-8"))
    removed, exclusion_evidence = recover_exclusion_indices(sources, excluded_raw)
    report = {"schema_version": 1, "historical_commit": HISTORY_COMMIT,
              "historical_files": HISTORY_FILES, "official_finqa": FINQA_2022,
              "official_tatqa": OFFICIAL_SOURCES["TAT-QA"],
              "exclusion_entries": len(excluded_raw), "exclusion_evidence": exclusion_evidence,
              "datasets": {}, "paper_ready": False}
    neg_files = {"FinQA": "finqa_nsdata.json", "TAT-QA": "tatqa_nsdata.json"}
    for name in sources:
        standard = flatten_official(name, native[name])
        # FinQA's original presentation table carries clean accounting signs.
        if name == "FinQA":
            for original, sample in zip(native[name], standard):
                sample["context"] = "\n".join([*original["pre_text"],
                    markdown_table(original.get("table_ori", original["table"])), *original["post_text"]])
        selected = [i for i in range(len(standard)) if i not in removed[name]]
        review = []
        kept = []
        for i in selected:
            sample = standard[i]
            if parse_number(sample["answer"]) is None:
                review.append({"source_index": i, "uid": sample["uid"], "question": sample["question"],
                               "answer": sample["answer"], "reason": "retained_historical_label_not_supported_scalar"})
            kept.append({"id": name + ":" + sample["uid"], "dataset": name,
                         "question": sample["question"], "context": sample["context"],
                         "answer": sample["answer"], "answer_meta": sample.get("answer_meta", {}),
                         "unanswerable": False, "source": {"uid": sample["uid"], "index": i,
                            "commit": FINQA_2022["commit"] if name == "FinQA" else OFFICIAL_SOURCES[name]["commit"]}})
        negatives = json.loads((upstream / "data" / name / neg_files[name]).read_text(encoding="utf-8"))
        for i, sample in enumerate(negatives):
            context = sample.get("context", "")
            if sample.get("table"):
                context += "\n" + sample["table"]
            kept.append({"id": name + ":counterfactual:" + str(i), "dataset": name,
                         "question": sample["question"], "context": context, "answer": None,
                         "unanswerable": True, "source": {"file": neg_files[name], "index": i}})
        target = output / (name + ".jsonl")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("".join(dumps(sample)+"\n" for sample in kept), encoding="utf-8")
        item = {"source_rows": len(standard), "excluded_indices": sorted(removed[name]),
                "selected_indices": selected, "selected_uids": [standard[i]["uid"] for i in selected],
                "actual": {"original": len(selected), "counterfactual": len(negatives), "total": len(kept)},
                "expected_table4": EXPECTED[name], "unresolved_labels": review,
                "selection_recovery": "exact historical exclusion identities, independent of desired counts",
                "file_sha256": sha256(target), "lineage": negative_lineage(sources[name], negatives)}
        for link in item["lineage"]["links"]:
            link["parent_in_selected_positives"] = (link["source_candidates"][0] in selected
                if len(link["source_candidates"]) == 1 else None)
        item["lineage"]["parents_excluded_from_positive_set"] = [
            link["negative_index"] for link in item["lineage"]["links"] if link["parent_in_selected_positives"] is False]
        item["counterfactual_fraction_of_unfiltered_source"] = len(negatives) / len(standard)
        item["counts_match"] = item["actual"] == item["expected_table4"]
        item["scalar_labels_supported"] = not review
        report["datasets"][name] = item
    # Verify rather than merely assume why the current author FinQA has 1,050 rows.
    author = json.loads((upstream / "data" / "FinQA" / "finqa.json").read_text(encoding="utf-8"))
    checks = {"same_length": len(author) == len(sources["FinQA"]),
              "question_matches": 0, "context_matches": 0, "original_table_matches": 0, "label_changes": []}
    for i, (a, source) in enumerate(zip(author, sources["FinQA"])):
        checks["question_matches"] += whitespace(a["question"]) == whitespace(source["question"])
        checks["context_matches"] += whitespace(a.get("context", "")) == whitespace(source["context"])
        checks["original_table_matches"] += whitespace(a.get("table", "")) == whitespace(source["table"])
        if a["answer"] != source["answer"]:
            checks["label_changes"].append({"index": i, "uid": source["uid"],
                                             "official_answer": source["answer"], "author_answer": a["answer"]})
    report["finqa_version_alignment"] = checks
    write_json(output / "selection_manifest.json", report)
    return report
