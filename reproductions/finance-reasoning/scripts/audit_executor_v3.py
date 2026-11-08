"""Audit the full run, exact request cache, units and freeze without gold comparisons."""
from collections import Counter
from decimal import Decimal
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fr_repro.assets import Problem
from fr_repro.common import digest, read_json, sha256, write_json
from fr_repro.execution import percentage_output_requested
from fr_repro.prompts import ID_JUDGE, candidate_ids, judge_response_format, messages, select_functions
from fr_repro.runner import run_identity

root = Path(__file__).resolve().parents[1]
output = root / "runs/aiwanwu-gpt56sol-executor-v3"
manifest = read_json(output / "run_manifest.json")
freeze = read_json(root / "research/executor_v3_preregistered_protocol.json")
config = manifest["identity"]["config"]
assert run_identity(config) == manifest
assert manifest["identity"]["source"] == freeze["source"]
assert config["execution_protocol"] == "question-unit-aware-v3"
assert config["judge_protocol"] == ID_JUDGE
for name, expected in freeze["source"].items():
    assert sha256(root / "fr_repro" / name) == expected, name
assert sha256(root / "fr_repro/prompts.json") == freeze["original_templates_sha256"]
data = Path(config["data_dir"])
assert sha256(data / "assets.lock.json") == freeze["asset_lock_sha256"]
assert sha256(data / "index/manifest.json") == freeze["index_manifest_sha256"]
index = read_json(data / "index/manifest.json")
assert sha256(data / "index/embeddings.npy") == index["embedding_sha256"]
lock = read_json(data / "assets.lock.json")
for relative, expected in lock["files"].items():
    assert sha256(data / relative) == expected, relative
# Only these three input fields are accessed; no gold or standard solution is used.
problems = {r["question_id"]: Problem(r["question_id"], r["question"], r.get("context", ""))
            for r in read_json(data / "raw/hard.json")}
functions = {f["function_id"]: f for f in read_json(data / "raw/functions-article-all.json")}
records = []
for path in (output / "predictions").glob("*.json"):
    envelope = read_json(path)
    record = envelope["record"]
    assert envelope["digest"] == digest(record) and record["run_id"] == manifest["run_id"]
    records.append(record)
assert len(records) == len({r["question_id"] for r in records}) == 238
assert {r["question_id"] for r in records} == set(lock["question_ids"])
statuses, backbones, cache_flags, selections = Counter(), Counter(), Counter(), Counter()
stage_count, percent_literals = 0, 0
for record in records:
    statuses[record["status"]] += 1
    problem = problems[record["question_id"]]
    assert record["answer_output_contract"]["percentage_literal_allowed"] is percentage_output_requested(problem.question)
    assert set(record["stages"]) == {"query", "judge", "pot"}
    candidates = record["candidates"]
    assert len(candidates) == len({c["function_id"] for c in candidates}) == 30
    assert [c["reference_id"] for c in candidates] == candidate_ids(30)
    selected = select_functions(record["stages"]["judge"]["content"],
                                [c["function_id"] for c in candidates], judge_protocol=ID_JUDGE)
    assert selected == record["selected_ids"]
    selections[len(selected)] += 1
    requests = {
        "query": messages("query", problem),
        "judge": messages("judge", problem, [functions[c["function_id"]]["function"] for c in candidates], judge_protocol=ID_JUDGE),
        "pot": messages("pot", problem, [functions[identifier]["function"] for identifier in selected]),
    }
    for stage, response in record["stages"].items():
        body = {"model": config["llm"]["model"], "messages": requests[stage], "stream": False, "n": 1, **config["llm"]["parameters"]}
        if stage == "judge":
            body["response_format"] = judge_response_format(30)
        key = digest({"endpoint": config["llm"]["base_url"].rstrip("/"), "body": body,
                      "scope": [manifest["run_id"], problem.question_id, stage]})
        cached = read_json(Path(config["cache_dir"]) / f"{key}.json")
        assert cached["identity"] == key and cached["response_digest"] == digest(cached["response"])
        assert cached["response"] == {k: v for k, v in response.items() if k != "cached"}
        stage_count += 1
        backbones[response["model_returned"]] += 1
        cache_flags[response["cached"]] += 1
    if record.get("return_representation") == "percentage_points":
        assert record["answer_output_contract"]["percentage_literal_allowed"] is True
        text = record["raw_return"].strip()
        assert text.endswith("%")
        assert record["answer"] == float(Decimal(text[:-1].strip()))
        percent_literals += 1
assert not statuses["api_error"] and not statuses["protocol_error"]
assert stage_count == 714 and backbones == {"gpt-5.6-sol": 714}
write_json(root / "research/executor_v3_gold_free_run_audit.json", {
    "standard_answers_used_for_audit": False,
    "source_config_and_dependencies_match_preregistered_run": True,
    "data_assets_and_prompts_unchanged": True, "all_238_identities_present": True,
    "all_714_exact_requests_verified_against_current_run_scoped_cache": True,
    "previous_experiment_responses_reused": 0,
    "current_run_cache_hits_during_transport_recovery": cache_flags[True],
    "saved_successful_stage_responses": stage_count, "backbones": dict(backbones),
    "percentage_unit_contracts_verified_for_all_questions": True,
    "accepted_percentage_literals": percent_literals, "percentage_magnitude_preserved": True,
    "selector_format_failures": 0, "api_errors": 0, "statuses": dict(statuses),
    "selected_function_count_distribution": dict(selections), "run_id": manifest["run_id"],
})
print("Full gold-free audit passed: 238 identities, 714 current-run responses, frozen rules, exact candidate and unit bindings.")
