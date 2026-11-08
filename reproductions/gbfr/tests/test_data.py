from gbfr.data import flatten_official
from gbfr.data import prepare_dataset, jsonl, write_json


def test_finqa_native_adapter_uses_full_document_and_no_solution_fields():
    rows = [{"id": "a", "pre_text": ["PRE"], "post_text": ["POST"],
             "table": [["Metric", "2024"], ["Revenue", "100"]],
             "qa": {"question": "Find revenue", "answer": "100", "program": "DO NOT PASS",
                    "gold_inds": {"bad": "DO NOT PASS"}}, "table_retrieved": "DO NOT PASS"}]
    record = flatten_official("FinQA", rows)[0]
    assert "PRE" in record["context"] and "POST" in record["context"] and "Revenue" in record["context"]
    assert "DO NOT PASS" not in record["context"] and "program" not in record


def test_finqa_prefers_original_presentation_table_for_accounting_signs():
    rows = [{"id": "a", "pre_text": [], "post_text": [],
             "table": [["Metric", "Value"], ["Cost", "-32 (32)"]],
             "table_ori": [["Metric", "Value"], ["Cost", "(32)"]],
             "qa": {"question": "Find cost", "answer": "-32"}}]
    record = flatten_official("FinQA", rows)[0]
    assert "(32)" in record["context"] and "-32 (32)" not in record["context"]


def test_tatqa_unwraps_singleton_and_preserves_explicit_scale():
    rows = [{"table": {"uid": "table", "table": [["A", "B"], ["Revenue", "2"]]},
             "paragraphs": [{"text": "Full paragraph"}], "questions": [
                 {"uid": "a", "question": "Find amount", "answer": ["2"], "answer_type": "span", "scale": "million"},
                 {"uid": "b", "question": "Find percent", "answer": 12, "answer_type": "arithmetic", "scale": "percent"},
                 {"uid": "c", "question": "Find both", "answer": ["1", "2"], "answer_type": "multi-span", "scale": ""}]}]
    result = flatten_official("TAT-QA", rows)
    assert result[0]["answer"] == "2" and result[0]["answer_meta"] == {"scale": "million"}
    assert result[1]["answer_meta"] == {"unit": "percentage"}
    assert result[2]["answer"] == ["1", "2"]


def test_full_finance_dataset_keeps_bool_and_only_original_question_fills_empty_context(tmp_path):
    root = tmp_path / "upstream"
    directory = root / "data/FinanceReasoning"
    question = "Is 10 greater than 5? Answer True or False."
    write_json(directory / "easy.json", [{"question": question, "context": "", "ground_truth": True}])
    write_json(directory / "medium.json", [])
    write_json(directory / "hard.json", [])
    write_json(directory / "financereasoning_nsdata.json", [])
    out = tmp_path / "processed"
    audit = prepare_dataset(root, "FinanceReasoning", out)
    records = jsonl(out / "FinanceReasoning.jsonl")
    assert audit["actual"]["original"] == 1 and audit["excluded"] == 0
    assert records[0]["answer"] is True and records[0]["answer_type"] == "boolean"
    assert records[0]["context"] == question
    assert records[0]["context_origin"] == "verbatim_question_for_empty_document"
