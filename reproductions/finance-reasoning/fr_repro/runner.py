"""End-to-end three-stage inference and frozen-denominator reporting."""
from __future__ import annotations

import asyncio
from collections import Counter
from contextlib import contextmanager
import importlib.metadata
import os
from pathlib import Path
import platform

from .assets import verify_assets
from .client import APIError, ChatClient
from .common import digest, read_json, sha256, write_json
from .execution import execute, percentage_output_requested
from .metrics import summarize
from .prompts import ID_JUDGE, LEGACY_JUDGE, candidate_ids, judge_response_format, messages, select_functions
from .retrieval import FunctionRetriever, verify_index


async def solve(problem, retriever, client, *, run_id, timeout, judge_protocol=LEGACY_JUDGE):
    trace = {"question_id": problem.question_id, "run_id": run_id, "stages": {}, "judge_protocol": judge_protocol}
    percentage_output = percentage_output_requested(problem.question)
    trace["answer_output_contract"] = {"percentage_literal_allowed": percentage_output,
                                       "source": "explicit unit request in the original question"}
    try:
        query = await client.complete(messages("query", problem), [run_id, problem.question_id, "query"])
        trace["stages"]["query"] = query
        candidates = retriever.search(query["content"], 30)
        if len(candidates) != 30 or len({c["function_id"] for c in candidates}) != 30:
            raise RuntimeError("Retriever did not supply 30 unique functions")
        trace["candidates"] = [{"function_id": c["function_id"], "score": c["score"]} for c in candidates]
        judge_kwargs = {}
        if judge_protocol == ID_JUDGE:
            for reference_id, candidate in zip(candidate_ids(len(candidates)), trace["candidates"]):
                candidate["reference_id"] = reference_id
            judge_kwargs["response_format"] = judge_response_format(len(candidates))
        judge = await client.complete(messages("judge", problem, [c["function"] for c in candidates], judge_protocol=judge_protocol),
                                      [run_id, problem.question_id, "judge"], **judge_kwargs)
        trace["stages"]["judge"] = judge
        selected = select_functions(judge["content"], candidates, judge_protocol=judge_protocol)
        trace["selected_ids"] = [c["function_id"] for c in selected]
        pot = await client.complete(messages("pot", problem, [c["function"] for c in selected]),
                                    [run_id, problem.question_id, "pot"])
        trace["stages"]["pot"] = pot
        result = await asyncio.to_thread(execute, pot["content"], timeout, percentage_output=percentage_output)
        return {**trace, **result}
    except APIError as exc:
        return {**trace, "status": "api_error", "answer": None, "error": str(exc), "fatal_api_error": exc.fatal}
    except ValueError as exc:
        # Invalid query/judge/program output is a failed model attempt, not a
        # transport retry or a silently substituted retrieval method.
        return {**trace, "status": "protocol_error", "answer": None, "error": str(exc)}


def preflight(config):
    problems, labels, functions = verify_assets(config["data_dir"])
    verify_index(config["data_dir"], functions, config["retriever"])
    return problems, labels, functions


def run_identity(config):
    root = Path(__file__).parent
    resolved = {**config, "llm": {**config["llm"], "base_url": os.environ.get(config["llm"].get("base_url_env", ""), config["llm"]["base_url"])}}
    versions = {name: importlib.metadata.version(name) for name in
                ["httpx", "numpy", "torch", "transformers", "huggingface-hub", "sympy", "scipy", "numpy-financial"]}
    identity = {"config": resolved, "asset_lock": sha256(Path(config["data_dir"]) / "assets.lock.json"),
                "index_manifest": sha256(Path(config["data_dir"]) / "index/manifest.json"),
                "source": {p.name: sha256(p) for p in sorted(root.glob("*.py"))},
                "prompts": sha256(root / "prompts.json"), "dependencies": versions, "python": platform.python_version()}
    return {"run_id": digest(identity), "identity": identity,
            "experiment": f"Table 5 selected method / {config['llm']['model']} / Hard / PoT"}


def bind_run(output_dir, identity):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    path = output / "run_manifest.json"
    if path.exists():
        if read_json(path) != identity:
            raise ValueError("Run configuration/code/assets/endpoint changed: select a new output_dir")
    else:
        if any((output / "predictions").glob("*.json")):
            raise ValueError("Unbound predictions exist; select a new output_dir")
        write_json(path, identity)


@contextmanager
def output_lock(output_dir):
    """OS advisory lock released automatically after interruption/process death."""
    path = Path(output_dir) / ".run.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = path.open("a+b")
    try:
        stream.seek(0)
        if os.name == "nt":
            import msvcrt
            if path.stat().st_size == 0:
                stream.write(b"0")
                stream.flush()
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        stream.close()


def load_records(output_dir, run_id, labels):
    records = []
    for path in sorted((Path(output_dir) / "predictions").glob("*.json")):
        envelope = read_json(path)
        record = envelope["record"]
        if envelope.get("digest") != digest(record) or record.get("run_id") != run_id:
            raise ValueError("Prediction checksum or run identity changed")
        if record["question_id"] not in labels or path.stem != digest(record["question_id"]):
            raise ValueError("Prediction has unknown question identity")
        records.append(record)
    summarize(records, labels)
    return records


