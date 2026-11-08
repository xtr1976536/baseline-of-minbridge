"""Real local retrieval plus all-question scheduling; no paid LLM calls.

Scripted completions are protocol fixtures and never performance estimates.
"""
import asyncio
from contextlib import redirect_stdout
import copy
import io
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fr_repro.common import load_config, read_json, write_json
from fr_repro.runner import preflight, run
from fr_repro.retrieval import FunctionRetriever

root = Path(__file__).resolve().parents[1]
config = load_config(root / "configs/main.json")
problems, labels, functions = preflight(config)
retriever = FunctionRetriever(config["data_dir"], functions, config["retriever"])
queries = ["Calculate a year-end employee bonus from annual salary and bonus percentage",
           "Calculate the net present value of a series of cash flows discounted at a fixed rate"]
batch_vectors = retriever.encoder.encode(queries)
single_vectors = np.vstack([retriever.encoder.encode([q])[0] for q in queries])
assert np.allclose(batch_vectors, single_vectors, rtol=1e-5, atol=1e-5), "Pooling depends on other questions' padding"
neighbors = [retriever.search(q, 30) for q in queries]
assert all(len(n) == len({f['function_id'] for f in n}) == 30 for n in neighbors)
assert [f['function_id'] for f in neighbors[0]] != [f['function_id'] for f in neighbors[1]]


class FrozenRetriever:
    def search(self, query, k):
        assert k == 30
        return neighbors[0]


class ScriptedClient:
    def __init__(self):
        self.calls = 0

    async def complete(self, request, scope):
        self.calls += 1
        stage = scope[-1]
        text = {"query": queries[0], "judge": "[" + ", ".join(["USEFUL"]*30) + "]",
                "pot": "def solution():\n    return 0"}[stage]
        return {"content": text, "usage": {}, "cached": False, "model_returned": "SCRIPTED_NO_LLM"}


async def validate():
    import tempfile
    trial = copy.deepcopy(config)
    trial["execution_mode"] = "scripted"
    (root / "tmp").mkdir(exist_ok=True)
    trial["output_dir"] = tempfile.mkdtemp(prefix="offline-main-", dir=root / "tmp")
    trial["cache_dir"] = str(root / "tmp/offline-api-cache-unused")
    fake = ScriptedClient()
    with redirect_stdout(io.StringIO()):
        first = await run(trial, client=fake, retriever=FrozenRetriever())
        count = fake.calls
        second = await run(trial, client=fake, retriever=FrozenRetriever())
    assert first["recorded"] == 238 and first["complete"] and second == first
    assert first["accuracy"] is None and not first["is_performance_result"]
    assert count == fake.calls == 238*3
    return {"covered_questions": 238, "scripted_stage_calls": count, "resume_new_stage_calls": fake.calls-count,
            "status": "offline scheduling verification only; not LLM accuracy", "output_dir": trial["output_dir"]}


result = {"real_paid_api_calls": 0, "retriever": "real pinned Contriever, full 3133-function index",
          "batch_padding_invariance": "passed within 1e-5 float32 tolerance",
          "real_retrieval_examples": [{"query": query, "top5": [{"function_id": f["function_id"], "title": f.get("article_title"), "score": f["score"]} for f in found[:5]]}
                                      for query, found in zip(queries, neighbors)],
          "full_split_protocol": asyncio.run(validate())}
write_json(root / "research/offline_validation.json", result)
print("Real Contriever retrieval and all 238 questions' scripted saving/resume verified; no real LLM accuracy reported.")
