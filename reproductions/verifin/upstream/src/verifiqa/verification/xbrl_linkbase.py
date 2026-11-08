from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree
from verifiqa.formulas.evaluator import format_number
from verifiqa.policy.registry import DEFAULT_POLICY_REGISTRY
from verifiqa.types import VerificationFact, VerificationIR


def _require_sec_user_agent() -> str:
    user_agent = os.environ.get("SEC_USER_AGENT", "").strip()
    if not user_agent:
        raise RuntimeError(
            "SEC_USER_AGENT is required for SEC EDGAR requests; set it to a "
            "descriptive value that includes contact information."
        )
    return user_agent



def _format_decimal(value: Decimal) -> str:
    """Emit an exact SMT-LIB numeric literal from a Decimal without float round-trip."""
    if value == value.to_integral_value():
        return str(int(value))
    return format(value.normalize(), "f")


def _binding_rhs(xbrl_var: str, multiplier: Any) -> str:
    try:
        value = float(multiplier)
    except (TypeError, ValueError):
        value = 1.0
    if value == 1.0:
        return xbrl_var
    if value == -1.0:
        return f"(* -1 {xbrl_var})"
    return f"(* {format_number(value)} {xbrl_var})"


XBRLI = "http://www.xbrl.org/2003/instance"
XBRLDI = "http://xbrl.org/2006/xbrldi"
LINK = "http://www.xbrl.org/2003/linkbase"
XLINK = "http://www.w3.org/1999/xlink"


@dataclass(frozen=True)
class XbrlContext:
    context_id: str
    instant: str = ""
    start_date: str = ""
    end_date: str = ""
    dimensions: tuple[str, ...] = ()


@dataclass(frozen=True)
class XbrlFact:
    concept: str
    local_name: str
    context_id: str
    unit_ref: str
    decimals: str = ""
    precision: str = ""
    value: Decimal | None = None


@dataclass(frozen=True)
class CalcChild:
    concept: str
    local_name: str
    weight: Decimal


@dataclass(frozen=True)
class CalcGroup:
    role: str
    parent_concept: str
    parent_local: str
    children: tuple[CalcChild, ...]
    source_path: str


@dataclass
class FilingXbrl:
    doc_name: str
    status: str
    cik: str = ""
    edgar_dir: Path | None = None
    instance_path: Path | None = None
    calculation_path: Path | None = None
    contexts: dict[str, XbrlContext] = field(default_factory=dict)
    units: dict[str, tuple[str, ...]] = field(default_factory=dict)
    facts_by_local_context: dict[tuple[str, str], XbrlFact] = field(default_factory=dict)
    calc_groups: list[CalcGroup] = field(default_factory=list)
    concept_labels: dict[str, list[str]] = field(default_factory=dict)
    diagnostics: list[str] = field(default_factory=list)


def attach_xbrl_calculations(
    ir: VerificationIR,
    doc_name: str,
    artifacts_dir: Path | None,
    *,
    ignore_unit_matching: bool = False,
) -> VerificationIR:
    """Attach parsed filing-specific calculation-linkbase metadata to an IR."""

    if artifacts_dir is None or not doc_name:
        return ir
    bundle = load_filing_xbrl(doc_name, artifacts_dir)
    if bundle.status != "ok":
        # No usable local calculation linkbase — but if the company is in the EDGAR
        # companyfacts cache we can still bind facts to authoritative filing values
        # (no calc constraints, like the table path). This rescues the cohort that
        # has no/incomplete local XBRL, which is exactly where the LLM goes unchecked.
        edgar_bindings = (
            _bind_ir_facts(ir, bundle, ignore_unit_matching=ignore_unit_matching)
            if (bundle.cik and bundle.edgar_dir is not None)
            else []
        )
        _apply_authoritative_bindings(ir, edgar_bindings)
        if edgar_bindings:
            ir.evidence_facts = {}
            ir.xbrl_calculations = {
                "enabled": True,
                "status": "ok",
                "grounding_status": _grounding_status("ok", edgar_bindings, []),
                "doc_name": doc_name,
                "bindings": edgar_bindings,
                "constraints": [],
                "declared_variables": sorted({b["xbrl_variable"] for b in edgar_bindings}),
                "dropped_constraints": [],
                "instantiated_constraints": 0,
                "connected_constraints": 0,
                "evidence_fact_variables": [],
                "binding_sources": sorted({str(b.get("source") or "") for b in edgar_bindings if b.get("source")}),
                "diagnostics": bundle.diagnostics + [f"edgar_only_binding:no_local_calc:{bundle.status}"],
            }
            return ir
        ir.evidence_facts = {}
        ir.xbrl_calculations = {
            "enabled": True,
            "status": bundle.status,
            "grounding_status": _grounding_status(bundle.status, [], []),
            "doc_name": doc_name,
            "diagnostics": bundle.diagnostics,
            "bindings": [],
            "constraints": [],
            "declared_variables": [],
            "dropped_constraints": [],
            "instantiated_constraints": 0,
            "connected_constraints": 0,
            "evidence_fact_variables": [],
        }
        return ir

    bindings = _bind_ir_facts(ir, bundle, ignore_unit_matching=ignore_unit_matching)
    _apply_authoritative_bindings(ir, bindings)
    instantiated_constraints = _instantiate_constraints(bundle)
    bound_xbrl_variables = {binding["xbrl_variable"] for binding in bindings}

    connected_constraints, disconnected_drops = _constraints_connected_to_bindings(
        instantiated_constraints,
        bound_xbrl_variables,
    )
    evidence_facts = _evidence_facts_from_constraints(
        connected_constraints,
        bundle,
        exclude_variables=bound_xbrl_variables,
    )
    asserted_xbrl_variables = bound_xbrl_variables | set(evidence_facts)
    constraints, missing_drops = _prune_constraints(connected_constraints, asserted_xbrl_variables)
    dropped_constraints = disconnected_drops + missing_drops

    surviving_variables = set().union(*(_constraint_variables(constraint) for constraint in constraints)) if constraints else set()
    evidence_facts = {
        name: fact
        for name, fact in evidence_facts.items()
        if name in surviving_variables and name not in bound_xbrl_variables
    }
    asserted_xbrl_variables = bound_xbrl_variables | set(evidence_facts)
    constraints, late_missing_drops = _prune_constraints(constraints, asserted_xbrl_variables)
    dropped_constraints.extend(late_missing_drops)

    declared = sorted(
        bound_xbrl_variables
        | {
            constraint["parent_variable"]
            for constraint in constraints
        }
        | {
            child["variable"]
            for constraint in constraints
            for child in constraint["children"]
        }
    )
    status = "ok" if constraints else "no_surviving_calculation_constraints"
    if not instantiated_constraints:
        status = "no_instantiated_calculation_constraints"
    elif not bindings:
        status = "no_safe_fact_bindings"
    elif not connected_constraints:
        status = "no_constraints_connected_to_formula_facts"
    ir.evidence_facts = evidence_facts
    ir.xbrl_calculations = {
        "enabled": True,
        "status": status,
        "grounding_status": _grounding_status(status, bindings, constraints),
        "doc_name": doc_name,
        "instance_path": str(bundle.instance_path or ""),
        "calculation_path": str(bundle.calculation_path or ""),
        "bindings": bindings,
        "constraints": constraints,
        "declared_variables": declared,
        "dropped_constraints": dropped_constraints,
        "instantiated_constraints": len(instantiated_constraints),
        "connected_constraints": len(connected_constraints),
        "evidence_fact_variables": sorted(evidence_facts),
        "binding_sources": sorted({str(binding.get("source") or "") for binding in bindings if binding.get("source")}),
        "canonical_bridge": {
            "enabled": True,
            "key": "concept+period+unit+dimensions",
        },
        "diagnostics": bundle.diagnostics,
    }
    return ir

_SOURCE_LABELS = {
    "source_document": "source-document",
    "finqa_table": "source-table",
    "edgar_companyfacts_fy": "EDGAR-companyfacts",
}


def _binding_source_label(xbrl: dict[str, Any], bindings: list[dict[str, Any]]) -> str:
    """Human label for the binding source, so injected SMT comments read accurately."""
    sources = {str(b.get("source") or "") for b in bindings}
    sources.discard("")
    if not sources:
        sources = {str(xbrl.get("source") or "")}
        sources.discard("")
    if len(sources) == 1:
        return _SOURCE_LABELS.get(next(iter(sources)), "XBRL")
    return "XBRL"


