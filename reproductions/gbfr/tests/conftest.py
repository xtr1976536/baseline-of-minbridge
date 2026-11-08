import json
from pathlib import Path

import pytest

from gbfr.graph import MetricGraph


@pytest.fixture
def graph():
    return MetricGraph.load(Path(__file__).parent / "fixtures" / "fmkg.small.json")


@pytest.fixture
def constraints():
    return {"temporal_scope": "2024", "entity_scope": "Company A",
            "meta": {"currency": "USD", "scale": "millions", "unit": None}}
