from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class RoleSpec:
    name: str
    aliases: list[str] = field(default_factory=list)
    period: str = ""
    # Authoritative XBRL concept qname (e.g. "us-gaap:RepaymentsOfLongTermDebt") when the
    # role is derived from a known calc-linkbase child — binds directly, skipping fuzzy
    # name→concept resolution that collapses distinct debt/flow roles onto one concept.
    concept: str = ""


@dataclass
class ClaimSpec:
    metric: str
    formula: str
    roles: list[RoleSpec]
    claim_unit: str
    tolerance: float
    formula_source: str  # "policy_registry" | "generic_operation" | "no_formula"
    period: str = ""
    operation: Optional[str] = None
    # LLM-parsed claim from the answer string (replaces regex _parse_number)
    claimed_value: Optional[float] = None
    claimed_unit: str = ""


@dataclass
class ClaimedAnswer:
    value: Optional[float]
    unit: str = ""


@dataclass
class GroundedFact:
    name: str
    value: float
    unit: str
    source_quote: str
    period: str = ""
    row_label: str = ""
    fact_type: str = "numeric"
    concept: str = ""  # authoritative XBRL concept qname carried from the RoleSpec


@dataclass
class AgentResult:
    question: str
    answer: str
    status: str  # VERIFIED | VIOLATED | ABSTAIN | UNVERIFIED_FORMULA
    metric: str = ""
    formula: str = ""
    formula_source: str = ""
    facts: dict[str, GroundedFact] = field(default_factory=dict)
    claimed_value: Optional[float] = None
    smtlib: str = ""
    solver_status: str = ""
    failure_reason: str = ""
    diagnostics: dict[str, Any] = field(default_factory=dict)
