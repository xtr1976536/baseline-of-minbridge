"""Parse one PoT completion and execute its solution in a restricted subprocess.

This is a limited math executor, not an operating-system security sandbox.
No generated-code repair, numerical fallback, or second inference attempt.
"""
from __future__ import annotations

import ast
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def extract_program(output):
    if len(output) > 100000:
        raise ValueError("Program exceeds the size limit")
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", output, flags=re.S)
    code = blocks[0] if blocks else output.split("```", 1)[0]
    if code.startswith("python\n"):
        code = code[7:]
    # The original PoT prompt ends inside solution(). Supporting a continued
    # function body is a syntax adapter, without changing its calculations.
    if not re.search(r"^def solution\s*\(", code, flags=re.M):
        lines = code.splitlines()
        while lines and not lines[0].strip():
            lines.pop(0)
        if lines and lines[0].startswith((" ", "\t")):
            code = "def solution():\n" + "\n".join(lines)
        elif lines:
            code = "def solution():\n" + "\n".join("    " + line for line in lines)
    tree = ast.parse(code)
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "solution"]
    if len(functions) != 1 or functions[0].args.args or functions[0].args.vararg or functions[0].args.kwarg:
        raise ValueError("Expected exactly one zero-argument solution()")
    validate_program(tree)
    return code


IMPORTS = {"math", "decimal", "statistics", "fractions", "datetime", "collections", "numpy", "numpy.linalg", "numpy_financial", "sympy", "scipy", "scipy.optimize", "scipy.stats", "scipy.signal"}
ATTRIBUTES = set("""
abs absolute arange array asarray average ceil clip concatenate cos cov cumprod cumsum diag dot exp expm1
floor full geomspace isclose isfinite linspace log log10 log1p log2 max mean median min multiply ones
percentile pi polyfit polynomial polyval power prod quantile reshape round sin sort sqrt square std sum tan
transpose var where zeros linalg solve inv norm eigvals item tolist shape size T real imag flatten
pv fv pmt ppmt ipmt nper rate npv irr mirr
acos asin atan atan2 cosh sinh tanh degrees radians factorial fmod fsum hypot trunc e inf nan
copysign fabs isinf isnan pow gcd lcm comb perm prod
Decimal ROUND_HALF_UP ROUND_HALF_EVEN ROUND_DOWN ROUND_UP getcontext localcontext prec rounding quantize
to_integral_value to_integral_exact normalize scaleb Fraction numerator denominator limit_denominator
mean median mode stdev pstdev variance pvariance harmonic_mean geometric_mean NormalDist
symbols Symbol Eq solve nsolve diff integrate Rational Integer Float simplify S N re im
optimize newton brentq bisect root fsolve minimize minimize_scalar success x fun
append extend insert pop remove count index reverse clear copy keys values items get setdefault update
format join split strip replace lower upper startswith endswith
erf erfc gamma lgamma remainder ulp nextafter frexp ldexp isqrt dist
all any hstack vstack column_stack stack ndarray roots linspace logical_and logical_or
stats norm cdf ppf pdf sf isf logcdf logpdf lognorm expon t chi2 poisson binom
signal find_peaks
datetime date timedelta strptime fromisoformat days seconds total_seconds year month day
Counter defaultdict most_common
""".split())
FORBIDDEN_NAMES = {"eval", "exec", "compile", "open", "input", "globals", "locals", "vars", "dir", "getattr", "setattr", "delattr", "help", "breakpoint", "exit", "quit", "type", "object", "super", "memoryview"}


def validate_program(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.AsyncFunctionDef, ast.Await, ast.Global, ast.Nonlocal, ast.With, ast.AsyncWith)):
            raise ValueError("Unsupported program construct")
        if isinstance(node, ast.Name) and (node.id.startswith("__") or node.id in FORBIDDEN_NAMES):
            raise ValueError("Unsupported program name")
        if isinstance(node, ast.Attribute) and (node.attr.startswith("_") or node.attr not in ATTRIBUTES):
            raise ValueError(f"Unsupported attribute: {node.attr}")
        if isinstance(node, ast.Import):
            if any(a.name not in IMPORTS for a in node.names):
                raise ValueError("Unsupported import")
        if isinstance(node, ast.ImportFrom):
            if node.level or node.module not in IMPORTS or any(a.name.startswith("_") or a.name not in ATTRIBUTES for a in node.names):
                raise ValueError("Unsupported from-import")
        if isinstance(node, ast.FunctionDef) and (node.decorator_list or node.name.startswith("__")):
            raise ValueError("Unsupported function decorator/name")


def percentage_output_requested(question):
    """Honor explicit output-unit clauses in the original question, never gold.

    The last explicit answer/result/expressed-as unit wins. Decimal-place
    precision is not itself a request for decimal/fraction units.
    """
    pattern = r"\b(?:(?P<direct>answer|result)\s+(?:as|in|with)|(?P<expressed>expressed)\s+as)\s+(?:a\s+)?(?P<unit>percentage|percent|decimal|fraction)\b(?P<points>\s+points?\b)?"
    matches = [match for match in re.finditer(pattern, question, flags=re.I)
               if match.group("direct") or re.fullmatch(r"[\s)\]}.!?]*", question[match.end():])]
    if not matches:
        return False
    last = matches[-1]
    return last.group("unit").lower() in {"percentage", "percent"} and last.group("points") is None


def execute(output, timeout=10, *, percentage_output=False):
    try:
        code = extract_program(output)
    except (ValueError, SyntaxError) as exc:
        return {"status": "invalid_program", "answer": None, "error": str(exc)}
    env = {k: v for k, v in os.environ.items() if k.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "COMSPEC"}}
    env.update({"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"})
    try:
        result = subprocess.run([sys.executable, "-I", str(Path(__file__).with_name("worker.py"))],
                                input=json.dumps({"code": code, "percentage_output": percentage_output}), capture_output=True, text=True,
                                encoding="utf-8", timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return {"status": "execution_error", "answer": None, "code": code, "error": "Execution timed out"}
    try:
        response = json.loads(result.stdout)
        return {**response, "code": code}
    except (ValueError, TypeError):
        return {"status": "execution_error", "answer": None, "code": code, "error": "Worker failed"}
