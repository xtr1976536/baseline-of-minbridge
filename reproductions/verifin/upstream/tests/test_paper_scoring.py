import copy
import csv
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.paper_scoring import (
    ScoringValidationError,
    candidate_is_correct,
    load_jsonl,
    load_manual_adjudications,
    load_policy,
    main,
    score_all,
    validate_dataset_ids,
)


RESULT_METADATA_DIR = ROOT / "results"
if not (RESULT_METADATA_DIR / "scoring_policy.json").is_file():
    RESULT_METADATA_DIR = ROOT / "publication_assets_source/results"
POLICY_PATH = RESULT_METADATA_DIR / "scoring_policy.json"
ADJUDICATION_PATH = RESULT_METADATA_DIR / "manual_adjudications.json"


@pytest.fixture(scope="module")
def policy():
    return load_policy(POLICY_PATH)


@pytest.fixture(scope="module")
def adjudications():
    return load_manual_adjudications(ADJUDICATION_PATH)


def _candidate(record_id, value, gold):
    return {
        "id": record_id,
        "claimed_value": value,
        "gold_answer": gold,
        "status": "VERIFIED",
    }


def test_manual_adjudication_is_candidate_specific(policy, adjudications):
    correct = _candidate("financebench_id_00882", 8400.0, "$8.4 billion")
    wrong = _candidate("financebench_id_00882", 4200.0, "$8.4 billion")
    assert candidate_is_correct(correct, "financebench", policy, adjudications)
    assert not candidate_is_correct(wrong, "financebench", policy, adjudications)


def test_manual_targets_replace_misleading_gold_numbers(policy, adjudications):
    requested_total = _candidate(
        "financebench_id_02024", 1959.0, "Components were 1097 and 862."
    )
    component_only = _candidate(
        "financebench_id_02024", 862.0, "Components were 1097 and 862."
    )
    assert candidate_is_correct(
        requested_total, "financebench", policy, adjudications
    )
    assert not candidate_is_correct(
        component_only, "financebench", policy, adjudications
    )


def test_reviewed_case_can_have_multiple_allowed_targets(policy, adjudications):
    assert candidate_is_correct(
        _candidate("financebench_id_01936", 87.0, "87 percent"),
        "financebench",
        policy,
        adjudications,
    )
    assert candidate_is_correct(
        _candidate("financebench_id_01936", 93.0, "87 percent"),
        "financebench",
        policy,
        adjudications,
    )
    assert not candidate_is_correct(
        _candidate("financebench_id_01936", 50.0, "87 percent"),
        "financebench",
        policy,
        adjudications,
    )


def test_dataset_denominators_are_exact(policy):
    for dataset_key, spec in policy["datasets"].items():
        rows = load_jsonl(ROOT / spec["source_path"])
        ids = validate_dataset_ids(rows, dataset_key, spec)
        assert len(ids) == spec["denominator"]


def test_wrong_denominator_is_rejected(policy):
    spec = copy.deepcopy(policy["datasets"]["financebench"])
    spec["denominator"] = 66
    rows = load_jsonl(ROOT / spec["source_path"])
    with pytest.raises(ScoringValidationError, match="expected 66"):
        validate_dataset_ids(rows, "financebench", spec)


def test_all_canonical_counts_match_manifest(policy, adjudications):
    results = score_all(ROOT, policy, adjudications)
    available = [row for row in results if row["status"] == "available"]
    assert len(available) == 20
    by_key = {
        (row["dataset"], row["group"], row["run"]): tuple(
            row[name] for name in ("TA", "FA", "TR", "FR", "AB")
        )
        for row in available
    }
    assert by_key[("financebench", "answer_models", "qwen3-30b")] == (
        24,
        0,
        20,
        8,
        15,
    )
    assert by_key[("financebench", "answer_models", "llama-3.1-8b")] == (
        10,
        0,
        17,
        12,
        28,
    )
    expected_baselines = {
        ("xbrlfiling", "baselines", "direct-llm"): (508, 92, 0, 0, 0),
        ("xbrlfiling", "baselines", "llm-judge"): (195, 26, 66, 313, 0),
        ("xbrlfiling", "baselines", "judge-plus-formula"): (480, 75, 17, 28, 0),
        ("xbrlfiling", "baselines", "program-of-thought"): (444, 6, 79, 49, 22),
        ("financebench", "baselines", "direct-llm"): (46, 18, 0, 0, 3),
        ("financebench", "baselines", "llm-judge"): (22, 7, 11, 24, 3),
        ("financebench", "baselines", "judge-plus-formula"): (34, 13, 5, 12, 3),
        ("financebench", "baselines", "program-of-thought"): (40, 4, 14, 6, 3),
    }
    for key, expected in expected_baselines.items():
        assert by_key[key] == expected