def augment_smt_with_xbrl(smtlib: str, ir: VerificationIR) -> str:
    """Append deterministic XBRL binding, evidence, and calculation assertions."""

    xbrl = ir.xbrl_calculations or {}
    bindings = list(xbrl.get("bindings") or [])
    constraints = list(xbrl.get("constraints") or [])
    evidence_facts = dict(getattr(ir, "evidence_facts", {}) or {})
    if not bindings and not constraints and not evidence_facts:
        return smtlib

    declared = set(_declared_variables(smtlib))
    named = set(re.findall(r":named\s+([A-Za-z_][A-Za-z0-9_]*)", smtlib))
    source_label = _binding_source_label(xbrl, bindings)
    header = (
        f"; {source_label} calculation-linkbase constraints parsed from the filing."
        if constraints
        else f"; {source_label} fact bindings (no calculation-linkbase constraints)."
    )
    additions: list[str] = ["", header]
    for variable in xbrl.get("declared_variables") or []:
        if variable not in declared:
            additions.append(f"(declare-const {variable} Real)")
            declared.add(variable)

    if evidence_facts:
        additions.append("")
        additions.append("; Redundant XBRL instance facts used only by calculation-linkbase constraints.")
    for variable, fact in sorted(evidence_facts.items()):
        assertion_name = f"evidence_{variable}"
        if assertion_name in named:
            continue
        raw = fact.value
        smt_val = _format_decimal(raw) if isinstance(raw, Decimal) else format_number(raw)
        additions.append(
            f"(assert (! (= {variable} {smt_val}) :named {assertion_name}))"
        )
        named.add(assertion_name)

    if bindings:
        additions.append("")
        additions.append(f"; IR-to-{source_label} bindings and independent instance-value witnesses.")
    for binding in bindings:
        fact_name = binding["fact_name"]
        xbrl_var = binding["xbrl_variable"]
        bind_name = _assertion_name(f"xbrl_bind_{fact_name}_{binding['context_id']}")
        if bind_name not in named:
            rhs = _binding_rhs(xbrl_var, binding.get("binding_multiplier", 1.0))
            tolerance = float(binding.get("binding_tolerance") or 0.0)
            if tolerance > 0.0:
                tol = format_number(tolerance)
                additions.append(f"(assert (! (<= (- {fact_name} {rhs}) {tol}) :named {bind_name}_upper))")
                additions.append(f"(assert (! (<= (- {rhs} {fact_name}) {tol}) :named {bind_name}_lower))")
                named.add(f"{bind_name}_upper")
                named.add(f"{bind_name}_lower")
            else:
                additions.append(f"(assert (! (= {fact_name} {rhs}) :named {bind_name}))")
                named.add(bind_name)
        xbrl_value = binding.get("xbrl_value")
        if xbrl_value is not None:
            inst_name = _assertion_name(f"xbrl_instance_{fact_name}")
            if inst_name not in named:
                smt_val = binding.get("xbrl_smt_value") or format_number(xbrl_value)
                additions.append(
                    f"(assert (! (= {xbrl_var} {smt_val}) :named {inst_name}))"
                )
                named.add(inst_name)

    if constraints:
        additions.append("")
        additions.append("; R constraints from filing calculationArc summation-item relationships.")
    for constraint in constraints:
        parent = constraint["parent_variable"]
        rhs = _weighted_sum((child["variable"], Decimal(str(child["weight"]))) for child in constraint["children"])
        tolerance = format_number(float(constraint["tolerance"]))
        diff = f"(- {parent} {rhs})"
        upper_name = _assertion_name(f"{constraint['name']}_upper")
        lower_name = _assertion_name(f"{constraint['name']}_lower")
        additions.append(f"(assert (! (<= {diff} {tolerance}) :named {upper_name}))")
        additions.append(f"(assert (! (>= {diff} (- {tolerance})) :named {lower_name}))")

    return _insert_before_check_sat(smtlib, "\n".join(additions))

def load_filing_xbrl(doc_name: str, artifacts_dir: Path) -> FilingXbrl:
    entry = _manifest_entry(doc_name, artifacts_dir)
    if entry is None:
        return FilingXbrl(doc_name=doc_name, status="missing_manifest_entry")
    # Resolve CIK / EDGAR companyfacts dir from the manifest up front, so the EDGAR
    # fallback can still bind facts when the local XBRL instance or calculation
    # linkbase is missing — those are exactly the cases that most need it.
    cik = str(entry.get("cik") or (entry.get("xbrl") or {}).get("cik") or "").lstrip("0") or ""
    edgar_dir = artifacts_dir.parent / "edgar_companyfacts" if cik else None
    if not entry.get("calculation_linkbases"):
        return FilingXbrl(
            doc_name=doc_name,
            status=str(entry.get("status") or "missing_calculation_linkbase"),
            cik=cik,
            edgar_dir=edgar_dir,
        )
    instance_path = _first_saved_path(entry, "instances")
    calculation_path = _first_saved_path(entry, "calculation_linkbases")
    if instance_path is None:
        return FilingXbrl(doc_name=doc_name, status="missing_xbrl_instance", cik=cik, edgar_dir=edgar_dir)
    if calculation_path is None:
        return FilingXbrl(doc_name=doc_name, status="missing_calculation_linkbase", cik=cik, edgar_dir=edgar_dir)

    contexts, units, facts, fact_diagnostics = _parse_instance(instance_path)
    groups, group_diagnostics = _parse_calculation_linkbase(calculation_path)
    label_path = _first_saved_path(entry, "label_linkbases") or _first_saved_path(entry, "other_linkbases_lab")
    # Also search the doc directory for any _lab.xml file
    if label_path is None and instance_path is not None:
        for candidate in instance_path.parent.glob("*_lab.xml"):
            label_path = candidate
            break
    concept_labels = _parse_label_linkbase(label_path) if label_path else {}
    return FilingXbrl(
        doc_name=doc_name,
        status="ok",
        cik=cik,
        edgar_dir=edgar_dir,
        instance_path=instance_path,
        calculation_path=calculation_path,
        contexts=contexts,
        units=units,
        facts_by_local_context=facts,
        calc_groups=groups,
        concept_labels=concept_labels,
        diagnostics=fact_diagnostics + group_diagnostics,
    )


def _manifest_entry(doc_name: str, artifacts_dir: Path) -> dict[str, Any] | None:
    manifest_path = artifacts_dir / "manifest.json"
    if not manifest_path.exists():
        return None
    with manifest_path.open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    docs = manifest.get("docs") or {}
    if isinstance(docs, dict):
        entry = docs.get(doc_name)
        if isinstance(entry, dict):
            return entry
    for entry in manifest.get("results") or []:
        if isinstance(entry, dict) and entry.get("doc_name") == doc_name:
            return entry
    return None


def _first_saved_path(entry: dict[str, Any], key: str) -> Path | None:
    for item in entry.get(key) or []:
        if item.get("status") == "saved" and item.get("path"):
            path = Path(str(item["path"]))
            if path.exists():
                return path
    return None


def _parse_instance(path: Path) -> tuple[dict[str, XbrlContext], dict[str, tuple[str, ...]], dict[tuple[str, str], XbrlFact], list[str]]:
    diagnostics: list[str] = []
    nsmap = _namespace_map(path)
    root = ElementTree.parse(path).getroot()
    contexts = _parse_contexts(root)
    units = _parse_units(root)
    facts: dict[tuple[str, str], XbrlFact] = {}
    duplicates = 0
    for element in root:
        context_id = element.attrib.get("contextRef")
        if not context_id:
            continue
        namespace, local = _split_tag(element.tag)
        if not local:
            continue
        value = _decimal_text(element.text)
        concept = _qname(nsmap, namespace, local)
        fact = XbrlFact(
            concept=concept,
            local_name=local,
            context_id=context_id,
            unit_ref=element.attrib.get("unitRef", ""),
            decimals=element.attrib.get("decimals", ""),
            precision=element.attrib.get("precision", ""),
            value=value,
        )
        key = (concept, context_id)
        if key in facts:
            duplicates += 1
            continue
        facts[key] = fact
    if duplicates:
        diagnostics.append(f"duplicate_concept_context_facts_deduplicated:{duplicates}")
    return contexts, units, facts, diagnostics


