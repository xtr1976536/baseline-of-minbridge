import asyncio
from pathlib import Path

import pytest

from gbfr.data import jsonl, write_json
from gbfr.runner import preflight, recover_journal, run_cell, run_identity, audit_datasets, validate_backbones, report
from gbfr.types import dumps
from gbfr.types import AssetError, Prediction


def test_user_backbone_requires_explicit_model_and_keeps_its_own_result_label(tmp_path):
    config={'experiment_profile':'user-requested-backbone','requested_backbone':'GPT-5.6 Sol',
            'requested_model':'gpt-5.6-sol','user_instruction':'Use GPT-5.6 Sol',
            'backbones':{'GPT-5.6 Sol':{'model':'gpt-5.6-sol'}},'output_dir':str(tmp_path)}
    validate_backbones(config)
    text=report(config)
    assert text.count('| GPT-5.6 Sol |')==4 and '| GPT-5 |' not in text
    assert text.count('—（用户指定骨干）')==4
    config['backbones']['GPT-5.6 Sol']['model']='a-different-model'
    with pytest.raises(AssetError):
        validate_backbones(config)
    with pytest.raises(AssetError):
        validate_backbones({'backbones':{'GPT-5.6 Sol':{'model':'gpt-5.6-sol'}}})


def test_missing_graph_is_detected_before_any_api_access(tmp_path):
    with pytest.raises(AssetError, match="Missing paper-validated"):
        preflight({"graph": str(tmp_path / "missing.json"),
                   "evaluation": {"rounding": "ROUND_HALF_UP", "unspecified_decimals": 2}})


def test_dataset_audit_surfaces_label_conflict_even_when_counts_match(tmp_path, monkeypatch):
    from gbfr import runner
    monkeypatch.setattr(runner, "EXPECTED", {"TAT-QA": {"original": 1, "counterfactual": 1, "total": 2}})
    rows = [{"id": "a", "question": "List two financial covenants", "context": "Data", "answer": "Ratio 2 and amount 100", "unanswerable": False},
            {"id": "b", "question": "Missing year", "context": "Data", "answer": None, "unanswerable": True}]
    (tmp_path / "TAT-QA.jsonl").write_text("".join(dumps(r)+"\n" for r in rows), encoding="utf-8")
    result = audit_datasets({"data_dir": str(tmp_path)})
    assert not result["all_datasets_ready"]
    assert result["datasets"]["TAT-QA"]["issues"] == ["unsupported_non_scalar_labels"]


def test_source_gold_disagreement_still_blocks_after_numeric_counts_match(tmp_path, monkeypatch):
    from gbfr import runner
    monkeypatch.setattr(runner, "EXPECTED", {"CFBenchmark": {"original": 1, "counterfactual": 0, "total": 1}})
    row = {"id": "a", "question": "Compute ROS", "context": "Data", "answer": "-0.037", "unanswerable": False}
    (tmp_path / "CFBenchmark.jsonl").write_text(dumps(row)+"\n", encoding="utf-8")
    write_json(tmp_path / "manifest.json", {"datasets": {"CFBenchmark": {
        "unresolved_gold_disagreements": [{"index": 18, "official_answer": "-270.2702", "gbfr_answer": "-0.037"}]}}})
    result = audit_datasets({"data_dir": str(tmp_path)})
    assert result["datasets"]["CFBenchmark"]["issues"] == ["unresolved_source_gold_disagreements"]


def test_journal_repairs_only_torn_final_line(tmp_path):
    path = tmp_path / "predictions.jsonl"
    path.write_bytes(b'{"sample_id":"a"}\n{"sample_')
    assert recover_journal(path) == [{"sample_id": "a"}]
    assert path.read_bytes() == b'{"sample_id":"a"}\n'
    path.write_bytes(b'bad\n{"sample_id":"a"}\n')
    with pytest.raises(AssetError):
        recover_journal(path)


def test_effective_endpoint_is_part_of_resume_identity(tmp_path, monkeypatch):
    lock = tmp_path / "lock.json"
    lock.write_text("{}")
    config = {"backbones": {"GPT-5": {"model": "gpt-5", "base_url": "url-a", "base_url_env": "TEST_GBFR_URL"}},
              "asset_lock": str(lock), "evaluation": {"unspecified_decimals": 2}}
    first = run_identity(config, "GPT-5", "FinQA")
    monkeypatch.setenv("TEST_GBFR_URL", "url-b")
    assert first != run_identity(config, "GPT-5", "FinQA")


def test_runner_strips_gold_and_resumes_without_recomputing(graph, tmp_path, monkeypatch):
    from gbfr import runner
    calls = []
    class FakeClient:
        def __init__(self, *args):
            self.records = []
        async def close(self):
            pass
    async def predict(self, question, context):
        calls.append((question, context))
        return Prediction("answered", 40, {}, "unknown", {})
    monkeypatch.setattr(runner, "ChatClient", FakeClient)
    monkeypatch.setattr(runner.GBFR, "predict", predict)
    asset = tmp_path / "graph.json"
    asset.write_text("{}")
    lock = tmp_path / "lock.json"
    lock.write_text("{}")
    config = {"output_dir": str(tmp_path / "out"), "cache_dir": str(tmp_path / "cache"),
              "graph": str(asset), "asset_lock": str(lock), "evaluation": {"unspecified_decimals": 2},
              "backbones": {"GPT-5": {"model": "gpt-5"}}}
    samples = [{"id": "a", "question": "Find profit", "context": "Data only", "answer": 40,
                "unanswerable": False, "solution": "MUST NOT BE SENT"}]
    asyncio.run(run_cell(config, graph, "FinQA", samples, "GPT-5"))
    asyncio.run(run_cell(config, graph, "FinQA", samples, "GPT-5"))
    assert calls == [("Find profit", "Data only")]
    predictions = jsonl(tmp_path / "out" / "GPT-5" / "FinQA" / "predictions.jsonl")
    assert len(predictions) == 1 and predictions[0]["status"] == "answered"


def test_billing_stop_preserves_partial_journal_and_full_denominator(graph,tmp_path,monkeypatch):
    from gbfr import runner
    from gbfr.llm import APIError
    calls=[]
    class Client:
        def __init__(self,*args):self.records=[]
        async def close(self):pass
    async def predict(self,question,context):
        calls.append(question)
        raise APIError('Chat API returned HTTP 402; task=OQA',status_code=402)
    monkeypatch.setattr(runner,'ChatClient',Client)
    monkeypatch.setattr(runner.GBFR,'predict',predict)
    for file in ['graph.json','lock.json']:(tmp_path/file).write_text('{}')
    config={'output_dir':str(tmp_path/'out'),'cache_dir':str(tmp_path/'cache'),
        'graph':str(tmp_path/'graph.json'),'asset_lock':str(tmp_path/'lock.json'),
        'evaluation':{'unspecified_decimals':2},'example_concurrency':1,
        'backbones':{'GPT-5':{'model':'gpt-5'}}}
    samples=[{'id':str(i),'question':str(i),'context':'Data','answer':1,'unanswerable':False} for i in range(4)]
    with pytest.raises(APIError):asyncio.run(run_cell(config,graph,'FinQA',samples,'GPT-5'))
    assert len(calls)==1
    folder=tmp_path/'out/GPT-5/FinQA'
    assert len(jsonl(folder/'predictions.jsonl'))==1
    metrics=__import__('json').loads((folder/'metrics.json').read_text())
    assert metrics['n']==4 and metrics['missing']==3 and metrics['errors']==1 and not metrics['complete']
