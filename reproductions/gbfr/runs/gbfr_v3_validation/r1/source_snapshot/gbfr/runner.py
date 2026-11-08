"""Only the GBFR rows of Table 1; persistent per-example predictions and traces."""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
from pathlib import Path

from .data import EXPECTED, jsonl, sha256, write_json
from .engine import GBFR
from .graph import MetricGraph
from .llm import APIError, ChatClient
from .metrics import parse_number, summarize
from .types import AssetError, dumps

RECONSTRUCTION_POLICY = 'paper-method-v1'


def validate_backbones(config):
    names = set(config['backbones'])
    if config.get('experiment_profile') == 'user-requested-backbone':
        name, model = config.get('requested_backbone'), config.get('requested_model')
        if not name or not model or names != {name} or config['backbones'][name]['model'] != model or not config.get('user_instruction'):
            raise AssetError('User-requested run requires one explicitly named backbone, model and instruction')
    elif config.get('experiment_profile') in {None, 'paper-table1-gbfr-only'}:
        if names != {'GPT-5','Qwen3-14B'}:
            raise AssetError('Main experiment requires exactly GPT-5 and Qwen3-14B')
    else:
        raise AssetError('Unknown experiment profile')


def _manifest(config):
    path = Path(config['data_dir']) / 'manifest.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def _expected_counts(config, manifest):
    if config.get('asset_policy') == RECONSTRUCTION_POLICY:
        if manifest.get('policy') != RECONSTRUCTION_POLICY or manifest.get('predictions_used') is not False:
            raise AssetError('Missing prediction-independent reconstruction manifest')
        if set(manifest.get('datasets', {})) != set(EXPECTED):
            raise AssetError('Reconstruction must include all four main datasets')
        return {name: manifest['datasets'][name]['expected_frozen'] for name in EXPECTED}
    if config.get('asset_policy') not in {None, 'paper-exact'}:
        raise AssetError('Unknown asset policy')
    return EXPECTED


PAPER_RESULTS = {
    "GPT-5": {"FinQA": [84.98, 98.80], "TAT-QA": [95.75, 96.69],
              "FinanceReasoning": [98.26, 100.0], "CFBenchmark": [96.69, 100.0]},
    "Qwen3-14B": {"FinQA": [76.73, 72.16], "TAT-QA": [91.50, 80.79],
                  "FinanceReasoning": [84.89, 83.25], "CFBenchmark": [86.75, 81.82]},
}


def resolve_paths(config_path: Path) -> dict:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    base = config_path.resolve().parent.parent
    for key in ["graph", "data_dir", "output_dir", "cache_dir", "asset_lock"]:
        path = Path(config[key])
        config[key] = str(path if path.is_absolute() else base / path)
    return config


def audit_datasets(config: dict) -> dict:
    """Inspect test-set readiness independently of the still-missing full FMKG."""
    datasets = {}
    manifest = _manifest(config)
    expected_counts = _expected_counts(config, manifest)
    for name, expected in expected_counts.items():
        path = Path(config["data_dir"]) / (name + ".jsonl")
        if not path.exists():
            datasets[name] = {"ready": False, "issues": ["missing_file"]}
            continue
        samples = jsonl(path)
        issues, unsupported, invalid_inputs = [], [], []
        counts = {"original": sum(not s["unanswerable"] for s in samples),
                  "counterfactual": sum(s["unanswerable"] for s in samples), "total": len(samples)}
        if counts != expected:
            issues.append("frozen_counts_differ" if config.get('asset_policy') == RECONSTRUCTION_POLICY else "table4_counts_differ")
        if len({s["id"] for s in samples}) != len(samples):
            issues.append("duplicate_sample_ids")
        digest = sha256(path)
        expected_digest = manifest.get("datasets", {}).get(name, {}).get("processed_sha256")
        unresolved_gold = manifest.get("datasets", {}).get(name, {}).get("unresolved_gold_disagreements", [])
        if unresolved_gold:
            issues.append("unresolved_source_gold_disagreements")
        if expected_digest and expected_digest != digest:
            issues.append("prepared_manifest_hash_mismatch")
        if config.get('asset_policy') == RECONSTRUCTION_POLICY:
            item = manifest['datasets'][name]
            adjustment_path = Path(config['data_dir']) / (name+'.adjustments.json')
            if not adjustment_path.exists() or sha256(adjustment_path) != item.get('adjustments_sha256'):
                issues.append('adjustment_audit_hash_mismatch')
            if [s['id'] for s in samples] != item.get('retained_ids'):
                issues.append('frozen_sample_identity_mismatch')
        for s in samples:
            if not s.get("question") or not isinstance(s.get("context"), str):
                invalid_inputs.append(s["id"])
            if s["unanswerable"]:
                if s.get("answer") is not None:
                    issues.append("counterfactual_has_non_abstention_label")
                continue
            boolean = (name == "FinanceReasoning" and s.get("answer_type") == "boolean" and isinstance(s["answer"], bool))
            if not boolean and parse_number(s["answer"]) is None:
                unsupported.append({"sample_id": s["id"], "question": s["question"], "answer": s["answer"]})
        if unsupported:
            issues.append("unsupported_non_scalar_labels")
        if invalid_inputs:
            issues.append("invalid_input_records")
        datasets[name] = {"ready": not issues, "issues": sorted(set(issues)), "actual": counts,
                          "expected_table4": EXPECTED[name], "expected_frozen": expected,
                          "counts_match_paper": counts == EXPECTED[name], "file_sha256": digest,
                          "unsupported_labels": unsupported, "invalid_inputs": invalid_inputs,
                          "unresolved_source_gold_disagreements": unresolved_gold,
                          "boolean_comparisons": sum(s.get("answer_type") == "boolean" for s in samples)}
    return {"datasets": datasets, "all_datasets_ready": all(d["ready"] for d in datasets.values()),
            "asset_policy": config.get('asset_policy', 'paper-exact'),
            "scope": "Frozen test-set identity/label readiness; main experiment also requires a validated DAG, asset lock and API"}


