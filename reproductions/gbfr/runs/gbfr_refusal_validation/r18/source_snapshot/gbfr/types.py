from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
import json
import math
import re


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
        from .units import normalize_meta
        try:
            meta=normalize_meta(obj['meta'])
            # A dollar sign alone does not establish an ISO currency. OES
            # must see the source symbol instead of an invented USD constraint.
            if obj['meta'].get('currency')=='$':meta['currency']='$'
        except ValueError as exc:raise ProtocolError(str(exc)) from exc
        return cls(obj["temporal_scope"], obj["entity_scope"],meta)

    def key(self) -> str:
        return dumps(asdict(self))


@dataclass(frozen=True)
class Goal:
    metric: str
    constraints: Constraints

    @classmethod
    def parse(cls, obj: dict) -> Goal:
        # The paper writes subgoals as (metric, C). JSON pairs and named
        # objects express the identical goal; neither changes its content.
        if isinstance(obj,(list,tuple)) and len(obj)==2:obj={'metric':obj[0],'constraints':obj[1]}
        if not isinstance(obj,dict):raise ProtocolError('A subgoal must be a metric/constraints object or pair')
        if not isinstance(obj.get("metric"), str) or not obj["metric"].strip():
            raise ProtocolError("Missing metric")
        if obj['metric'].strip().casefold() in {'unknown','null','none','n/a','unspecified'}:
            raise ProtocolError('OQA supplied a placeholder instead of a requested metric')
        metric=obj['metric'];constraints=obj['constraints']
        if isinstance(constraints,dict):
            # Some responses put a financial qualifier beside the three C
            # fields. Retain its content in the metric instead of silently
            # dropping it (e.g. total dividends paid IN CASH).
            qualifier=constraints.get('metric_qualifier')
            if qualifier is not None:
                if not isinstance(qualifier,str):raise ProtocolError('metric_qualifier must be text')
                if qualifier.strip() and qualifier.casefold() not in metric.casefold():metric+=' '+qualifier.strip()
        return cls(metric, Constraints.parse(constraints))


@dataclass
class Plan:
    reasoning_type: str
    operator: str
    subgoals: list[Goal]
    precision: str | None

    @classmethod
    def parse(cls, obj: dict) -> Plan:
        if not isinstance(obj,dict):raise ProtocolError('OQA must return an object')
        if set(obj) != {"reasoning_type", "operator", "subgoals", "precision"}:
            raise ProtocolError("OQA must return exactly the four Appendix F keys")
        reasoning={re.sub(r'[^a-z]','',s.casefold()):s for s in {
            "DirectRetrieval", "ArithmeticCalculation", "ComparativeReasoning",
            "StatisticalAggregation", "TemporalReasoning",
        }}
        kind=reasoning.get(re.sub(r'[^a-z]','',str(obj['reasoning_type']).casefold()))
        if kind is None:
            raise ProtocolError("Unsupported reasoning type")
        operator=' '.join(str(obj['operator']).casefold().replace('_',' ').replace('-',' ').split())
        operator={'subtract':'difference','divide':'division','multiply':'product','mean':'average',
                  'percentage change':'change ratio','percentagechange':'change ratio','change rate':'change ratio'}.get(operator,operator)
        if operator not in {
            "sum", "difference", "product", "division", "ratio", "change ratio",
            "range", "compare", "average", "time", "counting",
        }:
            raise ProtocolError("Unsupported aggregation operator")
        if not isinstance(obj['subgoals'],list):raise ProtocolError('subgoals must be an array')
        goals = [Goal.parse(x) for x in obj["subgoals"]]
        if not goals:
            raise ProtocolError("OQA returned no subgoals")
        expanded=[]
        aggregating=operator in {'sum','average','difference','division','ratio','change ratio','range','compare','counting'}
        for goal in goals:
            scope=goal.constraints.temporal_scope
            periods=scope if isinstance(scope,list) else None
            if isinstance(scope,str) and ';' in scope:
                parts=[p.strip() for p in scope.split(';') if p.strip()]
                # A conjunction such as "as of 2024; due within one year"
                # describes one constraint, not two independent operands.
                if len(parts)>1 and all(re.fullmatch(r'(?:FY\s*|(?:fiscal\s+)?year\s+)?(?:19|20)\d{2}',p,re.I) for p in parts):periods=parts
            if isinstance(scope,str) and re.fullmatch(r'\s*(?:19|20)\d{2}(?:\s*,\s*(?:and\s+)?(?:19|20)\d{2})+\s*',scope):
                periods=re.findall(r'(?:19|20)\d{2}',scope)
            if aggregating and periods and all(isinstance(p,str) and p.strip() for p in periods):
                for period in periods:expanded.append(Goal(goal.metric,Constraints(period,goal.constraints.entity_scope,dict(goal.constraints.meta))))
            else:expanded.append(goal)
        goals=expanded
        precision=obj['precision']
        if type(precision) is int and 0<=precision<=12:precision=f'{precision} decimal places'
        if precision is not None and not isinstance(precision, str):
            raise ProtocolError("precision must be a string or null")
        return cls(kind,operator,goals,precision)


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
