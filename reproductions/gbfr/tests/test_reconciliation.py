import pytest

from gbfr.reconciliation import recover_exclusion_indices, negative_lineage
from gbfr.types import AssetError


def test_exclusion_recovery_preserves_duplicate_multiplicity_and_documents_identity():
    row = {"question": "Find value", "context": "context", "table": "table", "answer": "text", "uid": "a"}
    twin = {**row, "uid": "b"}
    exclusions = [{"query": "Find value", "context": "context\ntable", "answer": "text"}]*2
    removed, proof = recover_exclusion_indices({"TAT-QA": [row, twin]}, exclusions)
    assert removed == {"TAT-QA": {0, 1}}
    assert [p["source_index"] for p in proof] == [0, 1]
    assert proof[0]["identical_remaining_copies"] == 2


def test_contextless_exclusion_requires_a_unique_question_label_pair():
    sources = {"FinQA": [{"question": "Q", "context": "C", "answer": "", "uid": "a"},
                          {"question": "Q", "context": "D", "answer": "12", "uid": "b"}]}
    removed, proof = recover_exclusion_indices(sources, [{"query": "Q", "answer": ""}])
    assert removed["FinQA"] == {0}
    assert proof[0]["method"] == "unique_question_label_no_context"
    sources["FinQA"][1]["answer"] = ""
    with pytest.raises(AssetError):
        recover_exclusion_indices(sources, [{"query": "Q", "answer": ""}])


def test_missing_exclusion_identity_never_fills_to_expected_count():
    with pytest.raises(AssetError):
        recover_exclusion_indices({"FinQA": []}, [{"query": "Q", "answer": ""}])


def test_negative_lineage_prefers_uid_for_repeated_questions():
    pos = [{"uid": "a", "question": "Same Q", "context": "A"},
           {"uid": "b", "question": "Same Q", "context": "B"}]
    neg = [{"uid": "b", "question": "Changed Q", "context": "B",
            "negative_sample_details": {"original_question": "Same Q"}}]
    result = negative_lineage(pos, neg)
    assert result["unique"] == 1 and result["links"][0]["source_candidates"] == [1]