def preflight(config: dict) -> tuple[MetricGraph, dict[str, list[dict]]]:
    evaluation = config.get("evaluation", {})
    if (evaluation.get("rounding") != "ROUND_HALF_UP"
            or type(evaluation.get("unspecified_decimals")) is not int
            or not 0 <= evaluation["unspecified_decimals"] <= 12):
        raise AssetError("Evaluation requires ROUND_HALF_UP and unspecified_decimals from 0 to 12")
    graph_path = Path(config["graph"])
    if not graph_path.exists():
        raise AssetError("Missing paper-validated FMKG: " + str(graph_path)
                         + ". See docs/REPRODUCTION.md; raw upstream JSON must not be silently substituted.")
    graph = MetricGraph.load(graph_path)
    expected_graph = {"nodes": 7521, "atomic": 3318, "derived": 4203, "edges": 20152}
    if config.get('asset_policy') == RECONSTRUCTION_POLICY:
        from .build_graph import POLICY, SOURCE_SHA256
        if (graph.provenance.get('policy') != POLICY or graph.provenance.get('source_sha256') != SOURCE_SHA256
                or graph.provenance.get('benchmark_inputs_used') is not False
                or graph.provenance.get('reconstructed') is not True):
            raise AssetError('FMKG lacks source-only reconstruction provenance')
    else:
        if graph.stats() != expected_graph:
            raise AssetError(f"FMKG statistics differ from paper: {graph.stats()} != {expected_graph}")
        if graph.provenance.get("paper_validated") is not True or not graph.provenance.get("source"):
            raise AssetError("FMKG lacks paper-validation provenance")
    data_audit = audit_datasets(config)
    if not data_audit["all_datasets_ready"]:
        problems = {name: item["issues"] for name, item in data_audit["datasets"].items() if not item["ready"]}
        raise AssetError("Unresolved evaluation assets: " + dumps(problems) + "; run check-data for individual records")
    validate_backbones(config)
    lock_path = Path(config["asset_lock"])
    if not lock_path.exists():
        raise AssetError("Missing reviewed asset lock; use lock-assets after validating the exact paper assets")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if config.get('asset_policy') == RECONSTRUCTION_POLICY:
        if lock.get('asset_policy') != RECONSTRUCTION_POLICY or lock.get('manifest_sha256') != sha256(Path(config['data_dir'])/'manifest.json'):
            raise AssetError('Frozen dataset policy/manifest differs from asset lock')
        if lock.get('graph_stats') != graph.stats():
            raise AssetError('Graph statistics differ from frozen reconstruction')
    if lock.get("graph_sha256") != sha256(graph_path):
        raise AssetError("Graph differs from reviewed asset lock")
    datasets = {}
    for name, expected in _expected_counts(config, _manifest(config)).items():
        path = Path(config["data_dir"]) / (name + ".jsonl")
        if lock.get("datasets", {}).get(name) != sha256(path):
            raise AssetError(f"{name} differs from reviewed asset lock")
        samples = jsonl(path)
        original = sum(not s["unanswerable"] for s in samples)
        negative = len(samples)-original
        actual = {"original": original, "counterfactual": negative, "total": len(samples)}
        if actual != expected:
            raise AssetError(f"{name} differs from frozen evaluation set: {actual} != {expected}")
        if len({s["id"] for s in samples}) != len(samples):
            raise AssetError("Duplicate sample ids")
        for s in samples:
            boolean_comparison = (name == "FinanceReasoning" and s.get("answer_type") == "boolean"
                                  and isinstance(s["answer"], bool))
            if not s["unanswerable"] and parse_number(s["answer"]) is None and not boolean_comparison:
                raise AssetError(f"Non-numeric scalar answer: {s['id']}")
            if not s.get("question") or not isinstance(s.get("context"), str):
                raise AssetError("Empty question or invalid context")
        datasets[name] = samples
    return graph, datasets