def save_record(output_dir, record):
    write_json(Path(output_dir) / "predictions" / f"{digest(record['question_id'])}.json",
               {"record": record, "digest": digest(record)})


def report(output_dir, records, labels, *, scripted=False, model_name="gpt-4o-2024-11-20", judge_protocol=LEGACY_JUDGE):
    summary = summarize(records, labels)
    summary["statuses"] = dict(Counter(r["status"] for r in records))
    usage = Counter()
    for record in records:
        for response in record["stages"].values():
            for key, value in response.get("usage", {}).items():
                if type(value) in (int, float):
                    usage[key] += value
    summary["logical_stage_usage"] = dict(usage)
    summary["backbone_requested"] = model_name
    summary["judge_protocol"] = judge_protocol
    summary["model_ids_returned"] = dict(Counter(response.get("model_returned", "not_reported")
        for record in records for response in record["stages"].values()))
    summary["paper_backbone_match_requested"] = model_name == "gpt-4o-2024-11-20"
    summary["is_performance_result"] = summary["complete"] and not scripted
    summary["status"] = "offline_protocol_only" if scripted else ("complete" if summary["complete"] else "partial_do_not_report_as_final")
    if scripted:
        summary["accuracy"] = None
        summary["correct"] = None
    write_json(Path(output_dir) / "metrics.json", summary)
    accuracy = f"{100*summary['accuracy']:.2f}%" if summary["is_performance_result"] else "not measured (scripted)" if scripted else "pending"
    text = ("# FinanceReasoning Table 5 selected main method\n\n"
            f"Backbone requested: `{model_name}`. LLM-instructed function retrieval + LLM judge + PoT; Hard split.\n\n"
            f"Selector output protocol: `{judge_protocol}`.\n\n"
            "| Method | Correct / full denominator | Local accuracy | Paper GPT-4o reference |\n"
            "|---|---:|---:|---:|\n"
            f"| Selected method with {model_name} | {summary['correct'] if not scripted else 'not measured'} / {summary['expected']} | {accuracy} | 91.60% |\n\n"
            f"Run status: {summary['status']}. Recorded: {summary['recorded']}; API failures: {summary['api_errors']}.\n\n"
            "The paper reference uses GPT-4o; a substituted backbone is a user-authorized method reproduction, not an identical-backbone replication. "
            "Invalid model outputs and code execution failures count as incorrect; "
            "transport failures or unfinished questions prevent a final report. No sign, percentage, or unit rescaling is used by the scorer.\n")
    Path(output_dir, "main_results.md").write_text(text, encoding="utf-8")
    return summary


async def run(config, *, limit=None, retry_errors=False, client=None, retriever=None):
    problems, labels, functions = preflight(config)
    identity = run_identity(config)
    with output_lock(config["output_dir"]):
        bind_run(config["output_dir"], identity)
        records = load_records(config["output_dir"], identity["run_id"], labels)
        previous = {r["question_id"]: r for r in records}
        pending = [p for p in problems if p.question_id not in previous or
                   (retry_errors and previous[p.question_id]["status"] == "api_error")]
        if limit is not None:
            if limit < 1:
                raise ValueError("limit must be positive")
            pending = pending[:limit]
        if not pending:
            return report(config["output_dir"], records, labels, scripted=config.get("execution_mode") == "scripted", model_name=config["llm"]["model"], judge_protocol=config.get("judge_protocol", LEGACY_JUDGE))
        own_client = client is None
        client = client or ChatClient(config["llm"], config["cache_dir"])
        try:
            retriever = retriever or FunctionRetriever(config["data_dir"], functions, config["retriever"])
            semaphore = asyncio.Semaphore(config.get("example_concurrency", 2))
            async def one(problem):
                async with semaphore:
                    record = await solve(problem, retriever, client, run_id=identity["run_id"],
                                         timeout=config.get("execution_timeout_seconds", 10), judge_protocol=config.get("judge_protocol", LEGACY_JUDGE))
                    save_record(config["output_dir"], record)
                    previous[problem.question_id] = record
                    print(f"{len(previous)}/{len(problems)} {problem.question_id}: {record['status']}", flush=True)
                    if record.get("fatal_api_error"):
                        raise APIError("Run halted on a permanent API error", fatal=True)
            tasks = [asyncio.create_task(one(p)) for p in pending]
            try:
                await asyncio.gather(*tasks)
            except APIError:
                pass  # Keep the saved error and unfinished rows for a later resume.
            finally:
                for task in tasks:
                    if not task.done():
                        task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
            return report(config["output_dir"], list(previous.values()), labels, scripted=config.get("execution_mode") == "scripted", model_name=config["llm"]["model"], judge_protocol=config.get("judge_protocol", LEGACY_JUDGE))
        finally:
            if own_client:
                await client.close()