def _parse_contexts(root: ElementTree.Element) -> dict[str, XbrlContext]:
    contexts: dict[str, XbrlContext] = {}
    for element in root.findall(f"{{{XBRLI}}}context"):
        context_id = element.attrib.get("id", "")
        if not context_id:
            continue
        period = element.find(f"{{{XBRLI}}}period")
        instant = _child_text(period, f"{{{XBRLI}}}instant")
        start = _child_text(period, f"{{{XBRLI}}}startDate")
        end = _child_text(period, f"{{{XBRLI}}}endDate")
        dimensions = []
        for member in element.iter(f"{{{XBRLDI}}}explicitMember"):
            dimension = member.attrib.get("dimension", "")
            member_text = (member.text or "").strip()
            dimensions.append(f"{dimension}={member_text}")
        contexts[context_id] = XbrlContext(
            context_id=context_id,
            instant=instant,
            start_date=start,
            end_date=end,
            dimensions=tuple(sorted(dimensions)),
        )
    return contexts


def _parse_units(root: ElementTree.Element) -> dict[str, tuple[str, ...]]:
    units: dict[str, tuple[str, ...]] = {}
    for unit in root.findall(f"{{{XBRLI}}}unit"):
        unit_id = unit.attrib.get("id", "")
        measures = tuple(
            (measure.text or "").strip()
            for measure in unit.iter(f"{{{XBRLI}}}measure")
            if (measure.text or "").strip()
        )
        if unit_id:
            units[unit_id] = measures
    return units


def _parse_calculation_linkbase(path: Path) -> tuple[list[CalcGroup], list[str]]:
    diagnostics: list[str] = []
    root = ElementTree.parse(path).getroot()
    groups: list[CalcGroup] = []
    for link in root.findall(f".//{{{LINK}}}calculationLink"):
        role = link.attrib.get(f"{{{XLINK}}}role", "")
        locs: dict[str, str] = {}
        for loc in link.findall(f"{{{LINK}}}loc"):
            label = loc.attrib.get(f"{{{XLINK}}}label", "")
            href = loc.attrib.get(f"{{{XLINK}}}href", "")
            concept = _concept_from_href(href)
            if label and concept:
                locs[label] = concept
        children_by_parent: dict[str, list[CalcChild]] = {}
        for arc in link.findall(f"{{{LINK}}}calculationArc"):
            parent_label = arc.attrib.get(f"{{{XLINK}}}from", "")
            child_label = arc.attrib.get(f"{{{XLINK}}}to", "")
            parent = locs.get(parent_label)
            child = locs.get(child_label)
            if not parent or not child:
                continue
            weight = _decimal_text(arc.attrib.get("weight", "1")) or Decimal("1")
            children_by_parent.setdefault(parent, []).append(
                CalcChild(concept=child, local_name=_local_from_qname(child), weight=weight)
            )
        for parent, children in children_by_parent.items():
            if children:
                groups.append(
                    CalcGroup(
                        role=role,
                        parent_concept=parent,
                        parent_local=_local_from_qname(parent),
                        children=tuple(children),
                        source_path=str(path),
                    )
                )
    if not groups:
        diagnostics.append("calculation_linkbase_had_no_groups")
    return groups, diagnostics

def _parse_label_linkbase(path: Path) -> dict[str, list[str]]:
    """Parse a label linkbase and return {concept_qname: [label, ...]}."""
    root = ElementTree.parse(path).getroot()
    concept_labels: dict[str, list[str]] = {}
    for link in root.findall(f".//{{{LINK}}}labelLink"):
        locs: dict[str, str] = {}
        for loc in link.findall(f"{{{LINK}}}loc"):
            label_key = loc.attrib.get(f"{{{XLINK}}}label", "")
            href = loc.attrib.get(f"{{{XLINK}}}href", "")
            concept = _concept_from_href(href)
            if label_key and concept:
                locs[label_key] = concept
        labels: dict[str, str] = {}
        for label_el in link.findall(f"{{{LINK}}}label"):
            label_key = label_el.attrib.get(f"{{{XLINK}}}label", "")
            role = label_el.attrib.get(f"{{{XLINK}}}role", "")
            text = (label_el.text or "").strip()
            # Prefer standard label; skip terse/documentation/period-start/end labels
            if text and "terse" not in role and "documentation" not in role:
                labels[label_key] = text
        for arc in link.findall(f"{{{LINK}}}labelArc"):
            loc_label = arc.attrib.get(f"{{{XLINK}}}from", "")
            label_key = arc.attrib.get(f"{{{XLINK}}}to", "")
            concept = locs.get(loc_label)
            text = labels.get(label_key)
            if concept and text:
                concept_labels.setdefault(concept, [])
                if text not in concept_labels[concept]:
                    concept_labels[concept].append(text)
    return concept_labels


def _bind_ir_facts(
    ir: VerificationIR,
    bundle: FilingXbrl,
    *,
    ignore_unit_matching: bool = False,
) -> list[dict[str, Any]]:
    bindings = []
    for fact in ir.facts.values():
        binding = _bind_fact(fact, ir, bundle, ignore_unit_matching=ignore_unit_matching)
        if binding is not None:
            bindings.append(binding)
    return bindings


def _apply_authoritative_bindings(ir: VerificationIR, bindings: list[dict[str, Any]]) -> None:
    """Make the authoritative XBRL value override the LLM-extracted fact value.

    The SMT emits ``evidence_<role> = ir.facts[role].value`` (the extraction) *and*
    binds ``role = multiplier * xbrl_value``. When the extraction disagrees with the
    filing's tagged value (e.g. the model read the wrong year), those two assertions
    contradict and the problem is UNSAT regardless of the claim — a false reject of a
    correct answer. Overriding the fact value with the bound XBRL value makes the two
    assertions agree, so verification checks the claim against the authoritative value.
    Soundness is preserved: a wrong claim still fails against the true XBRL value.
    """
    for b in bindings:
        name = b.get("fact_name")
        val = b.get("xbrl_value")
        if name in ir.facts and val is not None:
            mult = b.get("binding_multiplier") or 1.0
            ir.facts[name].value = float(val) * float(mult)


def _bind_fact(
    fact: VerificationFact,
    ir: VerificationIR,
    bundle: FilingXbrl,
    *,
    ignore_unit_matching: bool = False,
) -> dict[str, Any] | None:
    """Bind an IR fact to an XBRL value.

    Tries sources in order:
    1. SEC EDGAR companyfacts, keyed on each fact's fiscal-year tag (fy/fp/form).
       This spans every filing the company submitted, so it resolves the right year
       even when the loaded 10-K does not contain it, and uses EDGAR's own fiscal-year
       labels — which match the dataset's labels regardless of fiscal calendar.
    2. Local XBRL instance from the loaded filing (fallback when the company is not
       in the EDGAR cache).
    """
    if bundle.cik and bundle.edgar_dir is not None:
        binding = _bind_fact_edgar(
            fact,
            ir,
            bundle.cik,
            bundle.edgar_dir,
            ignore_unit_matching=ignore_unit_matching,
        )
        if binding is not None:
            return binding
    return _bind_fact_local(fact, ir, bundle, ignore_unit_matching=ignore_unit_matching)


