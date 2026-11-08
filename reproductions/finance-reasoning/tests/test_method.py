import asyncio
from dataclasses import asdict
import json
from pathlib import Path

import httpx
import numpy as np
import pytest

from fr_repro.assets import Problem, function_description, load_inputs
from fr_repro.client import APIError, ChatClient
from fr_repro.common import digest, read_json, write_json
from fr_repro.execution import execute
from fr_repro.metrics import correct, summarize
from fr_repro.prompts import messages, select_functions
from fr_repro.runner import bind_run, load_records, output_lock, report, save_record, solve

ROOT = Path(__file__).resolve().parents[1]


def test_all_official_assets_are_preserved_and_inference_objects_omit_labels():
    problems, labels, functions = load_inputs(ROOT / "data")
    assert len(problems) == 238 and len(functions) == 3133
    assert sum(type(v) is bool for v in labels.values()) == 3
    assert sum(not p.context.strip() for p in problems) == 14
    assert set(asdict(problems[0])) == {"question_id", "question", "context"}
    assert "Args:" not in function_description(functions[0]["function"])


@pytest.mark.parametrize("pred,gold,expected", [
    (100.2, 100, True), (100.20001, 100, False), (-100, 100, False), (0.1, 10, False),
    (10000000, 10, False), (0, 0, True), (1e-12, 0, False), (True, True, True),
    (1, True, False), (True, 1, False), ([10], 10, False), ("10", 10, False),
    (float("nan"), 10, False), (-100.2, -100, True),
])
def test_strict_scoring(pred, gold, expected):
    assert correct(pred, gold) is expected


def test_ordered_judge_and_no_silent_top3_fallback():
    candidates = list(range(30))
    raw = "[" + ", ".join("USEFUL" if i % 2 else "USELESS" for i in candidates) + "]"
    assert select_functions(raw, candidates) == [1, 3, 5]
    assert select_functions("["+", ".join(["USELESS"]*30)+"]", candidates) == []
    for invalid in ["[USEFUL]", "Here is the result: " + raw, "[USEFUL, maybe]"]:
        with pytest.raises(ValueError):
            select_functions(invalid, candidates)


@pytest.mark.parametrize("program,expected", [
    ("```python\ndef solution():\n    return 123.4\n```", 123.4),
    ("    amount = 120 * 1.35\n    return round(amount * .98 - (amount * .98 - 120 - 6) * .2 - 120, 2)\n```", 32.21),
    ("def solution():\n    import numpy_financial as nf\n    return nf.npv(.1, [-100, 60, 60])", 4.132231404958667),
    ("def solution():\n    from decimal import Decimal\n    return Decimal('0.1') + Decimal('0.2')", 0.3),
    ("def solution():\n    import numpy as np\n    return np.sum([1, 2, 3])", 6),
    ("def solution():\n    return 5 > 4", True),
    ("def solution():\n    from scipy.optimize import newton\n    return newton(lambda x: x*x - 4, 3)", 2),
    ("def solution():\n    from scipy.stats import norm\n    return norm.cdf(0)", .5),
    ("def solution():\n    from datetime import date\n    return (date(2025, 1, 2) - date(2025, 1, 1)).days", 1),
])
def test_math_execution(program, expected):
    result = execute(program)
    assert result["status"] == "ok", result
    assert result["answer"] == pytest.approx(expected)


@pytest.mark.parametrize("code", [
    "def solution():\n    import os\n    return os.environ.get('FR_GPT4O_API_KEY')",
    "def solution():\n    return eval('1+1')",
    "def solution():\n    import numpy as np\n    return np.load('secrets.npy')",
    "def solution():\n    return (1).__class__",
    "def solution():\n    return [1, 2]",
    "def solution():\n    return '10%'",
    "def solution():\n    return 1/0",
])
def test_invalid_program_is_incorrect_without_repair(code):
    result = execute(code)
    assert result["status"] in ("invalid_program", "execution_error") and result["answer"] is None


def test_timeout():
    result = execute("def solution():\n    while True:\n        pass", timeout=.3)
    assert result["status"] == "execution_error"


class FakeRetriever:
    def search(self, query, k):
        assert query == "cash flow query" and k == 30
        return [{"function_id": f"f{i}", "function": f"def cash{i}(x): return x", "score": 30-i} for i in range(30)]


class FakeClient:
    def __init__(self, malformed=False):
        self.calls = []
        self.malformed = malformed

    async def complete(self, request, scope):
        self.calls.append((request, scope))
        answer = {"query": "cash flow query", "judge": "["+", ".join(["USEFUL"]*30)+"]",
                  "pot": "def solution():\n    return 32.21"}[scope[-1]]
        if self.malformed and scope[-1] == "judge":
            answer = "[USEFUL]"
        return {"content": answer, "usage": {}, "cached": False}


def test_three_stage_path_uses_context_and_at_most_three_functions():
    client = FakeClient()
    problem = Problem("q", "Net return?", "Original confidential context")
    result = asyncio.run(solve(problem, FakeRetriever(), client, run_id="r", timeout=10))
    assert result["status"] == "ok" and result["answer"] == 32.21
    assert result["selected_ids"] == ["f0", "f1", "f2"]
    assert [s[-1] for _, s in client.calls] == ["query", "judge", "pot"]
    for request, _ in client.calls:
        assert "Original confidential context" in request[1]["content"]
        assert "ground_truth" not in str(request) and "python_solution" not in str(request)
    assert "def cash2" in client.calls[-1][0][1]["content"]
    assert "def cash3" not in client.calls[-1][0][1]["content"]