def test_canonical_baselines_use_one_raw_answer_pool(policy):
    protocol = policy["baseline_protocol"]
    assert protocol["name"] == "one-pool shared-answer evaluation"
    assert protocol["shared_field"] == "raw_answer"
    assert protocol["shared_field_matches_all_rows"] is True

    expected = {
        "xbrlfiling": {
            "source": "results/mc_calc_detsmt_v2_haiku/results.jsonl",
            "recovered": 7,
            "paths": {
                "direct-llm": "results/onepool/xbrl_none",
                "llm-judge": "results/onepool/xbrl_judge",
                "judge-plus-formula": "results/onepool/xbrl_judge_formula",
                "program-of-thought": "results/onepool/xbrl_pot",
            },
        },
        "financebench": {
            "source": "results/fb_detsmt_v2_haiku/results.jsonl",
            "recovered": 6,
            "paths": {
                "direct-llm": "results/onepool/fb_none",
                "llm-judge": "results/onepool/fb_judge",
                "judge-plus-formula": "results/onepool/fb_judge_formula",
                "program-of-thought": "results/onepool/fb_pot",
            },
        },
    }

    for dataset, spec in expected.items():
        assert protocol["answer_generator_run_by_dataset"][dataset] == spec["source"]
        source_rows = {
            row["id"]: row for row in load_jsonl(ROOT / spec["source"])
        }
        for run, relative_path in spec["paths"].items():
            run_spec = policy["canonical_runs"][dataset]["baselines"][run]
            assert run_spec["source_path"] == relative_path
            baseline_rows = load_jsonl(ROOT / relative_path / "results.jsonl")
            assert {
                row["id"]: row.get("raw_answer") for row in baseline_rows
            } == {
                row_id: row.get("raw_answer") for row_id, row in source_rows.items()
            }
            recovered = sum(
                source_rows[row["id"]].get("claimed_value") is None
                and row.get("claimed_value") is not None
                for row in baseline_rows
            )
            assert recovered == spec["recovered"]

    finance_direct = load_jsonl(
        ROOT / "results/onepool/fb_none/results.jsonl"
    )
    unparsed = [row for row in finance_direct if row.get("claimed_value") is None]
    assert len(unparsed) == 3
    assert any("zero" in row.get("raw_answer", "").lower() for row in unparsed)


def test_cli_prints_exact_counts(capsys):
    assert main(["--repo-root", str(ROOT)]) == 0
    output = capsys.readouterr().out
    assert "financebench\tanswer_models\tqwen3-30b\t24\t0\t20\t8\t15" in output
    assert "financebench\tanswer_models\tllama-3.1-8b\t10\t0\t17\t12\t28" in output
    assert "financebench\tanswer_models\tgpt-5.5\tNone\tNone\tNone\tNone\tNone" in output


def test_frozen_paper_metrics_match_recomputed_counts(policy, adjudications):
    computed = {
        (row["dataset"], row["group"], row["run"]): row
        for row in score_all(ROOT, policy, adjudications)
    }
    with (RESULT_METADATA_DIR / "paper_metrics.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        frozen = list(csv.DictReader(handle))
    assert len(frozen) == len(computed)
    for row in frozen:
        scored = computed[(row["dataset"], row["group"], row["run"])]
        for outcome in ("TA", "FA", "TR", "FR", "AB"):
            expected = "" if scored[outcome] is None else str(scored[outcome])
            assert row[outcome] == expected