def _bind_fact_local(
    fact: VerificationFact,
    ir: VerificationIR,
    bundle: FilingXbrl,
    *,
    ignore_unit_matching: bool = False,
) -> dict[str, Any] | None:
    registry_locals = _candidate_concept_locals(fact, None)
    candidate_locals = registry_locals or _candidate_concept_locals(fact, bundle)
    binding_source = "policy_alias_period_context" if registry_locals else "filing_label_linkbase"
    if not candidate_locals:
        return None
    years = _years_for_fact(fact, ir)
    candidates = []
    for local in candidate_locals:
        for (fact_concept, context_id), xbrl_fact in bundle.facts_by_local_context.items():
            if xbrl_fact.local_name != local:
                continue
            context = bundle.contexts.get(context_id)
            if context is None:
                continue
            if years and not _context_matches_year(context, years):
                continue
            candidates.append((xbrl_fact, context))
    candidates = _prefer_no_dimensions(candidates)
    candidates = _dedupe_candidates(candidates)
    if len(candidates) > 1:
        # Disambiguate by the registry's canonical concept order (e.g. NetIncomeLoss
        # before ProfitLoss), NOT by closeness to the LLM-extracted value. Picking the
        # candidate nearest the LLM number makes the binding agree with the answer it is
        # supposed to check — the source of false verifications.
        candidates = _prefer_registry_priority(candidates, fact)
    if len(candidates) > 1:
        # The year filter admits quarterly/interim contexts too; keep the full
        # fiscal-period fact (full-year duration, or year-end instant). Value-blind.
        candidates = _prefer_fiscal_period(candidates, years)
    if len(candidates) != 1:
        return None
    xbrl_fact, context = candidates[0]
    unit_measures = bundle.units.get(xbrl_fact.unit_ref, ())
    if not ignore_unit_matching and not _unit_kind_compatible_for_fact(fact, unit_measures, xbrl_fact.unit_ref):
        return None
    scale = _unit_scale(unit_measures, fact.unit)
    binding_multiplier = _unit_conversion_binding_multiplier(fact, unit_measures, xbrl_fact.unit_ref)
    # Reject if the bound XBRL value is implausibly far from the IR fact value (> 3x).
    # A wrong binding (e.g. balance-sheet asset matched to an amortization expense) would
    # produce a false SMT conflict, so no binding is better than a clearly wrong one.
    if xbrl_fact.value is not None and fact.value:
        scale_decimal = Decimal(str(scale)) if scale else Decimal("1")
        xbrl_decimal = xbrl_fact.value / scale_decimal if scale else xbrl_fact.value
        exact_multiplier = _exact_binding_multiplier(
            fact,
            xbrl_fact.concept,
            xbrl_decimal,
            _binding_tolerance(xbrl_fact, scale_decimal),
        )
        if exact_multiplier is not None:
            binding_multiplier *= exact_multiplier
        xbrl_check = float(xbrl_decimal) * binding_multiplier
        display_tolerance = _display_binding_tolerance(fact)
        diff = abs(xbrl_check - float(fact.value))
        if registry_locals:
            # Rule 1: registry-canonical concept is authoritative -> value-blind bind
            # (override the LLM value; mis-matched heuristic labels keep the gate).
            binding_tolerance = 0.0
        elif diff > display_tolerance:
            return None
        else:
            binding_tolerance = display_tolerance if diff > 1e-9 else 0.0
    else:
        binding_tolerance = 0.0
    xbrl_value: float | None = None
    xbrl_smt_value: str | None = None
    if xbrl_fact.value is not None:
        xbrl_decimal = xbrl_fact.value / Decimal(str(scale)) if scale else xbrl_fact.value
        xbrl_value = float(xbrl_decimal)
        xbrl_smt_value = _format_decimal(xbrl_decimal)
    context_period = _period_from_context(context)
    return {
        "fact_name": fact.name,
        "xbrl_variable": _canonical_xbrl_variable(xbrl_fact.concept, context_period, unit_measures),
        "source_variable": _xbrl_variable(xbrl_fact.concept, xbrl_fact.context_id),
        "canonical_key": _canonical_fact_key(xbrl_fact.concept, context_period, unit_measures),
        "xbrl_value": xbrl_value,
        "xbrl_smt_value": xbrl_smt_value,
        "concept": xbrl_fact.concept,
        "context_id": xbrl_fact.context_id,
        "context_period": context_period,
        "unit_ref": xbrl_fact.unit_ref,
        "unit_measures": list(unit_measures),
        "scale": scale,
        "binding_multiplier": binding_multiplier,
        "binding_kind": _binding_kind(binding_multiplier, binding_tolerance),
        "binding_tolerance": binding_tolerance if binding_tolerance > 0 else 0.0,
        "source": binding_source,
    }


def _fiscal_year_for_fact(fact: VerificationFact, ir: VerificationIR) -> str | None:
    """The fiscal-year label for this fact (e.g. ap_fy2019 -> "2019"), value-blind.

    Prefers the year token in the fact name (the dataset's fiscal label); falls back
    to the IR-derived years. This is matched against EDGAR's `fy` tag, which carries
    the company's own fiscal-year label regardless of calendar alignment.
    """
    matches = re.findall(r"(?:19|20)\d{2}", fact.name or "")
    if matches:
        return matches[-1]
    years = _years_for_fact(fact, ir)
    return max(years) if years else None


def _ordered_concept_qnames(fact: VerificationFact) -> list[str]:
    """Registry concept qnames for this fact, canonical-first (priority order)."""
    out: list[str] = []
    for concept_id in DEFAULT_POLICY_REGISTRY.infer_concepts(fact.name).values():
        concept = DEFAULT_POLICY_REGISTRY.concepts.get(concept_id)
        if concept is None:
            continue
        for qname in concept.xbrl_concepts:
            if qname not in out:
                out.append(qname)
    return out


def _edgar_concept_candidates(data: dict[str, Any], fact: VerificationFact) -> list[tuple[str, str, bool]]:
    """(namespace, concept_name, is_registry) candidates for this fact, in priority order.

    Registry-canonical concepts first (value-blind disambiguation, e.g. NetIncomeLoss
    before ProfitLoss). Only when the registry has no concept for the fact do we fall
    back to filing-label token matching — never to the LLM-extracted value.

    The is_registry flag marks the authoritative (registry-canonical) candidates: those
    are bound value-blind (rule 1), while the heuristic filing-label fallbacks keep the
    plausibility gate so a mis-matched concept cannot inject a false value.
    """
    facts = data.get("facts") or {}
    candidates: list[tuple[str, str, bool]] = []
    seen: set[tuple[str, str]] = set()

    # Authoritative source concept (from the calc-linkbase child the role was built from).
    # Bind straight to it, bypassing fuzzy name resolution that collapses distinct
    # roles (e.g. long- vs short-term debt proceeds/repayments) onto one concept.
    src = getattr(fact, "concept", "") or ""
    if src:
        namespace, _, local = src.partition(":")
        if local and namespace in facts and local in facts[namespace]:
            return [(namespace, local, True)]
        return []

    for qname in _ordered_concept_qnames(fact):
        namespace, _, local = qname.partition(":")
        if local and namespace in facts and local in facts[namespace]:
            key = (namespace, local)
            if key not in seen:
                candidates.append((namespace, local, True))
                seen.add(key)

    if not candidates:
        row_tokens = _label_tokens(fact.row_label) if fact.row_label else frozenset()
        search = row_tokens if len(row_tokens) >= 2 else _label_tokens(fact.name)
        if len(search) >= 2:
            scored: list[tuple[int, str, str]] = []
            for namespace, concepts in facts.items():
                for concept_name, concept_data in concepts.items():
                    label_tokens = _label_tokens(concept_data.get("label") or "")
                    if label_tokens and search <= label_tokens:
                        scored.append((len(label_tokens - search), namespace, concept_name))
            for _extra, namespace, concept_name in sorted(scored):
                key = (namespace, concept_name)
                if key not in seen:
                    candidates.append((namespace, concept_name, False))
                    seen.add(key)
    return candidates


def _primary_fy_entry(concept_data: dict[str, Any], fy: str) -> dict[str, Any] | None:
    """The fy=N filing's primary money-period entry for this concept.

    Kept for existing callers/tests. Binding code uses the unit-aware helper below.
    """
    primary = _primary_fy_entry_with_unit(concept_data, fy, "money")
    return primary[1] if primary else None


def _primary_fy_entry_with_unit(
    concept_data: dict[str, Any],
    fy: str,
    expected_unit_kind: str,
) -> tuple[str, dict[str, Any]] | None:
    """The fy=N filing's primary period with a compatible companyfacts unit."""
    best: tuple[str, str, str, dict[str, Any]] | None = None  # (end, filed, unit, entry)
    for unit_type, entries in (concept_data.get("units") or {}).items():
        if not _unit_kind_compatible(expected_unit_kind, _unit_kind_from_unit_text(unit_type)):
            continue
        for entry in entries:
            if str(entry.get("fy", "")) != str(fy):
                continue
            if str(entry.get("fp", "")).upper() != "FY":
                continue
            if str(entry.get("form", "")).upper() not in {"10-K", "10-K/A"}:
                continue
            end = str(entry.get("end", ""))
            if not end or entry.get("val") is None:
                continue
            filed = str(entry.get("filed", ""))
            if best is None or (end, filed) > (best[0], best[1]):
                best = (end, filed, unit_type, entry)
    return (best[2], best[3]) if best else None


