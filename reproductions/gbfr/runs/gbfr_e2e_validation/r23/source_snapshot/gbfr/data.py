"""Read published benchmark assets, strip all solutions and retain audit trails."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

from .metrics import parse_number
from .types import dumps


EXPECTED = {
    "CFBenchmark": {"original": 140, "counterfactual": 11, "total": 151},
    "FinanceReasoning": {"original": 2238, "counterfactual": 412, "total": 2650},
    "FinQA": {"original": 1002, "counterfactual": 97, "total": 1099},
    "TAT-QA": {"original": 1119, "counterfactual": 151, "total": 1270},
}
FILES = {
    "CFBenchmark": (["金融指标计算.json", "金融数值提取.json"], "cfben_nsdata.json"),
    "FinanceReasoning": (["easy.json", "medium.json", "hard.json"], "financereasoning_nsdata.json"),
    "FinQA": (["finqa.json"], "finqa_nsdata.json"),
    "TAT-QA": (["tatqa.json"], "tatqa_nsdata.json"),
}
OFFICIAL_SOURCES = {
    "FinQA": {
        "repository": "czyssrs/FinQA", "path": "dataset/test.json",
        "commit": "0f16e2867befa6840783e58be38c9efb9229d742",
        "sha256": "831dbfb2e785dbc227f895ce3f24046433467aec67b09db2bd6ac7692a8a30dc",
    },
    "TAT-QA": {
        "repository": "NExTplusplus/TAT-QA", "path": "dataset_raw/tatqa_dataset_test_gold.json",
        "commit": "12fd7c8bb474e8b45e9f54dbf7c281c178f1a510",
        "sha256": "c4d08418359c1d76468dec420ee748a37f48c06b63cb8ec2766f19d5d314b597",
    },
}


def markdown_table(rows: list[list]) -> str:
    def line(row):
        return "| " + " | ".join(str(cell).replace("|", "\\|").replace("\n", " ") for cell in row) + " |"
    if not rows:
        return ""
    return "\n".join([line(rows[0]), line(["---"]*len(rows[0])), *[line(r) for r in rows[1:]]])


def flatten_official(name: str, rows: list[dict]) -> list[dict]:
    """Use entire document content; never use gold_inds, facts or retrieval labels."""
    if name == "FinQA":
        return [{"question": r["qa"]["question"], "answer": r["qa"]["answer"], "uid": r["id"],
                 "context": "\n".join([*r["pre_text"], markdown_table(r.get("table_ori", r["table"])), *r["post_text"]])}
                for r in rows]
    if name == "TAT-QA":
        result = []
        for group in rows:
            context = "\n".join([*(p["text"] for p in group["paragraphs"]),
                                  markdown_table(group["table"]["table"])])
            for q in group["questions"]:
                answer = q["answer"]
                if isinstance(answer, list) and len(answer) == 1:
                    answer = answer[0]
                scale = q.get("scale", "")
                meta = {"unit": "percentage"} if scale == "percent" else {"scale": scale} if scale else {}
                result.append({"question": q["question"], "answer": answer, "context": context,
                               "uid": group["table"]["uid"] + "_" + q["uid"],
                               "answer_type": q["answer_type"], "answer_meta": meta})
        return result
    raise ValueError("No native adapter for " + name)


def fetch_official(directory: Path, *, offline=False):
    import httpx
    directory.mkdir(parents=True, exist_ok=True)
    for name, spec in OFFICIAL_SOURCES.items():
        path = directory / (name + ".json")
        url = f"https://raw.githubusercontent.com/{spec['repository']}/{spec['commit']}/{spec['path']}"
        if not path.exists():
            if offline:
                raise FileNotFoundError("Missing pinned official split: " + str(path))
            response = httpx.get(url, timeout=60, follow_redirects=True)
            response.raise_for_status()
            path.write_bytes(response.content)
        if sha256(path) != spec["sha256"]:
            raise ValueError("Official split does not match pinned SHA256: " + str(path))
        write_json(directory / (name + ".source.json"), {**spec, "url": url, "sha256": sha256(path)})


def sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def jsonl(path: str | Path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: str | Path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def prepare_dataset(root: Path, name: str, output: Path, official_dir: Path | None = None) -> dict:
    positive_files, negative_file = FILES[name]
    use_official = official_dir is not None and name in OFFICIAL_SOURCES
    if use_official:
        positive_files = [OFFICIAL_SOURCES[name]["path"].split("/")[-1]]
    samples, exclusions, files, used_ids = [], [], [], set()
    raw_count = 0
    for filename in [*positive_files, negative_file]:
        negative = filename == negative_file
        source = official_dir / (name + ".json") if use_official and not negative else root / "data" / name / filename
        rows = json.loads(source.read_text(encoding="utf-8"))
        source_info = {"path": str(source.resolve()), "sha256": sha256(source), "raw_groups": len(rows)}
        if use_official and not negative:
            if sha256(source) != OFFICIAL_SOURCES[name]["sha256"]:
                raise ValueError("Official source changed: " + str(source))
            rows = flatten_official(name, rows)
            source_info["official_source"] = OFFICIAL_SOURCES[name]
        source_info["rows"] = len(rows)
        files.append(source_info)
        for i, row in enumerate(rows):
            answer = row.get("ground_truth") if name == "FinanceReasoning" else row.get("answer")
            if not negative:
                raw_count += 1
                is_boolean_comparison = name == "FinanceReasoning" and isinstance(answer, bool)
                if parse_number(answer) is None and not is_boolean_comparison:
                    exclusions.append({"source_file": filename, "source_index": i,
                                       "reason": "non_scalar_numeric_answer", "answer": answer,
                                       "answer_type": row.get("answer_type")})
                    continue
            elif str(answer).strip().upper() not in {"N/A", "NONE", "NULL", "⊥"}:
                raise ValueError(f"Counterfactual has a non-abstention label: {filename}:{i}")
            context = row.get("context", "")
            table = row.get("table", "")
            if table:
                context += "\n" + (table if isinstance(table, str) else dumps(table))
            question = row.get("question", "")
            if not question or not isinstance(context, str):
                raise ValueError(f"Missing question or invalid context: {filename}:{i}")
            context_origin = "provided_document"
            if name == "FinanceReasoning" and not context.strip():
                # Self-contained problems have their data in the question. Copy
                # those exact user-provided facts; introduce no numbers or labels.
                context = question
                context_origin = "verbatim_question_for_empty_document"
            key = hashlib.sha256(dumps([name, filename, i, question]).encode()).hexdigest()[:20]
            ident = name + ":" + key
            if ident in used_ids:
                raise ValueError("Duplicate sample id")
            used_ids.add(ident)
            samples.append({"id": ident, "dataset": name, "question": question, "context": context,
                            "answer": None if negative else answer, "unanswerable": negative,
                            "answer_type": "abstention" if negative else "boolean" if isinstance(answer, bool) else "numeric",
                            "context_origin": context_origin,
                            "answer_meta": row.get("answer_meta", {}),
                            "source": {"file": filename, "index": i,
                                       "uid": row.get("uid", row.get("question_id"))},
                            "perturbation": row.get("negative_sample_details", {}).get("modification_type") if negative else None})
    actual = {"original": sum(not s["unanswerable"] for s in samples),
              "counterfactual": sum(s["unanswerable"] for s in samples),
              "total": len(samples)}
    destination = output / (name + ".jsonl")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("".join(dumps(s) + "\n" for s in samples), encoding="utf-8")
    write_json(output / (name + ".exclusions.json"), exclusions)
    return {"dataset": name, "raw_original": raw_count, "excluded": len(exclusions),
            "actual": actual, "expected_table4": EXPECTED[name], "counts_match": actual == EXPECTED[name],
            "counterfactual_origin": "author-published; human-verification provenance not independently available",
            "counterfactual_groups": dict(Counter(s["perturbation"] for s in samples if s["unanswerable"])),
            "empty_contexts": sum(not s["context"].strip() for s in samples),
            "self_contained_question_documents": sum(s["context_origin"] == "verbatim_question_for_empty_document" for s in samples),
            "boolean_comparisons": sum(s["answer_type"] == "boolean" for s in samples),
            "processed_sha256": sha256(destination), "source_files": files}


def audit_raw_graph(path: Path) -> dict:
    rows = json.loads(path.read_text(encoding="utf-8"))
    valid = [r for r in rows if isinstance(r.get("term_en"), dict) and r["term_en"].get("name")]
    names = Counter(r["term_en"]["name"] for r in valid)
    edges = {(r["term_en"]["name"], d["concept"]) for r in valid
             for d in r.get("related_concepts_en", []) if d.get("concept")}
    all_names = set(names) | {b for _, b in edges}
    # Kahn's residual exposes cycles without deleting or reorienting any edge.
    children = {n: set() for n in all_names}
    degree = Counter({n: 0 for n in all_names})
    for a, b in edges:
        children[a].add(b)
        degree[b] += 1
    queue = [n for n in all_names if degree[n] == 0]
    visited = 0
    while queue:
        node = queue.pop()
        visited += 1
        for b in children[node]:
            degree[b] -= 1
            if degree[b] == 0:
                queue.append(b)
    return {"source_sha256": sha256(path), "raw_records": len(rows), "valid_term_records": len(valid),
            "error_records": len(rows)-len(valid), "unique_exact_names": len(names),
            "duplicate_name_count": sum(c > 1 for c in names.values()),
            "duplicate_record_count": sum(c-1 for c in names.values()),
            "records_without_formula_field_content": sum(not r.get("formula_en") for r in valid),
            "records_with_formula_field_content": sum(bool(r.get("formula_en")) for r in valid),
            "explicit_atomic_derived_type_field_available": False,
            "unique_declared_dependencies": len(edges),
            "extra_dependency_names": len(all_names-set(names)),
            "declared_dependency_graph_is_dag": visited == len(all_names),
            "cycle_residual_count": len(all_names)-visited,
            "cycle_residual_examples": sorted(n for n in all_names if degree[n] > 0)[:20],
            "paper_expected": {"nodes": 7521, "atomic": 3318, "derived": 4203, "edges": 20152},
            "paper_ready": False,
            "reason": "Raw records do not define the paper's expert-validated canonical formula-level DAG"}


def prepare(root: Path, output: Path, official_dir: Path | None = None, recovered_dir: Path | None = None,
            source_reviews: dict | None = None) -> dict:
    import subprocess
    revision = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if source_reviews is None:
        source_reviews = {}
        for name, filename in [("CFBenchmark", "cfbenchmark_source.json"), ("FinanceReasoning", "finance_reasoning_source.json")]:
            review = root.parent / "reconciliation" / filename
            if review.exists():
                source_reviews[name] = json.loads(review.read_text(encoding="utf-8"))
    if official_dir is None:
        raise ValueError("Official FinQA/TAT-QA splits must be provided; no silent upstream substitute")
    datasets = {name: prepare_dataset(root, name, output, official_dir) for name in FILES}
    if recovered_dir is not None:
        recovered = json.loads((recovered_dir / "selection_manifest.json").read_text(encoding="utf-8"))
        for name, item in recovered["datasets"].items():
            source = recovered_dir / (name + ".jsonl")
            if sha256(source) != item["file_sha256"]:
                raise ValueError("Recovered selection changed: " + name)
            diagnostic = datasets[name]
            destination = output / (name + ".jsonl")
            destination.write_bytes(source.read_bytes())
            excluded = [{"source_index": i, "reason": "recovered_historical_exclusion_identity"}
                        for i in item["excluded_indices"]]
            write_json(output / (name + ".exclusions.json"), excluded)
            datasets[name] = {"dataset": name, "raw_original": item["source_rows"],
                "excluded": len(excluded), "actual": item["actual"], "expected_table4": EXPECTED[name],
                "counts_match": item["counts_match"], "processed_sha256": sha256(destination),
                "selection_recovery": item["selection_recovery"],
                "scalar_labels_supported": item["scalar_labels_supported"],
                "unresolved_labels": item["unresolved_labels"],
                "selection_manifest_sha256": sha256(recovered_dir / "selection_manifest.json"),
                "official_source": recovered["official_finqa"] if name == "FinQA" else recovered["official_tatqa"],
                "historical_exclusion_commit": recovered["historical_commit"],
                "historical_exclusion_sha256": recovered["historical_files"]["data/remove_problem.json"],
                "diagnostic_full_latest_numeric_filter": diagnostic}
    author_view = {name: prepare_dataset(root, name, output / "author_view") for name in OFFICIAL_SOURCES}
    if source_reviews and "CFBenchmark" in source_reviews:
        datasets["CFBenchmark"]["unresolved_gold_disagreements"] = source_reviews["CFBenchmark"]["gold_label_edits_in_gbfr_release"]
        datasets["CFBenchmark"]["input_transform_exceptions"] = source_reviews["CFBenchmark"]["input_transform_exceptions"]
    graph = audit_raw_graph(root / "knowledge_base" / "term_en_final.json")
    manifest = {"schema_version": 1, "source_repository": "https://github.com/aolaoban/Graph-Bounded_Financial_Reasoning",
                "source_commit": revision, "datasets": datasets, "author_positive_comparison": author_view,
                "raw_graph": graph,
                "paper_ready": False,
                "note": "No random 50-example subsampling, no truncation, no gold/solutions passed to model"}
    write_json(output / "manifest.json", manifest)
    return manifest