def lock_assets(config: dict, provenance: str):
    """Hash reviewed assets, without granting them paper compliance by filename."""
    graph = MetricGraph.load(config["graph"])
    write_json(config["asset_lock"], {"schema_version": 1, "provenance": provenance,
               "asset_policy": config.get('asset_policy', 'paper-exact'), 'graph_stats': graph.stats(),
               'manifest_sha256': sha256(Path(config['data_dir'])/'manifest.json'),
               "graph_sha256": sha256(config["graph"]),
               "datasets": {name: sha256(Path(config["data_dir"]) / (name+".jsonl")) for name in EXPECTED}})
    # Validation still checks frozen identities/counts, hashes and DAG before any API request.
    return graph.stats()


def run_identity(config: dict, backbone: str, dataset: str) -> str:
    from . import __version__
    # Include source/prompts hashes, endpoint, model and parameters; exclude secrets.
    source_dir = Path(__file__).parent
    sources = {str(p.relative_to(source_dir)): sha256(p) for p in sorted(source_dir.rglob("*"))
               if p.suffix in {".py", ".txt"} and "__pycache__" not in p.parts}
    backbone_config = dict(config["backbones"][backbone])
    backbone_config["effective_base_url"] = os.environ.get(backbone_config.get("base_url_env", ""), backbone_config.get("base_url", ""))
    body = {"version": __version__, "source": sources, "backbone": backbone_config,
            'experiment_profile': config.get('experiment_profile','paper-table1-gbfr-only'),
            "dataset": dataset, "asset_lock": sha256(config["asset_lock"]),
            "evaluation": config["evaluation"], "execution_timeout": config.get("execution_timeout", 5)}
    if config.get('validation_manifest_sha256'):body['validation_manifest_sha256']=config['validation_manifest_sha256']
    return hashlib.sha256(dumps(body).encode()).hexdigest()


def recover_journal(path: Path) -> list[dict]:
    """Only repair a torn final line after interruption; interior corruption fails."""
    if not path.exists():
        return []
    raw = path.read_bytes()
    lines = raw.splitlines(keepends=True)
    result = []
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            result.append(json.loads(line))
        except (UnicodeDecodeError, json.JSONDecodeError):
            if i == len(lines)-1 and not line.endswith(b"\n"):
                path.write_bytes(b"".join(lines[:i]))
                break
            raise AssetError("Prediction journal is corrupt before its final incomplete line") from None
    # Ensure subsequent append does not join onto a valid but unterminated object.
    if result and path.read_bytes() and not path.read_bytes().endswith(b"\n"):
        with path.open("ab") as stream:
            stream.write(b"\n")
    return result


