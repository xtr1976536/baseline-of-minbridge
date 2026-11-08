"""Uniform executor correction using frozen responses, with no HTTP client.

Run only after the entire original inference is complete. Preserve the raw run,
all original retrieval choices, and every model response verbatim.
"""
import asyncio
from collections import Counter
from contextvars import ContextVar
import copy
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fr_repro.assets import verify_assets
from fr_repro.common import digest, read_json, sha256, write_json
from fr_repro.runner import run

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "runs/aiwanwu-gpt56sol-c8"
manifest = read_json(ORIGINAL / "run_manifest.json")
source_config = manifest["identity"]["config"]
original_id = manifest["run_id"]
problems, labels, functions = verify_assets(source_config["data_dir"])
original_records = {}
for path in (ORIGINAL / "predictions").glob("*.json"):
    envelope = read_json(path)
    record = envelope["record"]
    assert envelope["digest"] == digest(record) and record["run_id"] == original_id
    original_records[record["question_id"]] = record
assert len(original_records) == len(problems) == 238
assert set(original_records) == {p.question_id for p in problems}
assert all(r["status"] != "api_error" for r in original_records.values()), "Resolve transport failures before replay"
assert sha256(Path(source_config["data_dir"]) / "assets.lock.json") == manifest["identity"]["asset_lock"]
assert sha256(Path(source_config["data_dir"]) / "index/manifest.json") == manifest["identity"]["index_manifest"]
assert sha256(ROOT / "fr_repro/prompts.json") == manifest["identity"]["prompts"]
changed = [name for name, expected in manifest["identity"]["source"].items()
           if sha256(ROOT / "fr_repro" / name) != expected]
assert set(changed) == {"execution.py", "worker.py"}, changed
functions_by_id = {f["function_id"]: f for f in functions}
active_question = ContextVar("active_question")


class FrozenResponseClient:
    def __init__(self):
        self.calls = Counter()

    async def complete(self, request, scope):
        question_id, stage = scope[1:]
        active_question.set(question_id)
        original = original_records[question_id]["stages"][stage]
        body = {"model": source_config["llm"]["model"], "messages": request,
                "stream": False, "n": 1, **source_config["llm"]["parameters"]}
        key = digest({"endpoint": source_config["llm"]["base_url"].rstrip("/"), "body": body,
                      "scope": [original_id, question_id, stage]})
        # No network fallback: a missing exact request/response is an error.
        cached = read_json(Path(source_config["cache_dir"]) / f"{key}.json")
        assert cached["identity"] == key and cached["response_digest"] == digest(cached["response"])
        assert cached["response"] == {k: v for k, v in original.items() if k != "cached"}
        self.calls[stage] += 1
        return {**cached["response"], "cached": True}


class FrozenRetrieval:
    def search(self, query, k):
        record = original_records[active_question.get()]
        assert query == record["stages"]["query"]["content"] and k == 30
        return [{**functions_by_id[c["function_id"]], "score": c["score"]} for c in record["candidates"]]


config = copy.deepcopy(source_config)
config["output_dir"] = str(ROOT / "runs/aiwanwu-gpt56sol-final")
config["execution_correction"] = {
    "frozen_original_run_id": original_id,
    "original_output_dir": str(ORIGINAL),
    "new_model_calls": 0,
    "reason": "Uniform fixes for ordinary underscore local variables, datetime internal import, and canonical numeric return formatting; no label-guided changes.",
}
write_json(ROOT / "configs/local.aiwanwu-gpt56sol-final.json", config)
client = FrozenResponseClient()
result = asyncio.run(run(config, client=client, retriever=FrozenRetrieval()))
assert result["complete"] and result["recorded"] == 238
final_records = {read_json(p)["record"]["question_id"]: read_json(p)["record"]
                 for p in (Path(config["output_dir"]) / "predictions").glob("*.json")}
for question_id, original in original_records.items():
    final = final_records[question_id]
    assert final["stages"].keys() == original["stages"].keys()
    for stage, response in original["stages"].items():
        assert {k: v for k, v in final["stages"][stage].items() if k != "cached"} == {k: v for k, v in response.items() if k != "cached"}
    assert final.get("candidates") == original.get("candidates")
    assert final.get("selected_ids") == original.get("selected_ids")
changes = [{"question_id": question_id, "old_status": original_records[question_id]["status"],
            "new_status": final["status"], "old_answer": original_records[question_id]["answer"], "new_answer": final["answer"]}
           for question_id, final in final_records.items()
           if (original_records[question_id]["status"], original_records[question_id]["answer"]) != (final["status"], final["answer"])]
write_json(ROOT / "research/execution_replay_audit.json", {
    "original_run_id": original_id, "changed_source_files": changed,
    "original_output_dir": str(ORIGINAL), "corrected_output_dir": config["output_dir"],
    "questions": 238, "new_paid_model_calls": 0, "replayed_stage_counts": dict(client.calls),
    "all_model_responses_verbatim": True, "all_retrieval_choices_unchanged": True,
    "executor_result_changes": changes, "final_metrics": result,
})
print("Uniform execution correction complete; all model responses/retrievals preserved; new paid calls: 0.")
print(result)