def _prefer_current_noncurrent_variant(
    candidates: list[tuple[str, str, bool]],
    data: dict[str, Any],
    ir: VerificationIR,
    fact: VerificationFact,
) -> list[tuple[str, str, bool]]:
    """Prefer the concept variant implied by the role name / metric context.

    Registry mapping is blind to distinguishing modifiers, so an ambiguous role can bind
    to the wrong sibling:
      * ``property_plant_and_equipment_gross`` -> ``PropertyPlantAndEquipmentNet``
        (should be ...Gross) — the "gross"/"net" distinction, from the role name;
      * ``term_debt`` under a ``non_current`` metric -> ``LongTermDebt`` (should be the
        Noncurrent portion) — the "current"/"non-current" distinction, from the metric.
    We prepend the qualified sibling *only if it exists in companyfacts*, so a spurious
    pair (e.g. a "net" role with no "...Gross" tag) is a harmless no-op and this can never
    bind to a concept the filing didn't tag.
    """
    metric = (getattr(ir, "metric", "") or "").lower()
    fname = (fact.name or "").lower()

    # (preferred_suffix, opposite_suffix) pairs to try, most specific first.
    pairs: list[tuple[str, str]] = []
    if "gross" in fname:
        pairs.append(("Gross", "Net"))
    elif "net" in fname:
        pairs.append(("Net", "Gross"))
    # current/non-current: from the metric, only when the role itself is not already
    # current/non-current-specific (preserves the existing, validated behavior).
    if "current" not in fname and "noncurrent" not in fname:
        if "noncurrent" in metric or "non_current" in metric or "non current" in metric:
            pairs.append(("Noncurrent", "Current"))
        elif "current" in metric:
            pairs.append(("Current", "Noncurrent"))
    if not pairs:
        return candidates

    def sibling(local: str, qualifier: str, other: str) -> str:
        if local.endswith(qualifier):
            return local
        if local.endswith(other):
            return local[: -len(other)] + qualifier
        return local + qualifier

    prefix = []
    for namespace, concept_name, is_registry in candidates:
        for qualifier, other in pairs:
            q = sibling(concept_name, qualifier, other)
            if q != concept_name and namespace in data.get("facts", {}) and q in data["facts"][namespace]:
                key = (namespace, q, is_registry)
                if key not in prefix:
                    prefix.append(key)
    return prefix + list(candidates) if prefix else candidates


def _bind_fact_edgar(
    fact: VerificationFact,
    ir: VerificationIR,
    cik: str,
    cache_dir: Path,
    *,
    ignore_unit_matching: bool = False,
) -> dict[str, Any] | None:
    """Bind an IR fact to its EDGAR companyfacts value, keyed on the fiscal-year tag.

    Resolution is value-blind: concept by registry priority, period by the fact's
    fiscal-year label (`fy`) and the filing's primary (latest-ending) period. No use
    of the LLM-extracted value for selection, sign, or plausibility.
    """
    data = EdgarCompanyFactsCache.get(cik, cache_dir)
    if not data:
        return None
    fy = _fiscal_year_for_fact(fact, ir)
    if not fy:
        return None

    expected_unit_kind = "unknown" if ignore_unit_matching else _expected_unit_kind_for_fact(fact)
    candidates = _edgar_concept_candidates(data, fact)
    candidates = _prefer_current_noncurrent_variant(candidates, data, ir, fact)
    for namespace, concept_name, is_registry in candidates:
        primary = _primary_fy_entry_with_unit(
            data["facts"][namespace][concept_name],
            fy,
            expected_unit_kind,
        )
        if primary is None:
            continue
        unit_type, entry = primary

        qname = f"{namespace}:{concept_name}"
        period_end = str(entry.get("end", ""))
        period_start = str(entry.get("start", ""))
        accn = str(entry.get("accn", ""))
        context_id = f"edgar_{period_end}_{accn}" if accn else f"edgar_{period_end}"
        scale = _unit_scale((unit_type,), fact.unit)
        xbrl_decimal = Decimal(str(entry["val"])) / Decimal(str(scale)) if scale else Decimal(str(entry["val"]))
        context_period = {
            "instant": "" if period_start else period_end,
            "start_date": period_start,
            "end_date": period_end,
            "dimensions": [],
        }
        unit_measures = (unit_type,)
        binding_multiplier = (
            1.0
            if ignore_unit_matching
            else _unit_conversion_binding_multiplier(fact, unit_measures, unit_type)
        )

        xbrl_check = float(xbrl_decimal) * binding_multiplier
        diff = abs(xbrl_check - float(fact.value))
        if is_registry:
            # Rule 1: a registry-canonical concept is authoritative, so bind its value
            # VALUE-BLIND — override the LLM-extracted number rather than gate on it.
            # This is exactly how a wrong operand (e.g. ProfitLoss bound where the
            # policy requires NetIncomeLoss) gets caught downstream by the solver.
            binding_tolerance = 0.0
        else:
            display_tolerance = _display_binding_tolerance(fact)
            if diff > display_tolerance:
                continue
            binding_tolerance = display_tolerance if diff > 1e-9 else 0.0

        return {
            "fact_name": fact.name,
            "xbrl_variable": _canonical_xbrl_variable(qname, context_period, unit_measures),
            "source_variable": _xbrl_variable(qname, context_id),
            "canonical_key": _canonical_fact_key(qname, context_period, unit_measures),
            "xbrl_value": float(xbrl_decimal),
            "xbrl_smt_value": _format_decimal(xbrl_decimal),
            "concept": qname,
            "context_id": context_id,
            "context_period": context_period,
            "unit_ref": unit_type,
            "unit_measures": list(unit_measures),
            "scale": scale,
            "binding_multiplier": binding_multiplier,
            "binding_kind": _binding_kind(binding_multiplier, binding_tolerance),
            "binding_tolerance": binding_tolerance if binding_tolerance > 0 else 0.0,
            "source": "edgar_companyfacts_fy",
        }
    return None


class EdgarCompanyFactsCache:
    """Fetches and disk-caches SEC EDGAR companyfacts JSON.

    GET data.sec.gov/api/xbrl/companyfacts/CIK{10-digit-padded}.json
    Returns every XBRL fact ever filed by a company across all namespaces
    (us-gaap standard + company extension namespaces like nflx:, amzn:, etc.)
    with labels and historical period values.
    """

    _URL_TEMPLATE = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    _memory: dict[str, dict[str, Any] | None] = {}

    @classmethod
    def get(cls, cik: str, cache_dir: Path) -> dict[str, Any] | None:
        """Return companyfacts dict for the given CIK (stripped of leading zeros)."""
        normalized = cik.lstrip("0") or "0"
        if normalized in cls._memory:
            return cls._memory[normalized]

        padded = normalized.zfill(10)
        cache_path = cache_dir / f"CIK{padded}.json"

        if cache_path.exists():
            try:
                with cache_path.open(encoding="utf-8") as fh:
                    data = json.load(fh)
                cls._memory[normalized] = data
                return data
            except Exception:
                pass

        url = cls._URL_TEMPLATE.format(cik=padded)
        user_agent = _require_sec_user_agent()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": user_agent})
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
        except Exception:
            cls._memory[normalized] = None
            return None

        cache_dir.mkdir(parents=True, exist_ok=True)
        try:
            with cache_path.open("w", encoding="utf-8") as fh:
                json.dump(data, fh)
        except Exception:
            pass

        cls._memory[normalized] = data
        return data

    @classmethod
    def clear(cls) -> None:
        cls._memory.clear()


