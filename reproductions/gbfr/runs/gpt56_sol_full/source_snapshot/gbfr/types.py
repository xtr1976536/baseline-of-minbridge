from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
import json
import math


class ProtocolError(ValueError):
    """Malformed operator structure or executable protocol; not an abstention."""


class EvidenceError(ProtocolError):
    """A well-formed binding fails an explicit evidence/constraint check."""


class AssetError(ValueError):
    pass


def finite(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProtocolError(f"Expected a numeric scalar, got {type(value).__name__}")
    result = float(value)
    if not math.isfinite(result):
        raise ProtocolError("Non-finite number")
    return result


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


@dataclass(frozen=True)
class Constraints:
    temporal_scope: Any = None
    entity_scope: Any = None
    meta: dict[str, Any] = field(default_factory=lambda: {
        "currency": None, "scale": None, "unit": None,
    })

    @classmethod
    def parse(cls, obj: dict) -> Constraints:
        if not isinstance(obj, dict) or not {
            "temporal_scope", "entity_scope", "meta"
        } <= obj.keys():
            raise ProtocolError("Constraints require temporal_scope, entity_scope and meta")
        if not isinstance(obj["meta"], dict) or not {"currency", "scale", "unit"} <= obj["meta"].keys():
            raise ProtocolError("meta requires currency, scale and unit")
        return cls(obj["temporal_scope"], obj["entity_scope"], obj["meta"])

    def key(self) -> str:
        return dumps(asdict(self))


@dataclass(frozen=True)
class Goal:
    metric: str
    constraints: Constraints

    @classmethod
    def parse(cls, obj: dict) -> Goal:
        if not isinstance(obj.get("metric"), str) or not obj["metric"].strip():
            raise ProtocolError("Missing metric")
        return cls(obj["metric"], Constraints.parse(obj["constraints"]))


@dataclass
class Plan:
    reasoning_type: str
    operator: str
    subgoals: list[Goal]
    precision: str | None

    @classmethod
    def parse(cls, obj: dict) -> Plan:
        if set(obj) != {"reasoning_type", "operator", "subgoals", "precision"}:
            raise ProtocolError("OQA must return exactly the four Appendix F keys")
        if obj["reasoning_type"] not in {
            "DirectRetrieval", "ArithmeticCalculation", "ComparativeReasoning",
            "StatisticalAggregation", "TemporalReasoning",
        }:
            raise ProtocolError("Unsupported reasoning type")
        if obj["operator"] not in {
            "sum", "difference", "product", "division", "ratio", "change ratio",
            "range", "compare", "average", "time", "counting",
        }:
            raise ProtocolError("Unsupported aggregation operator")
        goals = [Goal.parse(x) for x in obj["subgoals"]]
        if not goals:
            raise ProtocolError("OQA returned no subgoals")
        if obj["precision"] is not None and not isinstance(obj["precision"], str):
            raise ProtocolError("precision must be a string or null")
        return cls(obj["reasoning_type"], obj["operator"], goals, obj["precision"])


@dataclass
class Resolution:
    value: float | None
    meta: dict = field(default_factory=dict)
    paths: list[dict] = field(default_factory=list)
    reason: str = ""


@dataclass
class Prediction:
    status: str  # answered | abstained; exceptions become error in the runner
    value: float | None
    meta: dict
    precision: str | None
    trace: dict
    reason: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
