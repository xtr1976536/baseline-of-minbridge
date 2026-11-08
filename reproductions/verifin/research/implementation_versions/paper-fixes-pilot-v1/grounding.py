"""Value-blind filing-local binding; no benchmark proof or answer is accepted."""
from __future__ import annotations
from dataclasses import dataclass
import ast
from datetime import date
from decimal import Decimal
from pathlib import Path
import json
import re
from verifiqa.policy.registry import DEFAULT_POLICY_REGISTRY as REGISTRY

class Unresolved(ValueError):
    pass

def tokens(text):
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", str(text)).lower()
    text = text.replace("non-current", "noncurrent").replace("non current", "noncurrent")
    return {x for x in re.findall(r"[a-z0-9]+", text) if x not in {"the", "of", "and", "a", "in"}}

def unit(text):
    t = text.lower().replace("iso4217:", "")
    scale = next((Decimal(v) for k, v in [("billion", "1e9"), ("million", "1e6"), ("thousand", "1e3")] if k in t), Decimal(1))
    for currency in ("usd", "eur", "gbp", "cny", "jpy", "cad", "aud"):
        if currency in t or (currency == "usd" and ("$" in t or "dollar" in t)):
            if "share" in t and ("/" in t or "per" in t): return currency+"/shares", scale
            return currency, scale
    if "percent" in t or "%" in t: return "pure", Decimal(".01")
    if "share" in t: return "shares", scale
    if any(x in t for x in ["ratio", "pure", "number", "count", "dimensionless"]): return "pure", Decimal(1)
    raise Unresolved("unknown_unit:"+text)

def conversion(source, target):
    a, sa = unit(source)
    b, sb = unit(target)
    if a != b:
        raise Unresolved("unit_mismatch:"+a+":"+b)
    return sa/sb

@dataclass
class Filing:
    data: dict
    @classmethod
    def load(cls, path):
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def period_candidates(self, period):
        exact = re.findall(r"\d{4}-\d{2}-\d{2}", period)
        years = re.findall(r"(?:19|20)\d{2}", period)
        if exact: return {exact[-1]}
        if len(set(years)) != 1:
            raise Unresolved("ambiguous_role_period:"+period)
        if re.search(r"q[1-4]|quarter|month|interim", period, re.I):
            quarter=re.search(r'q([1-4])',period,re.I)
            filing_quarter=re.search(r'Q([1-4])',self.data.get('doc_name',''))
            if (quarter and filing_quarter and quarter[1]==filing_quarter[1]
                    and str(self.data.get('fiscal_year'))==years[0] and self.data.get('period_end')):
                return {self.data['period_end']}
            raise Unresolved("quarter_requires_exact_end_date_or_matching_source_quarter")
        fy = self.data.get("fiscal_year")
        end = self.data.get("period_end")
        offset = int(end[:4])-int(fy) if end and fy else 0
        calendar_year = int(years[0])+offset
        anchor = None
        if end:
            try: anchor = date.fromisoformat(end).replace(year=calendar_year)
            except ValueError: anchor = date(calendar_year,2,28)
        ends = set()
        for f in self.data["facts"]:
            p = f["period"]
            d = p.get("instant") or p.get("end_date")
            if d and ((anchor and abs((date.fromisoformat(d)-anchor).days)<=15) or (not anchor and int(d[:4])==calendar_year)):
                # Annual duration or year-end instant only; never a Q1 value.
                if p.get("start_date") and not 300 <= (date.fromisoformat(d)-date.fromisoformat(p["start_date"])).days <= 400:
                    continue
                ends.add(d)
        return ends

    def bind(self, role, expected_unit, period, extracted=None):
        period = role.period or period
        ends = self.period_candidates(period)
        if not ends: raise Unresolved("missing_reporting_period:"+period)
        candidates = []
        for f in self.data["facts"]:
            p = f["period"]
            if (p.get("instant") or p.get("end_date")) not in ends or p.get("dimensions"):
                continue
            if p.get('start_date') and not re.search(r'\d{4}-\d{2}-\d{2}',period):
                days=(date.fromisoformat(p['end_date'])-date.fromisoformat(p['start_date'])).days
                if re.search(r'q[1-4]',period,re.I):
                    if not 70<=days<=110:continue
                elif not 300<=days<=400:continue
            try: conversion(f["unit"], expected_unit)
            except Unresolved: continue
            candidates.append(f)
        method = "linkbase_concept" if role.concept else "concept_registry"
        if role.concept:
            qnames = [role.concept]
        else:
            concepts = REGISTRY.infer_concepts(role.name)
            qnames = [q for cid in concepts.values() for q in REGISTRY.concepts[cid].xbrl_concepts]
        chosen = []
        if qnames:
            for qname in qnames:
                found = [f for f in candidates if f["concept"] == qname]
                if found:
                    chosen = found
                    break
        else:
            method = "symbolic_label_heuristic"
            label = getattr(extracted, "row_label", "") or (role.aliases[0] if role.aliases else role.name)
            required = tokens(label)
            scored = []
            for f in candidates:
                labels = self.data.get("labels", {}).get(f["concept"], []) or [f["concept"].split(":")[-1]]
                scores = [len(tokens(x)-required) for x in labels if required and required <= tokens(x)]
                if scores: scored.append((min(scores), f))
            if scored:
                best = min(x[0] for x in scored)
                chosen = [f for score, f in scored if score == best]
        unique = {}
        for f in chosen:
            p = f["period"]
            k = (f["concept"], f["unit"], p.get("instant"), p.get("start_date"), p.get("end_date"), str(Decimal(f["value"])))
            unique.setdefault(k, f)
        if len(unique) != 1:
            raise Unresolved("missing_or_ambiguous_filing_fact:"+role.name)
        f = next(iter(unique.values()))
        value = Decimal(f["value"])*conversion(f["unit"], expected_unit)
        if method == "symbolic_label_heuristic":
            if extracted is None: raise Unresolved("heuristic_requires_extracted_value")
            ev = Decimal(str(extracted.value))*conversion(extracted.unit, expected_unit)
            if (value == 0) != (ev == 0) or (value*ev < 0) or (value and not Decimal(1)/3 <= abs(ev/value) <= 3):
                raise Unresolved("heuristic_plausibility_failed:"+role.name)
        return {"role": role.name, "value": str(value), "unit": expected_unit, "concept": f["concept"],
                "period": f["period"], "accession": self.data["accession"], "source_fact_id": f["id"],
                "source_url": self.data["source_url"], "source_sha256": self.data["instance_sha256"],
                "decimals": f.get("decimals"), "method": method}

