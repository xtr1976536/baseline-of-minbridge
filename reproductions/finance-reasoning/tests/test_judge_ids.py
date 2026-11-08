import asyncio
import json

import httpx
import pytest

from fr_repro.assets import Problem
from fr_repro.client import ChatClient
from fr_repro.prompts import ID_JUDGE, PROMPTS, candidate_ids, judge_response_format, messages, select_functions
from fr_repro.runner import solve


def test_id_encoding_preserves_source_criteria_problem_and_function_text():
    functions = [f'def function_{i}(x):\n    """Exact description {i}."""\n    return x' for i in range(30)]
    problem = Problem("synthetic", "Synthetic question only", "Synthetic context only")
    legacy = messages("judge", problem, functions)
    new = messages("judge", problem, functions, judge_protocol=ID_JUDGE)
    assert new[0]["content"] == legacy[0]["content"].replace("respond with [USEFUL]", "mark it as useful for selection").replace("respond with [USELESS]", "exclude it from selection")
    for identifier, code in zip(candidate_ids(30), functions):
        assert f'<candidate id="{identifier}">\n{code}\n</candidate>' in new[1]["content"]
    assert "Synthetic context only" in new[1]["content"] and "Synthetic question only" in new[1]["content"]
    assert "ground_truth" not in str(new) and "python_solution" not in str(new)
    for stage in ["query", "pot"]:
        assert messages(stage, problem, functions, judge_protocol=ID_JUDGE) == messages(stage, problem, functions)


@pytest.mark.parametrize("raw,expected", [
    ('{"selected_ids":[]}', []),
    ('{"selected_ids":["C01"]}', [0]),
    ('{"selected_ids":["C30","C02","C11"]}', [1, 10, 29]),
    ('```json\n{"selected_ids":["C02"]}\n```', [1]),
])
def test_sparse_id_selection_is_unambiguous_and_keeps_the_selected_set(raw, expected):
    assert select_functions(raw, list(range(30)), judge_protocol=ID_JUDGE) == expected


@pytest.mark.parametrize("raw", [
    '{"selected_ids":["C01","C01"]}',
    '{"selected_ids":["C00"]}',
    '{"selected_ids":["C31"]}',
    '{"selected_ids":["C1"]}',
    '{"selected_ids":[1]}',
    '{"selected_ids":[true]}',
    '{"selected_ids":["C01","C02","C03","C04"]}',
    '{"selected_ids":null}',
    '{"selected_ids":[] ,"reason":"extra"}',
    '{"selected_ids":[],"selected_ids":["C01"]}',
    '["C01"]',
    'Here is JSON: {"selected_ids":["C01"]}',
    '[USEFUL, USELESS]',
])
def test_invalid_id_output_is_rejected_without_guessing_or_truncation(raw):
    with pytest.raises(ValueError):
        select_functions(raw, list(range(30)), judge_protocol=ID_JUDGE)


def test_structured_format_applies_only_to_the_judge_and_is_part_of_cache_identity(tmp_path, monkeypatch):
    monkeypatch.setenv("FR_TEST_KEY", "synthetic-secret")
    requests = []
    def handle(request):
        body = json.loads(request.content)
        requests.append(body)
        return httpx.Response(200, json={"model": body["model"], "choices": [{"finish_reason": "stop", "message": {"content": '{"selected_ids":["C01"]}'}}]})
    async def check():
        client = ChatClient({"api_key_env": "FR_TEST_KEY", "base_url": "https://unit.invalid/v1", "model": "gpt-5.6-sol", "requests_per_minute": 100000000},
                            tmp_path, transport=httpx.MockTransport(handle))
        request = messages("query", Problem("synthetic", "Synthetic question", ""))
        await client.complete(request, ["run", "q", "query"])
        await client.complete(request, ["run", "q", "query"], response_format=judge_response_format(30))
        await client.complete(request, ["run", "q", "query"], response_format=judge_response_format(30))
        await client.close()
    asyncio.run(check())
    assert len(requests) == 2
    assert "response_format" not in requests[0]
    schema = requests[1]["response_format"]["json_schema"]
    assert schema["strict"] is True
    assert schema["schema"]["properties"]["selected_ids"]["maxItems"] == 3
    assert schema["schema"]["properties"]["selected_ids"]["items"]["enum"] == candidate_ids(30)


def test_one_id_judge_call_selects_only_referenced_functions():
    class Retriever:
        def search(self, query, k):
            return [{"function_id": f"f{i}", "function": f"def fn{i}(x): return x", "score": 30-i} for i in range(30)]
    class Client:
        def __init__(self):
            self.calls = []
        async def complete(self, request, scope, **kwargs):
            self.calls.append((request, scope, kwargs))
            text = {"query": "synthetic search", "judge": '{"selected_ids":["C01","C03"]}', "pot": "def solution():\n    return 7"}[scope[-1]]
            return {"content": text, "usage": {}, "cached": False}
    client = Client()
    result = asyncio.run(solve(Problem("synthetic", "Synthetic question", ""), Retriever(), client,
                              run_id="synthetic_run", timeout=10, judge_protocol=ID_JUDGE))
    assert result["status"] == "ok" and result["answer"] == 7
    assert result["selected_ids"] == ["f0", "f2"]
    assert result["candidates"][29]["reference_id"] == "C30"
    assert [scope[-1] for _, scope, _ in client.calls] == ["query", "judge", "pot"]
    assert not client.calls[0][2] and not client.calls[2][2]
    assert client.calls[1][2]["response_format"] == judge_response_format(30)
    assert "def fn2" in client.calls[2][0][1]["content"] and "def fn1" not in client.calls[2][0][1]["content"]
