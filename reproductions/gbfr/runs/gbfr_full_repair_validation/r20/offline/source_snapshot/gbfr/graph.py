"""Explicit formula operands, a validated DAG, and symbolic one-hop inverses.

No language model is allowed to invent a formula or a dependency edge.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
import json
from pathlib import Path
import re

import sympy as sp

from .types import AssetError, Constraints, Goal


def norm(name: str) -> str:
    return " ".join(name.casefold().split())


@dataclass
class Operand:
    symbol: str
    metric: str
    constraints: dict = field(default_factory=dict)


@dataclass
class Formula:
    id: str
    target: str
    expression: str  # RHS in named symbols, e.g. (a+b)/2
    operands: list[Operand]
    source_formula: str
    meta: dict = field(default_factory=dict)
    direction: str = "down"

    def symbolic(self):
        """AST to SymPy without sympify/eval on untrusted source text."""
        symbols = {o.symbol: sp.Symbol(o.symbol, real=True) for o in self.operands}

        def convert(n):
            if isinstance(n, ast.Name) and n.id in symbols:
                return symbols[n.id]
            if isinstance(n, ast.Constant) and type(n.value) in (int, float):
                return sp.Rational(str(n.value))
            if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
                v = convert(n.operand)
                return -v if isinstance(n.op, ast.USub) else v
            if isinstance(n, ast.BinOp):
                a, b = convert(n.left), convert(n.right)
                ops = {ast.Add: lambda: a+b, ast.Sub: lambda: a-b,
                       ast.Mult: lambda: a*b, ast.Div: lambda: a/b,
                       ast.Pow: lambda: a**b}
                if type(n.op) in ops:
                    return ops[type(n.op)]()
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and not n.keywords:
                functions = {"sqrt": sp.sqrt, "log": sp.log, "ln": sp.log, "exp": sp.exp,
                             "abs": sp.Abs, "min": sp.Min, "max": sp.Max,
                             "log10": lambda x: sp.log(x, 10)}
                if n.func.id in functions:
                    return functions[n.func.id](*(convert(arg) for arg in n.args))
            raise AssetError(f"Unsupported symbolic expression in {self.id}")

        try:
            tree = ast.parse(self.expression, mode="eval").body
            # Preserve syntactically used operands even when symbolic algebra
            # cancels one (e.g. A - (A - B)). Do not reject a valid source formula
            # merely because SymPy simplified its free-symbol set.
            used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id in symbols}
            if used != set(symbols):
                raise AssetError(f"Unused operands in source expression: {self.id}")
            result = convert(tree)
        except (SyntaxError, RecursionError) as exc:
            raise AssetError(f"Invalid expression in {self.id}") from exc
        if not set(result.free_symbols) <= set(symbols.values()):
            raise AssetError(f"Missing operands in {self.id}")
        return result, symbols


@dataclass
class Metric:
    name: str
    aliases: list[str]
    definition: str
    kind: str
    formulas: list[Formula]
    primary_aliases: list[str] = field(default_factory=list)


class MetricGraph:
    def __init__(self, nodes: list[Metric], provenance: dict | None = None):
        self.nodes = {n.name: n for n in nodes}
        self.provenance = provenance or {}
        if len(self.nodes) != len(nodes):
            raise AssetError("Duplicate canonical nodes; expert disambiguation is required")
        self.aliases: dict[str, set[str]] = {}
        self.primary_names: dict[str, set[str]] = {}
        self.parents: dict[str, list[tuple[str, Formula]]] = {}
        self._inverse_cache: dict[str, list[Formula]] = {}
        self._inverse_one_cache={}
        self._inverse_tasks={}
        self._symbolic_semaphore=None
        self.inverse_failures={}
        formula_ids = set()
        for n in nodes:
            if n.kind not in {"atomic", "derived"} or (n.kind == "atomic") != (not n.formulas):
                raise AssetError(f"Invalid atomic/derived partition: {n.name}")
            for alias in [n.name, *n.aliases]:
                self.aliases.setdefault(norm(alias), set()).add(n.name)
            for alias in [n.name, *n.primary_aliases]:
                self.primary_names.setdefault(norm(alias),set()).add(n.name)
            for f in n.formulas:
                if f.target != n.name or f.id in formula_ids:
                    raise AssetError(f"Invalid target/duplicate formula id: {f.id}")
                formula_ids.add(f.id)
                if len({o.symbol for o in f.operands}) != len(f.operands):
                    raise AssetError(f"Duplicate operand symbols: {f.id}")
                if len({o.metric for o in f.operands}) != len(f.operands):
                    raise AssetError(f"Formula needs distinct metric/role names for compute(vars): {f.id}")
                f.symbolic()
                for o in f.operands:
                    if o.metric not in self.nodes:
                        raise AssetError(f"Missing dependency {o.metric} in {f.id}")
                    self.parents.setdefault(o.metric, []).append((n.name, f))
        self._validate_dag()

    @classmethod
    def load(cls, path: str | Path) -> MetricGraph:
        obj = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.load_object(obj)

    @classmethod
    def load_object(cls, obj: dict) -> MetricGraph:
        if obj.get("schema_version") != 1:
            raise AssetError("Expected curated graph schema_version=1; raw upstream JSON is not a DAG")
        nodes = []
        for n in obj["nodes"]:
            fs = [Formula(
                id=f["id"], target=n["name"], expression=f["expression"],
                operands=[Operand(**o) for o in f["operands"]],
                source_formula=f["source_formula"], meta=f.get("meta", {}),
            ) for f in n.get("formulas", [])]
            nodes.append(Metric(n["name"], n.get("aliases", []), n.get("definition", ""), n["kind"], fs,n.get('primary_aliases',[])))
        return cls(nodes, obj.get("provenance"))

    def _validate_dag(self):
        visiting, done = set(), set()

        def visit(name, trail):
            if name in visiting:
                raise AssetError("Canonical FMKG contains a cycle: " + " -> ".join([*trail, name]))
            if name in done:
                return
            visiting.add(name)
            for f in self.nodes[name].formulas:
                for o in f.operands:
                    visit(o.metric, [*trail, name])
            visiting.remove(name)
            done.add(name)
        for name in self.nodes:
            visit(name, [])

    def find(self, name: str) -> Metric | None:
        if name in self.nodes:
            return self.nodes[name]
        primary=self.primary_names.get(norm(name),set())
        if primary:
            return self.nodes[next(iter(primary))] if len(primary)==1 else None
        matches = self.aliases.get(norm(name), set())
        return self.nodes[next(iter(matches))] if len(matches) == 1 else None

    def stats(self) -> dict:
        edges = {(n.name, o.metric) for n in self.nodes.values()
                 for f in n.formulas for o in f.operands}
        return {"nodes": len(self.nodes), "atomic": sum(n.kind == "atomic" for n in self.nodes.values()),
                "derived": sum(n.kind == "derived" for n in self.nodes.values()), "edges": len(edges)}

    def inverse_parents(self, name):
        result=[]
        for parent,f in self.parents.get(name,[]):
            matches=[o for o in f.operands if o.metric==name]
            if len(matches)==1 and not (set(matches[0].constraints)-{'meta'}):result.append((parent,f))
        return result

    def inverses(self, name: str) -> list[Formula]:
        """Immediate, uniquely rearrangeable inverses; no unbounded solver."""
        result=[]
        for parent,f in self.inverse_parents(name):
            k=(name,f.id)
            if k not in self._inverse_one_cache:
                inverse=make_inverse(parent,f,name,general=False)
                if inverse is not None:self._inverse_one_cache[k]=inverse
            inverse=self._inverse_one_cache.get(k)
            if inverse is not None:result.append(inverse)
        return result

    async def inverses_for(self,name,parent_names,timeout=3):
        """General symbolic solving runs only for a directly grounded parent."""
        import asyncio
        eligible=[(p,f) for p,f in self.inverse_parents(name) if p in parent_names]
        async def one(parent,f):
            k=(name,f.id)
            if k not in self._inverse_one_cache:
                quick=make_inverse(parent,f,name,general=False)
                if quick is not None:self._inverse_one_cache[k]=quick
                else:
                    task=self._inverse_tasks.get(k)
                    if task is None or task.cancelled():
                        task=asyncio.create_task(self._general_inverse(parent,f,name,timeout))
                        self._inverse_tasks[k]=task
                    self._inverse_one_cache[k]=await asyncio.shield(task)
            return self._inverse_one_cache[k]
        return [f for f in await asyncio.gather(*(one(p,f) for p,f in eligible)) if f is not None]

    async def _general_inverse(self,parent,formula,name,timeout):
        import asyncio,sys
        from dataclasses import asdict
        from .types import dumps
        if self._symbolic_semaphore is None:self._symbolic_semaphore=asyncio.Semaphore(2)
        async with self._symbolic_semaphore:
            proc=await asyncio.create_subprocess_exec(sys.executable,'-I',str(Path(__file__).with_name('symbolic_worker.py')),
                stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
            try:
                stdout,_=await asyncio.wait_for(proc.communicate(dumps({'parent':parent,'formula':asdict(formula),'name':name}).encode('utf-8')),timeout)
                if proc.returncode:return None
                obj=json.loads(stdout)
                if not obj.get('formula'):return None
                f=obj['formula'];f['operands']=[Operand(**o) for o in f['operands']]
                inverse=Formula(**f);inverse.symbolic()
                return inverse
            except asyncio.TimeoutError:
                proc.kill();await proc.wait()
                self.inverse_failures[(name,formula.id)]='symbolic_solver_deadline'
                return None
            except asyncio.CancelledError:
                proc.kill();await proc.wait();raise
            except (ValueError,AssetError):return None



def formula_literal(formula: Formula,metric: str) -> float | None:
    """Recognize an explicit mathematical literal, not an unstated data value.

    The public graph sometimes represents the factor 100 in a percentage
    formula as an operand named '100'. Only bind it when that same literal
    occurs on the formula's RHS. Query amounts and other metrics still use OES.
    """
    import math
    if not re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?',metric):return None
    rhs=formula.source_formula.split('=',1)[-1]
    if not re.search(r'(?<![\w.])'+re.escape(metric)+r'(?![\w.])',rhs):return None
    value=float(metric)
    if not math.isfinite(value):raise AssetError('Non-finite formula literal')
    return value


def operand_goal(operand: Operand, parent: Constraints) -> Goal:
    """Default: Algorithm 1 inherits C. Curated roles may bind a relative year.

    Example: temporal_scope='$year-1' implements beginning equity from the prior
    year end. No model-generated change of entity/time is accepted here.
    """
    from dataclasses import asdict
    obj = asdict(parent)
    patch = dict(operand.constraints)
    temporal = patch.get("temporal_scope")
    if isinstance(temporal, str) and temporal.startswith("$year"):
        year = str(parent.temporal_scope)
        years = list(re.finditer(r'(?<!\d)(?:19|20)\d{2}(?!\d)', year))
        annual_scope = re.fullmatch(r'(?:FY\s*|fiscal year\s*|year\s*|年度\s*|财年\s*)?(?:19|20)\d{2}(?:\s*(?:fiscal year|年度|财年))?', year, re.I)
        annual_scope=annual_scope or (re.search(r'\b(?:year ended|fiscal year|annual|year[- ]end)\b|年度|财年',year,re.I)
            and not re.search(r'\b(?:quarter|three months|six months|nine months)\b|季度',year,re.I))
        if not annual_scope or len(years) != 1 or not re.fullmatch(r"\$year(?:[+-]\d+)?", temporal):
            raise AssetError("A relative-year operand requires an unambiguous four-digit parent year")
        match = years[0]
        patch["temporal_scope"] = year[:match.start()] + str(int(match[0]) + int(temporal[5:] or '0')) + year[match.end():]
    if "meta" in patch:
        obj["meta"] = {**obj["meta"], **patch.pop("meta")}
    obj.update(patch)
    return Goal(operand.metric, Constraints.parse(obj))


def make_inverse(parent,formula,name,*,general=False):
    """Unique real rearrangement; general mode is confined to a worker."""
    matches=[o for o in formula.operands if o.metric==name]
    if len(matches)!=1 or set(matches[0].constraints)-{'meta'}:return None
    try:
        expr,symbols=formula.symbolic()
        target=symbols[matches[0].symbol];out=sp.Symbol('parent_value',real=True)
        linear=sp.solve_linear(out-expr,symbols=[target]) if expr.is_rational_function(target) else (None,None)
        if linear[0]==target:solution=linear[1]
        elif expr==sp.log(target):solution=sp.exp(out)
        elif expr==sp.exp(target):solution=sp.log(out)
        elif general:
            solutions=sp.solve(sp.Eq(out,expr),target)
            if len(solutions)!=1:return None
            solution=solutions[0]
        else:return None
        if solution.has(sp.I) or solution.has(sp.Piecewise):return None
        needed=solution.free_symbols
        operands=[Operand('parent_value',parent,{'meta':{'currency':None,'scale':None,'unit':None,**formula.meta}})] if out in needed else []
        operands += [o for o in formula.operands if o.metric!=name and symbols[o.symbol] in needed]
        text=sp.pycode(solution).replace('math.','')
        inverse=Formula(formula.id+':inverse:'+name,name,text,operands,
            f'Rearrange [{formula.source_formula}] to solve for {name}: {text}',direction='up')
        inverse.symbolic()
        return inverse
    except (RecursionError,NotImplementedError,ValueError,TypeError,ZeroDivisionError,AssetError):return None