def reporting_tolerance(question, output_unit, bindings, evidence):
    """No candidate input: disclosed/question precision only, otherwise abstain."""
    from verifiqa.answer_spec import answer_spec_from_question
    spec = answer_spec_from_question(question)
    if spec.precision_digits is not None:
        return str(Decimal(".5")*(Decimal(10)**-spec.precision_digits)), "question_precision"
    if re.search(r"nearest\s+(?:million|billion|thousand|dollar)", question, re.I):
        return ".5", "question_reporting_unit"
    if len(bindings) == 1:
        b = bindings[0]
        d = b.get("decimals")
        if d == "INF": return "0", "filing_exact"
        if d is not None and re.fullmatch(r"[+-]?\d+", str(d)):
            currency, scale = unit(output_unit)
            return str(Decimal(".5")*Decimal(10)**-int(d)/scale), "filing_fact_decimals"
    # For derived monetary subtotals the disclosure's display scale is authoritative.
    kind, scale = unit(output_unit)
    if kind not in {"pure", "shares"}:
        labels = re.findall(r"(?:in|amounts in|\()\s*(?:USD\s+|U\.S\.\s+|\$\s*)?(millions|thousands|billions)\b", evidence, re.I)
        scales = {unit("USD "+x.rstrip("s"))[1] for x in labels}
        if len(scales) == 1:
            return str(Decimal(".5")*next(iter(scales))/scale), "filing_display_scale"
    if kind == 'pure':
        # Paper does not specify how to choose a reporting precision for an
        # unreported derived ratio. Freeze two decimals, never infer from candidate.
        return '.005', 'reproduction_assumption_derived_ratio_two_decimals'
    raise Unresolved("reporting_precision_not_established")

def validate_dimensions(formula, bindings, output_unit):
    def dimension(label):
        kind,_=unit(label)
        if kind=='pure': return {}
        if '/' in kind:
            a,b=kind.split('/',1);return {a:1,b:-1}
        return {kind:1}
    dims={b['role']:dimension(b['unit']) for b in bindings}
    def walk(n):
        if isinstance(n,ast.Name): return dims[n.id]
        if isinstance(n,ast.Constant): return {}
        if isinstance(n,ast.UnaryOp): return walk(n.operand)
        if isinstance(n,ast.BinOp):
            a,b=walk(n.left),walk(n.right)
            if isinstance(n.op,(ast.Add,ast.Sub)):
                if a!=b: raise Unresolved('incompatible_operand_dimensions')
                return a
            if isinstance(n.op,(ast.Mult,ast.Div)):
                out=dict(a)
                for k,v in b.items():out[k]=out.get(k,0)+(v if isinstance(n.op,ast.Mult) else -v)
                return {k:v for k,v in out.items() if v}
            if isinstance(n.op,ast.Pow) and isinstance(n.right,ast.Constant) and type(n.right.value) is int:
                return {k:v*n.right.value for k,v in a.items() if v*n.right.value}
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in {'cagr','cagr_percent','coverage_ratio'}:
            args=[walk(x) for x in n.args]
            if len(args)>=2 and args[0]==args[1]:return {}
            raise Unresolved('incompatible_ratio_dimensions')
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in {'abs','min','max'}:
            args=[walk(x) for x in n.args]
            if args and all(a==args[0] for a in args):return args[0]
        raise Unresolved('unsupported_dimension_expression')
    if walk(ast.parse(formula,mode='eval').body)!=dimension(output_unit):
        raise Unresolved('formula_output_dimension_mismatch')