async def run_cell(config: dict, graph: MetricGraph, name: str, samples: list[dict], backbone: str, *, retry_errors=False):
    out = Path(config["output_dir"]) / backbone / name
    out.mkdir(parents=True, exist_ok=True)
    identity = run_identity(config, backbone, name)
    metadata_path = out / "run.json"
    if metadata_path.exists():
        if json.loads(metadata_path.read_text(encoding="utf-8"))["identity"] != identity:
            raise AssetError("Output belongs to different source/config/assets; use another output_dir")
    else:
        write_json(metadata_path, {"identity": identity, "backbone": backbone, "dataset": name,
                                  "profile": config.get('experiment_profile','paper-table1-gbfr-only'), "asset_policy": config.get('asset_policy', 'paper-exact'),
                                  "backbone_config": config["backbones"][backbone],
                                  "graph_sha256": sha256(config["graph"]), "sample_count": len(samples),
                                  'scheduling':{'example_concurrency':config.get('example_concurrency',1)},
                                  "evaluation": config["evaluation"]})
    predictions_path = out / "predictions.jsonl"
    previous = recover_journal(predictions_path)
    completed = {p["sample_id"]: p for p in previous}
    if len(completed) != len(previous) or set(completed)-{s["id"] for s in samples}:
        raise AssetError("Duplicate or unrelated stored predictions")
    if retry_errors:
        completed = {k: p for k, p in completed.items() if p["status"] != "error"}
        predictions_path.write_text("".join(dumps(p)+"\n" for p in completed.values()), encoding="utf-8")
    # Credentials are only needed after all asset checks and before actual inference.
    if len(completed) == len(samples):
        result = summarize(samples, list(completed.values()), config["evaluation"]["unspecified_decimals"])
        write_json(out / "metrics.json", result)
        return result
    client = ChatClient(config["backbones"][backbone], Path(config["cache_dir"]) / backbone)
    model = GBFR(graph, client, config.get("execution_timeout", 5))
    sem = asyncio.Semaphore(config.get("example_concurrency", 1))
    write_lock = asyncio.Lock()
    progress = len(completed)
    stop=asyncio.Event()
    fatal_error=None
    consecutive_api_errors=0

    async def one(sample):
        nonlocal progress,fatal_error,consecutive_api_errors
        if sample["id"] in completed:
            return
        async with sem:
            if stop.is_set():
                return
            try:
                # This is the complete model input. No ground truth, solution, negative
                # reason, function implementation or perturbation label is visible.
                pred = (await model.predict(sample["question"], sample["context"])).to_dict()
                consecutive_api_errors=0
            except Exception as exc:
                pred = {"status": "error", "value": None, "meta": {}, "precision": None,
                        "error_type": type(exc).__name__, "error": str(exc),
                        "trace": getattr(exc, "gbfr_trace", {})}
                status=getattr(exc,'status_code',None)
                systemic=isinstance(exc,APIError) and (status in {401,402,403,429}
                    or (status is not None and status>=500) or str(exc).startswith('Transport failure'))
                consecutive_api_errors=consecutive_api_errors+1 if systemic else 0
                if systemic and (status in {401,402,403} or consecutive_api_errors>=3):
                    fatal_error=exc
                    stop.set()
            pred["sample_id"] = sample["id"]
            async with write_lock:
                with predictions_path.open("a", encoding="utf-8") as stream:
                    stream.write(dumps(pred)+"\n")
                    stream.flush()
                completed[sample["id"]] = pred
                progress += 1
                print(f"{backbone}/{name}: {progress}/{len(samples)} status={pred['status']}", flush=True)
    try:
        await asyncio.gather(*(one(s) for s in samples))
    finally:
        usage_path = out / "api_usage.json"
        old_usage = json.loads(usage_path.read_text(encoding="utf-8")) if usage_path.exists() else []
        write_json(usage_path, old_usage + client.records)
        await client.close()
    result = summarize(samples, list(completed.values()), config["evaluation"]["unspecified_decimals"])
    write_json(out / "metrics.json", result)
    if fatal_error is not None:
        write_json(out/'interruption.json',{'reason':str(fatal_error),'status_code':getattr(fatal_error,'status_code',None),
            'completed':len(completed),'total':len(samples),'remaining':len(samples)-len(completed),
            'resume_command':'python -m gbfr.cli run --config configs/gpt56_sol.json --retry-errors'})
        raise fatal_error
    return result


def report(config: dict) -> str:
    lines = ["# GBFR 主实验", "", "仅包含表 1 的 GBFR 行。论文参考值不代表本地实测结果。", "",
             "| 骨干 | 数据集 | 本地 Total Acc. | 本地 Abst. Acc. | 论文 Total / Abst. | 状态 |",
             "|---|---|---:|---:|---:|---|"]
    if config.get('asset_policy') == RECONSTRUCTION_POLICY:
        lines[3:3] = ['资产采用论文方法重建，数据按预先冻结的数值任务规则调整；分母与论文不完全相同，参考值不作同集合直接比较。', '']
    if config.get('experiment_profile') == 'user-requested-backbone':
        lines[0] = '# GBFR 用户指定骨干实验'
        lines[2] = '本次骨干由用户指定，模型名称按实际配置显示；不将其标注为论文 GPT-5 或 Qwen3-14B。'
    for backbone in config['backbones']:
        for dataset in EXPECTED:
            reference=PAPER_RESULTS.get(backbone,{}).get(dataset)
            path = Path(config["output_dir"]) / backbone / dataset / "metrics.json"
            if path.exists():
                obj = json.loads(path.read_text(encoding="utf-8"))
                total, abst = f"{obj['total_accuracy']:.2f}", f"{obj['abstention_accuracy']:.2f}"
                status = "已完成" if obj["complete"] else f"未完成，错误 {obj['errors']}，缺失 {obj['missing']}"
            else:
                total = abst = "—"
                status = "尚未运行"
            reference_text=f'{reference[0]:.2f} / {reference[1]:.2f}' if reference else '—（用户指定骨干）'
            lines.append(f"| {backbone} | {dataset} | {total} | {abst} | {reference_text} | {status} |")
    text = "\n".join(lines)+"\n"
    target = Path(config["output_dir"]) / "main_results.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return text


async def run(config: dict, *, retry_errors=False):
    graph, datasets = preflight(config)
    try:
        for backbone in config["backbones"]:
            for name, samples in datasets.items():
                await run_cell(config, graph, name, samples, backbone, retry_errors=retry_errors)
    finally:
        report(config)