def _candidate_concept_locals(fact: VerificationFact, bundle: "FilingXbrl | None" = None) -> set[str]:
    # Use only fact.name for policy inference — row_label/source_quote contain qualifier words
    # (e.g. "amortization of streaming content assets") whose substrings match unrelated concepts
    # (e.g. "assets" matches TotalAssetsLike).  Fact names are already semantically precise.
    source_concept = getattr(fact, "concept", "") or ""
    if source_concept:
        return {_local_from_qname(source_concept)}
    qnames = set()
    concepts = DEFAULT_POLICY_REGISTRY.infer_concepts(fact.name)
    for concept_id in concepts.values():
        concept = DEFAULT_POLICY_REGISTRY.concepts.get(concept_id)
        if concept is not None:
            qnames.update(concept.xbrl_concepts)
    compact_inputs = {_compact(value) for value in (fact.name, fact.row_label) if value}
    for concept in DEFAULT_POLICY_REGISTRY.concepts.values():
        for qname in concept.xbrl_concepts:
            local = _local_from_qname(qname)
            if _compact(local) in compact_inputs:
                qnames.add(qname)
    # Fallback: match against the filing's own label linkbase
    if not qnames and bundle is not None and bundle.concept_labels and fact.row_label:
        row_tokens = _label_tokens(fact.row_label)
        if len(row_tokens) >= 2:  # require at least 2 meaningful tokens to avoid broad matches
            for concept_qname, labels in bundle.concept_labels.items():
                for label in labels:
                    label_tokens = _label_tokens(label)
                    # row tokens must all appear in the filing label tokens
                    if row_tokens and row_tokens <= label_tokens:
                        qnames.add(concept_qname)
                        break
    return {_local_from_qname(qname) for qname in qnames if qname}


def _years_for_fact(fact: VerificationFact, ir: VerificationIR) -> set[str]:
    values = [fact.period, fact.column, fact.name]
    if not fact.period and not fact.column:
        values.append(ir.period)
    years = set()
    for value in values:
        years.update(re.findall(r"(?:19|20)\d{2}", value or ""))
    return years


def _context_matches_year(context: XbrlContext, years: set[str]) -> bool:
    return any(
        date[:4] in years
        for date in (context.instant, context.end_date, context.start_date)
        if date
    )


def _prefer_no_dimensions(candidates: list[tuple[XbrlFact, XbrlContext]]) -> list[tuple[XbrlFact, XbrlContext]]:
    no_dimensions = [candidate for candidate in candidates if not candidate[1].dimensions]
    return no_dimensions or candidates


def _context_duration_days(context: XbrlContext) -> int:
    if not (context.start_date and context.end_date):
        return 0
    try:
        return (date.fromisoformat(context.end_date) - date.fromisoformat(context.start_date)).days
    except ValueError:
        return 0


def _prefer_fiscal_period(
    candidates: list[tuple[XbrlFact, XbrlContext]],
    years: set[str],
) -> list[tuple[XbrlFact, XbrlContext]]:
    """Keep the candidate(s) reported for the full fiscal period, value-blind.

    The year filter admits any context touching the target year — including
    quarterly/partial durations and interim instants. Disambiguate by period shape,
    not by value: for duration facts prefer the full fiscal year (~365 days) ending
    in the target year; for instant facts prefer the fiscal year-end (latest instant
    in the target year).
    """
    durations = [(f, c) for f, c in candidates if c.start_date and c.end_date]
    instants = [(f, c) for f, c in candidates if c.instant and not (c.start_date and c.end_date)]

    # Mixed period-types mean the candidates are different concepts (a balance/instant
    # vs a flow/duration, e.g. AccountsPayableCurrent vs IncreaseDecreaseInAccountsPayable).
    # That is a concept ambiguity, not a period one — do not resolve it here by preferring
    # one period-type. Leave both so the caller fails safely rather than binding the wrong
    # concept.
    if durations and instants:
        return candidates

    if durations:
        full_year = [
            (f, c) for f, c in durations
            if 350 <= _context_duration_days(c) <= 380 and (c.end_date[:4] in years)
        ]
        return full_year or candidates

    in_year = [(f, c) for f, c in instants if c.instant[:4] in years]
    if in_year:
        latest = max(c.instant for _f, c in in_year)
        return [(f, c) for f, c in in_year if c.instant == latest]

    return candidates


def _dedupe_candidates(candidates: list[tuple[XbrlFact, XbrlContext]]) -> list[tuple[XbrlFact, XbrlContext]]:
    out = []
    seen = set()
    for xbrl_fact, context in candidates:
        key = (xbrl_fact.local_name, xbrl_fact.context_id, xbrl_fact.unit_ref)
        if key in seen:
            continue
        seen.add(key)
        out.append((xbrl_fact, context))
    return out


def _ordered_concept_locals(fact: VerificationFact) -> list[str]:
    """Registry concept locals for this fact in canonical priority order.

    The registry lists each semantic bucket's XBRL concepts most-canonical first
    (e.g. NetIncomeLike -> [NetIncomeLoss, ProfitLoss, ...]), so the list index is
    the disambiguation priority. Value-blind: derived only from the fact's name.
    """
    ordered: list[str] = []
    for concept_id in DEFAULT_POLICY_REGISTRY.infer_concepts(fact.name).values():
        concept = DEFAULT_POLICY_REGISTRY.concepts.get(concept_id)
        if concept is None:
            continue
        for qname in concept.xbrl_concepts:
            local = _local_from_qname(qname)
            if local not in ordered:
                ordered.append(local)
    return ordered


def _prefer_registry_priority(
    candidates: list[tuple[XbrlFact, XbrlContext]],
    fact: VerificationFact,
) -> list[tuple[XbrlFact, XbrlContext]]:
    """Keep the candidate(s) whose concept ranks earliest in the registry order.

    Replaces value-based disambiguation: the choice between concepts (e.g.
    NetIncomeLoss vs ProfitLoss) is made by the registry's canonical ordering, never
    by which value happens to match the LLM's extracted number.
    """
    priority = _ordered_concept_locals(fact)
    if not priority:
        return candidates

    def rank(item: tuple[XbrlFact, XbrlContext]) -> int:
        local = item[0].local_name
        return priority.index(local) if local in priority else len(priority)

    best = min(rank(item) for item in candidates)
    return [item for item in candidates if rank(item) == best]


_OUTFLOW_MAGNITUDE_CONCEPT_LOCALS = frozenset({
    "PaymentsToAcquirePropertyPlantAndEquipment",
    "PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
})


def _binding_tolerance(fact: XbrlFact, scale: Decimal) -> Decimal:
    if not scale:
        return Decimal("0.000001")
    return max(Decimal("0.000001"), _fact_tolerance(fact) / scale)


def _exact_binding_multiplier(
    fact: VerificationFact,
    concept: str,
    xbrl_value: Decimal,
    tolerance: Decimal,
) -> float | None:
    expected = Decimal(str(fact.value))
    if _decimal_close(xbrl_value, expected, tolerance):
        return 1.0
    if not _allows_outflow_magnitude_binding(fact, concept):
        return None
    if not expected or not xbrl_value:
        return None
    if not _decimal_close(abs(xbrl_value), abs(expected), tolerance):
        return None
    if (expected < 0 < xbrl_value) or (xbrl_value < 0 < expected):
        return -1.0
    return None


def _allows_outflow_magnitude_binding(fact: VerificationFact, concept: str) -> bool:
    local = _local_from_qname(concept)
    if local in _OUTFLOW_MAGNITUDE_CONCEPT_LOCALS:
        return True
    if local.startswith("PaymentsToAcquire") or "CapitalExpenditure" in local:
        return True
    text = _compact(f"{fact.name} {fact.row_label}")
    return local.startswith("PurchaseOf") and ("capex" in text or "capitalexpenditure" in text)


def _decimal_close(left: Decimal, right: Decimal, tolerance: Decimal) -> bool:
    return abs(left - right) <= tolerance


def _instantiate_constraints(bundle: FilingXbrl) -> list[dict[str, Any]]:
    constraints = []
    for group_index, group in enumerate(bundle.calc_groups):
        child_concepts = [child.concept for child in group.children]
        context_ids = sorted(
            context_id
            for parent_concept, context_id in bundle.facts_by_local_context
            if parent_concept == group.parent_concept
        )
        for context_id in context_ids:
            parent_fact = bundle.facts_by_local_context.get((group.parent_concept, context_id))
            if parent_fact is None:
                continue
            child_facts = [bundle.facts_by_local_context.get((concept, context_id)) for concept in child_concepts]
            if any(child is None for child in child_facts):
                continue
            child_facts_typed = [child for child in child_facts if child is not None]
            if any(child.unit_ref != parent_fact.unit_ref for child in child_facts_typed):
                continue
            scale = Decimal(str(_unit_scale(bundle.units.get(parent_fact.unit_ref, ()), "USD millions")))
            tolerance = _fact_tolerance(parent_fact) / scale
            children = []
            for child, child_fact in zip(group.children, child_facts_typed):
                tolerance += abs(child.weight) * (_fact_tolerance(child_fact) / scale)
                children.append(
                    {
                        "variable": _canonical_variable_for_fact(bundle, child_fact),
                        "source_variable": _xbrl_variable(child_fact.concept, child_fact.context_id),
                        "canonical_key": _canonical_key_for_fact(bundle, child_fact),
                        "concept": child_fact.concept,
                        "weight": float(child.weight),
                    }
                )
            name = _assertion_name(
                "xbrl_calc_"
                + str(group_index)
                + "_"
                + _hashish(group.role)
                + "_"
                + group.parent_local
                + "_"
                + context_id
            )
            constraints.append(
                {
                    "name": name,
                    "role": group.role,
                    "parent_variable": _canonical_variable_for_fact(bundle, parent_fact),
                    "parent_source_variable": _xbrl_variable(parent_fact.concept, parent_fact.context_id),
                    "parent_canonical_key": _canonical_key_for_fact(bundle, parent_fact),
                    "parent_concept": parent_fact.concept,
                    "context_id": context_id,
                    "children": children,
                    "tolerance": float(tolerance),
                    "source_path": group.source_path,
                }
            )
    return constraints


