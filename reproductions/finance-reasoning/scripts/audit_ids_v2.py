"""Audit actual ID-selector outputs and frozen settings without reading gold values."""
from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fr_repro.common import digest, read_json, sha256, write_json
from fr_repro.prompts import ID_JUDGE, candidate_ids, select_functions

root = Path(__file__).resolve().parents[1]
output = root / "runs/aiwanwu-gpt56sol-ids-v2"
manifest = read_json(output / "run_manifest.json")
freeze = read_json(root / "research/ids_v2_preregistered_protocol.json")
config = manifest["identity"]["config"]
lock = read_json(Path(config["data_dir"]) / "assets.lock.json")
assert config["judge_protocol"] == ID_JUDGE
assert manifest["identity"]["source"] == freeze["source"]
for name, expected in freeze["source"].items():
    assert sha256(root / "fr_repro" / name) == expected, name
assert sha256(root / "fr_repro/prompts.json") == freeze["original_templates_sha256"]
assert sha256(Path(config["data_dir"]) / "assets.lock.json") == freeze["asset_lock_sha256"]
for relative, expected in lock["files"].items():
    assert sha256(Path(config["data_dir"]) / relative) == expected, relative

records = []
for path in (output / "predictions").glob("*.json"):
    envelope = read_json(path)
    record = envelope["record"]
    assert envelope["digest"] == digest(record)
    assert record["run_id"] == manifest["run_id"]
    assert record["judge_protocol"] == ID_JUDGE
    records.append(record)
assert len(records) == len({r["question_id"] for r in records}) == 238
assert {r["question_id"] for r in records} == set(lock["question_ids"])
statuses = Counter(r["status"] for r in records)
assert not statuses["api_error"], "Resolve API errors before accepting the full rerun"
selections, backbones, cached_flags = Counter(), Counter(), Counter()
stage_count = 0
for record in records:
    assert set(record["stages"]) == {"query", "judge", "pot"}, record["question_id"]
    candidates = record["candidates"]
    assert len(candidates) == len({c["function_id"] for c in candidates}) == 30
    assert [c["reference_id"] for c in candidates] == candidate_ids(30)
    selected = select_functions(record["stages"]["judge"]["content"],
                                [c["function_id"] for c in candidates], judge_protocol=ID_JUDGE)
    assert selected == record["selected_ids"]
    selections[len(selected)] += 1
    for response in record["stages"].values():
        stage_count += 1
        backbones[response["model_returned"]] += 1
        cached_flags[response["cached"]] += 1
assert stage_count == 714 and backbones == {"gpt-5.6-sol": 714}
assert cached_flags[False] == 714 and not cached_flags[True], "This full rerun must not reuse earlier responses"
assert not statuses["protocol_error"]
write_json(root / "research/ids_v2_gold_free_run_audit.json", {
    "gold_values_read": False, "source_matches_preregistered_freeze": True,
    "data_assets_and_templates_unchanged": True, "all_238_identities_present": True,
    "candidate_binding_and_selection_validation": "passed for all 238 questions",
    "selector_format_failures": 0, "api_errors": 0,
    "saved_stage_responses": stage_count, "responses_reused_from_earlier_runs": 0,
    "stage_backbones": dict(backbones), "selected_function_count_distribution": dict(selections),
    "statuses": dict(statuses), "run_id": manifest["run_id"],
})
print("Gold-free audit passed: 238 identities, 714 fresh responses, valid candidate bindings, zero selector format failures.")