def test_bad_judge_is_a_single_failed_attempt():
    client = FakeClient(malformed=True)
    result = asyncio.run(solve(Problem("q", "Question", ""), FakeRetriever(), client, run_id="r", timeout=10))
    assert result["status"] == "protocol_error" and len(client.calls) == 2


def test_full_denominator_and_api_errors_do_not_produce_final_accuracy(tmp_path):
    labels = {"q1": 10, "q2": 20, "q3": 30}
    records = [{"question_id": "q1", "answer": 10, "status": "ok", "stages": {}},
               {"question_id": "q2", "answer": None, "status": "api_error", "stages": {}}]
    result = report(tmp_path, records, labels)
    assert result["accuracy"] == 1/3 and not result["complete"]
    assert "pending" in (tmp_path / "main_results.md").read_text()
    records[1]["status"] = "execution_error"
    records.append({"question_id": "q3", "answer": 30, "status": "ok", "stages": {}})
    assert summarize(records, labels)["complete"]
    scripted = report(tmp_path, records, labels, scripted=True)
    assert scripted["accuracy"] is None and not scripted["is_performance_result"]


def test_resume_refuses_changed_code_assets_or_prediction(tmp_path):
    bind_run(tmp_path, {"run_id": "r"})
    bind_run(tmp_path, {"run_id": "r"})
    with pytest.raises(ValueError):
        bind_run(tmp_path, {"run_id": "changed"})
    record = {"question_id": "q", "run_id": "r", "status": "ok", "answer": 10, "stages": {}}
    save_record(tmp_path, record)
    assert load_records(tmp_path, "r", {"q": 10}) == [record]
    path = next((tmp_path / "predictions").glob("*.json"))
    obj = read_json(path)
    obj["record"]["answer"] = 999
    write_json(path, obj)
    with pytest.raises(ValueError):
        load_records(tmp_path, "r", {"q": 10})


def test_output_lock_is_exclusive_and_released(tmp_path):
    with output_lock(tmp_path):
        with pytest.raises(OSError):
            with output_lock(tmp_path):
                pass
    with output_lock(tmp_path):
        pass


def test_chat_transport_preserves_roles_snapshot_scope_and_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("FR_TEST_KEY", "private-test-key")
    config = {"api_key_env": "FR_TEST_KEY", "model": "gpt-4o-2024-11-20", "base_url": "https://unit.invalid/v1",
              "requests_per_minute": 100000000, "parameters": {"temperature": 1.0}, "retries": 0}
    requests = []
    def handle(request):
        body = json.loads(request.content)
        assert body["messages"][0]["role"] == "system"
        assert body["model"] == "gpt-4o-2024-11-20" and body["n"] == 1
        requests.append(body)
        return httpx.Response(200, json={"model": body["model"], "choices": [{"finish_reason": "stop", "message": {"content": "query"}}], "usage": {"total_tokens": 20}})
    async def test():
        client = ChatClient(config, tmp_path, transport=httpx.MockTransport(handle))
        prompt = messages("query", Problem("q", "Question", "Context"))
        first = await client.complete(prompt, ["run", "q", "query"])
        second = await client.complete(prompt, ["run", "q", "query"])
        third = await client.complete(prompt, ["run", "other_question", "query"])
        await client.close()
        assert not first["cached"] and second["cached"] and not third["cached"]
    asyncio.run(test())
    assert len(requests) == 2
    assert "private-test-key" not in "".join(p.read_text() for p in tmp_path.glob("*.json"))


def test_transport_does_not_accept_truncation(tmp_path, monkeypatch):
    monkeypatch.setenv("FR_TEST_KEY", "x")
    async def test():
        client = ChatClient({"api_key_env": "FR_TEST_KEY", "base_url": "https://unit.invalid/v1", "model": "gpt-4o-2024-11-20", "retries": 0},
                            tmp_path, transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"choices": [{"finish_reason": "length", "message": {"content": "partial"}}]})))
        with pytest.raises(APIError):
            await client.complete([], ["query"])
        await client.close()
    asyncio.run(test())
    assert not list(tmp_path.glob("*.json"))


def test_masked_mean_pooling_ignores_padding():
    import torch
    from fr_repro.retrieval import mean_pool
    hidden = torch.tensor([[[1., 2.], [3., 4.], [100., 100.]]])
    actual = mean_pool(hidden, torch.tensor([[1, 1, 0]]))
    assert np.allclose(actual.numpy(), [[2., 3.]])


def test_report_labels_user_requested_backbone(tmp_path):
    result = report(tmp_path, [{"question_id": "q", "answer": 1, "status": "ok", "stages": {
        "pot": {"model_returned": "gpt-5.6-sol", "usage": {}}}}], {"q": 1}, model_name="gpt-5.6-sol")
    assert result["backbone_requested"] == "gpt-5.6-sol"
    assert not result["paper_backbone_match_requested"]
    assert result["model_ids_returned"] == {"gpt-5.6-sol": 1}
    assert "Selected method with gpt-5.6-sol" in (tmp_path / "main_results.md").read_text()


def test_invalid_credentials_are_fatal(tmp_path, monkeypatch):
    monkeypatch.setenv("FR_TEST_KEY", "x")
    async def check():
        client = ChatClient({"api_key_env": "FR_TEST_KEY", "base_url": "https://unit.invalid/v1", "model": "gpt-5.6-sol", "retries": 0},
                            tmp_path, transport=httpx.MockTransport(lambda _: httpx.Response(401, json={"error": {"code": "invalid_api_key"}})))
        with pytest.raises(APIError) as caught:
            await client.complete([], ["query"])
        assert caught.value.fatal
        await client.close()
    asyncio.run(check())