def _constraints_connected_to_bindings(
    constraints: list[dict[str, Any]],
    bound_xbrl_variables: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    connected = []
    dropped = []
    for constraint in constraints:
        variables = _constraint_variables(constraint)
        if bound_xbrl_variables and variables & bound_xbrl_variables:
            connected.append(constraint)
        else:
            dropped.append(_dropped_constraint(constraint, [], "not_connected_to_formula_fact"))
    return connected, dropped


def _evidence_facts_from_constraints(
    constraints: list[dict[str, Any]],
    bundle: FilingXbrl,
    exclude_variables: set[str],
) -> dict[str, VerificationFact]:
    needed_variables = sorted(
        set().union(*(_constraint_variables(constraint) for constraint in constraints))
        if constraints
        else set()
    )
    facts_by_variable = _facts_by_variable(bundle)
    evidence_facts: dict[str, VerificationFact] = {}
    for variable in needed_variables:
        if variable in exclude_variables:
            continue
        xbrl_fact = facts_by_variable.get(variable)
        if xbrl_fact is None or xbrl_fact.value is None:
            continue
        context = bundle.contexts.get(xbrl_fact.context_id)
        measures = bundle.units.get(xbrl_fact.unit_ref, ())
        scale = Decimal(str(_unit_scale(measures, "USD millions")))
        value = xbrl_fact.value / scale if scale else xbrl_fact.value
        evidence_facts[variable] = VerificationFact(
            name=variable,
            value=float(value),
            unit=_scaled_unit_label(measures, scale),
            fact_type="xbrl_instance",
            raw_value=float(xbrl_fact.value),
            raw_unit=" ".join(measures),
            source_scale="millions" if scale == Decimal("1000000.0") else "ones",
            source_scale_quote=_unit_quote(measures),
            source_quote=f"XBRL instance fact {xbrl_fact.concept}={xbrl_fact.value} contextRef={xbrl_fact.context_id}",
            chunk_id=f"xbrl:{bundle.doc_name}:{xbrl_fact.context_id}:{xbrl_fact.local_name}",
            period=_context_period_label(context),
            row_label=xbrl_fact.concept,
            column=_context_period_label(context),
        )
    return evidence_facts


def _prune_constraints(
    constraints: list[dict[str, Any]],
    asserted_xbrl_variables: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    kept = []
    dropped = []
    for constraint in constraints:
        missing = sorted(_constraint_variables(constraint) - asserted_xbrl_variables)
        if missing:
            dropped.append(_dropped_constraint(constraint, missing, "missing_asserted_fact"))
        else:
            kept.append(constraint)
    return kept, dropped


def _constraint_variables(constraint: dict[str, Any]) -> set[str]:
    variables = {str(constraint.get("parent_variable") or "")}
    variables.update(
        str(child.get("variable") or "")
        for child in constraint.get("children") or []
    )
    variables.discard("")
    return variables


def _dropped_constraint(constraint: dict[str, Any], missing_variables: list[str], reason: str) -> dict[str, Any]:
    return {
        "name": constraint.get("name", ""),
        "role": constraint.get("role", ""),
        "context_id": constraint.get("context_id", ""),
        "parent_variable": constraint.get("parent_variable", ""),
        "parent_concept": constraint.get("parent_concept", ""),
        "missing_variables": missing_variables,
        "reason": reason,
    }


def _facts_by_variable(bundle: FilingXbrl) -> dict[str, XbrlFact]:
    facts: dict[str, XbrlFact] = {}
    for fact in bundle.facts_by_local_context.values():
        facts.setdefault(_canonical_variable_for_fact(bundle, fact), fact)
    return facts


def _grounding_status(status: str, bindings: list[dict[str, Any]], constraints: list[dict[str, Any]]) -> str:
    if bindings and constraints:
        return "LINKBASE_OK"
    if bindings:
        return "INSTANCE_ONLY"
    if status == "not_sec_xbrl_filing":
        return "NOT_SEC_XBRL"
    if status in {"missing_calculation_linkbase", "xbrl_only_no_calculation_linkbase"}:
        return "NO_LINKBASE"
    if status == "missing_manifest_entry":
        return "MISSING_MANIFEST"
    if status in {"no_safe_fact_bindings", "partial_bindings"}:
        return "NO_SAFE_BINDING"
    if status == "no_instantiated_calculation_constraints":
        return "NO_LINKBASE_CONSTRAINTS"
    if status == "no_constraints_connected_to_formula_facts":
        return "INSTANCE_ONLY"
    if status == "no_surviving_calculation_constraints":
        return "INSTANCE_ONLY" if bindings else "NO_SAFE_BINDING"
    return status.upper() if status else "UNKNOWN"


def _canonical_variable_for_fact(bundle: FilingXbrl, fact: XbrlFact) -> str:
    context = bundle.contexts.get(fact.context_id)
    return _canonical_xbrl_variable(
        fact.concept,
        _period_from_context(context),
        bundle.units.get(fact.unit_ref, ()),
    )


def _canonical_key_for_fact(bundle: FilingXbrl, fact: XbrlFact) -> str:
    context = bundle.contexts.get(fact.context_id)
    return _canonical_fact_key(
        fact.concept,
        _period_from_context(context),
        bundle.units.get(fact.unit_ref, ()),
    )


def _period_from_context(context: XbrlContext | None) -> dict[str, Any]:
    if context is None:
        return {"instant": "", "start_date": "", "end_date": "", "dimensions": []}
    return {
        "instant": context.instant,
        "start_date": context.start_date,
        "end_date": context.end_date,
        "dimensions": list(context.dimensions),
    }


def _canonical_xbrl_variable(concept: str, context_period: dict[str, Any], unit_measures: Iterable[str]) -> str:
    return _symbol("xbrl_fact__" + _canonical_fact_key(concept, context_period, unit_measures))


def _canonical_fact_key(concept: str, context_period: dict[str, Any], unit_measures: Iterable[str]) -> str:
    return "__".join(
        [
            concept,
            _canonical_period_key(context_period),
            _canonical_unit_key(unit_measures),
            _canonical_dimensions_key(context_period.get("dimensions") or []),
        ]
    )


def _canonical_period_key(context_period: dict[str, Any]) -> str:
    instant = str(context_period.get("instant") or "")
    start = str(context_period.get("start_date") or "")
    end = str(context_period.get("end_date") or "")
    if instant and not start:
        return f"instant:{instant}"
    if start or end:
        return f"duration:{start}:{end}"
    if end:
        return f"instant:{end}"
    return "period:unknown"


def _canonical_unit_key(unit_measures: Iterable[str]) -> str:
    measures = []
    for measure in unit_measures:
        text = str(measure or "").strip()
        if not text:
            continue
        local = text.split(":")[-1]
        measures.append(local.upper() if local.upper() == "USD" else local)
    return "unit:" + "_".join(sorted(measures)) if measures else "unit:none"


def _canonical_dimensions_key(dimensions: Iterable[str]) -> str:
    values = sorted(str(dim).strip() for dim in dimensions if str(dim).strip())
    if not values:
        return "dims:none"
    joined = "|".join(values)
    if len(joined) > 120:
        return "dims:" + _hashish(joined)
    return "dims:" + joined


def _scaled_unit_label(measures: Iterable[str], scale: Decimal) -> str:
    if scale == Decimal("1000000.0") and any(measure.endswith(":USD") or measure == "USD" for measure in measures):
        return "USD millions"
    return " ".join(measures)


def _unit_quote(measures: Iterable[str]) -> str:
    values = list(measures)
    return "XBRL unit " + ", ".join(values) if values else ""


def _context_period_label(context: XbrlContext | None) -> str:
    if context is None:
        return ""
    if context.instant:
        return context.instant
    if context.start_date or context.end_date:
        return f"{context.start_date} to {context.end_date}".strip()
    return context.context_id


def _fact_tolerance(fact: XbrlFact) -> Decimal:
    decimals = (fact.decimals or "").strip().lower()
    if decimals in {"inf", "infinite"}:
        return Decimal("0")
    try:
        places = int(decimals)
    except ValueError:
        places = 0
    return Decimal("0.5") * (Decimal(10) ** Decimal(-places))


_MILLION_ALIASES = frozenset({"m", "million", "millions", "mm", "usd millions", "usd million", "$ millions", "$ million"})
_BILLION_ALIASES = frozenset({"b", "billion", "billions", "usd billions", "usd billion", "$ billions", "$ billion"})
_THOUSAND_ALIASES = frozenset({"k", "thousand", "thousands", "usd thousands", "usd thousand"})


def _unit_scale(measures: Iterable[str], target_unit: str) -> float:
    target = (target_unit or "").lower().strip()
    is_usd = any(_unit_kind_from_unit_text(measure) == "money" for measure in measures)
    if not is_usd:
        return 1.0
    if target in _MILLION_ALIASES or ("usd" in target and "million" in target):
        return 1_000_000.0
    if target in _BILLION_ALIASES or ("usd" in target and "billion" in target):
        return 1_000_000_000.0
    if target in _THOUSAND_ALIASES or ("usd" in target and "thousand" in target):
        return 1_000.0
    return 1.0


def _unit_kind_compatible_for_fact(
    fact: VerificationFact,
    measures: Iterable[str],
    unit_ref: str = "",
) -> bool:
    expected = _expected_unit_kind_for_fact(fact)
    actual = _actual_unit_kind(measures, unit_ref)
    return _unit_kind_compatible(expected, actual)


def _unit_conversion_binding_multiplier(
    fact: VerificationFact,
    measures: Iterable[str],
    unit_ref: str = "",
) -> float:
    expected = _expected_unit_kind_for_fact(fact)
    actual = _actual_unit_kind(measures, unit_ref)
    if expected == "percent" and actual == "ratio":
        return 100.0
    if expected == "ratio" and actual == "percent":
        return 0.01
    return 1.0


def _actual_unit_kind(measures: Iterable[str], unit_ref: str = "") -> str:
    measure_text = " ".join(str(measure) for measure in measures if measure)
    if measure_text:
        return _unit_kind_from_unit_text(measure_text)
    return _unit_kind_from_unit_text(unit_ref)


def _binding_kind(multiplier: float, tolerance: float = 0.0) -> str:
    rounded = tolerance > 0
    if multiplier == -1.0:
        base = "outflow_magnitude"
    elif multiplier == 100.0:
        base = "ratio_to_percent"
    elif multiplier == 0.01:
        base = "percent_to_ratio"
    else:
        base = "same_sign"
    return f"rounded_{base}" if rounded else base


def _display_binding_tolerance(fact: VerificationFact) -> float:
    value = float(fact.value)
    unit_kind = _expected_unit_kind_for_fact(fact)
    if unit_kind in {"percent", "ratio"} and value.is_integer():
        return 0.5
    text = str(fact.raw_value if fact.raw_value is not None else fact.value)
    if "e" in text.lower():
        return 1e-6
    if "." in text:
        decimals = len(text.rstrip("0").split(".", 1)[1])
        if decimals > 0:
            return 0.5 * (10 ** -decimals)
    return 0.5


def _expected_unit_kind_for_fact(fact: VerificationFact) -> str:
    return _unit_kind_from_unit_text(" ".join(value for value in (fact.unit, fact.raw_unit) if value))


def _unit_kind_from_unit_text(value: str) -> str:
    text = (value or "").lower()
    if not text:
        return "unknown"
    if "usd" in text or "$" in text or "iso4217" in text:
        return "money"
    if "percent" in text or "percentage" in text or "%" in text:
        return "percent"
    if "ratio" in text or "pure" in text or "xbrli:pure" in text:
        return "ratio"
    return "unknown"


def _unit_kind_compatible(expected: str, actual: str) -> bool:
    expected = (expected or "").lower()
    actual = (actual or "").lower()
    if not expected or expected == "unknown" or not actual or actual == "unknown":
        return True
    if expected == actual:
        return True
    if expected == "percent" and actual == "ratio":
        return True
    if expected == "ratio" and actual == "percent":
        return True
    return False


def _namespace_map(path: Path) -> dict[str, str]:
    nsmap: dict[str, str] = {}
    for _, item in ElementTree.iterparse(path, events=("start-ns",)):
        prefix, uri = item
        if uri not in nsmap:
            nsmap[uri] = prefix or ""
    return nsmap


def _split_tag(tag: str) -> tuple[str, str]:
    if tag.startswith("{") and "}" in tag:
        namespace, local = tag[1:].split("}", 1)
        return namespace, local
    return "", tag


def _qname(nsmap: dict[str, str], namespace: str, local: str) -> str:
    prefix = nsmap.get(namespace, "")
    return f"{prefix}:{local}" if prefix else local


def _concept_from_href(href: str) -> str:
    fragment = href.rsplit("#", 1)[-1]
    if "_" not in fragment:
        return fragment
    prefix, local = fragment.split("_", 1)
    return f"{prefix}:{local}"


def _local_from_qname(qname: str) -> str:
    if ":" in qname:
        return qname.split(":", 1)[1]
    if "_" in qname:
        return qname.split("_", 1)[1]
    return qname


def _child_text(element: ElementTree.Element | None, tag: str) -> str:
    if element is None:
        return ""
    child = element.find(tag)
    return (child.text or "").strip() if child is not None else ""


def _decimal_text(value: str | None) -> Decimal | None:
    text = (value or "").strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def _xbrl_variable(concept: str, context_id: str) -> str:
    return _symbol("xbrl_" + concept.replace(":", "_") + "__" + context_id)


def _symbol(value: str, limit: int = 220) -> str:
    symbol = re.sub(r"[^A-Za-z0-9_]+", "_", value)
    symbol = re.sub(r"_+", "_", symbol).strip("_")
    if not symbol or not re.match(r"[A-Za-z_]", symbol):
        symbol = f"x_{symbol}"
    if len(symbol) > limit:
        suffix = "_" + _hashish(symbol)
        symbol = symbol[: max(1, limit - len(suffix))].rstrip("_") + suffix
    return symbol


def _assertion_name(value: str) -> str:
    return _symbol(value, limit=180)


def _compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


_STOP_WORDS = frozenset({"and", "or", "of", "the", "a", "an", "in", "to", "net", "total"})

def _label_tokens(value: str) -> frozenset[str]:
    """Lowercase alphabetic tokens, minus stop words, from a label string."""
    tokens = re.findall(r"[a-z]+", (value or "").lower())
    return frozenset(t for t in tokens if t not in _STOP_WORDS and len(t) > 1)


def _hashish(value: str) -> str:
    total = 0
    for char in value:
        total = ((total * 33) + ord(char)) % 1_000_000_007
    return str(total)


def _weighted_sum(children: Iterable[tuple[str, Decimal]]) -> str:
    terms = []
    for variable, weight in children:
        if weight == Decimal("1"):
            terms.append(variable)
        else:
            terms.append(f"(* {format_number(float(weight))} {variable})")
    if not terms:
        return "0"
    if len(terms) == 1:
        return terms[0]
    return f"(+ {' '.join(terms)})"


def _insert_before_check_sat(smtlib: str, addition: str) -> str:
    match = re.search(r"\(\s*check-sat\s*\)", smtlib)
    if match is None:
        return smtlib.rstrip() + "\n" + addition + "\n"
    return smtlib[: match.start()].rstrip() + "\n" + addition + "\n\n" + smtlib[match.start():].lstrip()


def _declared_variables(smtlib: str) -> set[str]:
    return set(re.findall(r"\(\s*declare-const\s+([A-Za-z_][A-Za-z0-9_]*)\s+Real\s*\)", smtlib))
