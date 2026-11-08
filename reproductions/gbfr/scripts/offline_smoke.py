"""Exercise model plumbing without an API; NOT a benchmark accuracy evaluation."""
import asyncio
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gbfr.data import write_json
from gbfr.engine import GBFR
from gbfr.graph import MetricGraph
from tests.helpers import ScriptedClient


async def main():
    graph = MetricGraph.load(ROOT / "tests" / "fixtures" / "fmkg.small.json")
    constraints = {"temporal_scope": "2024", "entity_scope": "Company A",
                   "meta": {"currency": "USD", "scale": "millions", "unit": None}}
    context = "Company A 2024. Net Sales: 100. COGS: 60. Profit Margin: 0.4. Double Profit: 80."
    client = ScriptedClient(constraints, {"Revenue": (100, "Net Sales: 100"), "Cost": (60, "COGS: 60"),
                            "Profit Margin": (.4, "Profit Margin: 0.4"), "Double Profit": (80, "Double Profit: 80")})
    answer = await GBFR(graph, client).predict("Find gross profit", context)
    absent = await GBFR(graph, ScriptedClient(constraints)).predict("Find gross profit", context)
    assert answer.value == 40 and answer.status == "answered"
    assert absent.status == "abstained" and absent.value is None
    write_json(ROOT / "research" / "offline_smoke.json", {
        "mode": "offline scripted protocol check; not an LLM benchmark", "fixture_is_paper_graph": False,
        "answerable": answer.to_dict(), "missing_evidence": absent.to_dict(),
    })
    print("Offline flow passed: three agreeing paths -> 40; absent evidence -> abstained.")
    print("No API was called. No paper accuracy result was measured.")


if __name__ == "__main__":
    asyncio.run(main())
