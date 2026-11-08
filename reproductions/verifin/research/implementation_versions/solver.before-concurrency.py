"""Equation in §3.6, with exact rationals and separately checked domain guards."""
from __future__ import annotations
import ast
from decimal import Decimal
import re
import z3

class Unsupported(ValueError):
    pass

def number(value):
    d = Decimal(str(value))
    if not d.is_finite():
        raise Unsupported("non_finite_number")
    return z3.RealVal(format(d, "f"))

def expression(text, variables):
    guards = []
    def walk(n):
        if isinstance(n, ast.Name) and n.id in variables:
            return variables[n.id]
        if isinstance(n, ast.Constant) and type(n.value) in (int, float):
            return number(n.value)
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd)):
            v = walk(n.operand)
            return -v if isinstance(n.op, ast.USub) else v
        if isinstance(n, ast.BinOp):
            a, b = walk(n.left), walk(n.right)
            if isinstance(n.op, ast.Add): return a+b
            if isinstance(n.op, ast.Sub): return a-b
            if isinstance(n.op, ast.Mult): return a*b
            if isinstance(n.op, ast.Div):
                guards.append(b != 0)
                return a/b
            if isinstance(n.op, ast.Pow):
                # Fixed integer powers remain quantifier-free real arithmetic.
                if isinstance(n.right, ast.Constant) and type(n.right.value) is int and 0 <= n.right.value <= 20:
                    return a**n.right.value
                raise Unsupported("noninteger_or_variable_power")
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and not n.keywords:
            args = [walk(x) for x in n.args]
            if n.func.id in {'cagr','cagr_percent'} and len(args)==3:
                years_node=n.args[2]
                if not isinstance(years_node,ast.Constant) or type(years_node.value) is not int or not 1<=years_node.value<=20:
                    raise Unsupported('cagr_requires_fixed_positive_integer_years')
                end,start,_=args
                base=z3.Real('cagr_base_'+str(len(guards)))
                guards.extend([start>0,end>0,base>0,start*(base**years_node.value)==end])
                return (base-1)*(100 if n.func.id=='cagr_percent' else 1)
            if n.func.id=='coverage_ratio' and len(args)==2:
                a,b=args
                guards.append(z3.Implies(a>0,b!=0))
                return z3.If(a<=0,0,a/b)
            if n.func.id == "abs" and len(args) == 1:
                return z3.If(args[0] >= 0, args[0], -args[0])
            if n.func.id in {"min", "max"} and args:
                out = args[0]
                for a in args[1:]:
                    out = z3.If(out <= a, out, a) if n.func.id == "min" else z3.If(out >= a, out, a)
                return out
        raise Unsupported("unsupported_formula_syntax:"+type(n).__name__)
    try:
        out = walk(ast.parse(text, mode="eval").body)
    except SyntaxError as exc:
        raise Unsupported("invalid_formula") from exc
    return out, guards

def verify(formula, facts, claim, tolerance, *, timeout_ms=5000):
    if not facts or Decimal(str(tolerance)) < 0:
        raise Unsupported("empty_facts_or_invalid_tolerance")
    variables = {n: z3.Real("operand_"+str(i)) for i, n in enumerate(sorted(facts))}
    rhs, guards = expression(formula, variables)
    solver = z3.Solver()
    solver.set(timeout=timeout_ms)
    labels = {}
    def add(expr, label):
        safe = re.sub(r"[^A-Za-z0-9_]", "_", label)
        labels[safe] = label
        solver.assert_and_track(expr, safe)
    for name, symbol in variables.items():
        add(symbol == number(facts[name]), "filing_"+name)
    for i, guard in enumerate(guards):
        add(guard, "domain_"+str(i))
    # A missing domain (e.g. division by zero) is not evidence of a wrong claim.
    base = solver.check()
    if base != z3.sat:
        return {"status": "ABSTAIN", "reason": "undefined_formula_domain" if base == z3.unsat else "solver_unknown", "smtlib": solver.to_smt2()}
    expected = z3.Real("expected_value")
    add(expected == rhs, "authorized_formula")
    candidate, tau = number(claim), number(tolerance)
    add(expected-candidate <= tau, "claim_lower_bound")
    add(candidate-expected <= tau, "claim_upper_bound")
    result = solver.check()
    # Tracking literals must be asserted for standalone SMT replay.
    # Assert tracked Boolean literals in the standalone file so ordinary
    # `z3 file.smt2` checks the same obligation, not unassumed implications.
    smt = solver.sexpr()+'\n'+'\n'.join('(assert '+x+')' for x in labels)+"\n(check-sat)\n"
    if result == z3.sat:
        return {"status": "VERIFIED", "solver_status": "SAT", "expected": str(solver.model().eval(expected)), "smtlib": smt}
    if result == z3.unsat:
        return {"status": "VIOLATED", "solver_status": "UNSAT", "unsat_core": [labels[str(x)] for x in solver.unsat_core()], "smtlib": smt}
    return {"status": "ABSTAIN", "reason": "solver_unknown", "solver_reason": solver.reason_unknown(), "smtlib": smt}
