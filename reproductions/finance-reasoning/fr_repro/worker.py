"""Math-only subprocess worker; environment credentials are not inherited."""
import builtins
import contextlib
from decimal import Decimal
import io
import json
import math
import numbers
import re
import sys

ALLOWED_IMPORTS = {"_strptime", "math", "decimal", "statistics", "fractions", "datetime", "collections", "numpy", "numpy.linalg", "numpy_financial", "sympy", "scipy", "scipy.optimize", "scipy.stats", "scipy.signal"}


def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
    if level or name not in ALLOWED_IMPORTS:
        raise ImportError("Import unavailable")
    return builtins.__import__(name, globals, locals, fromlist, level)


def main():
    payload = json.load(sys.stdin)
    allowed = "abs all any bool dict enumerate filter float int isinstance len list map max min next pow range reversed round set sorted str sum tuple zip Exception ValueError TypeError ZeroDivisionError print".split()
    safe_builtins = {name: getattr(builtins, name) for name in allowed}
    safe_builtins["__import__"] = restricted_import
    namespace = {"__builtins__": safe_builtins}
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(payload["code"], "<model_program>", "exec"), namespace)
            answer = namespace["solution"]()
        # Pure numerical formatting is a representation adapter, not a unit conversion.
        representation = {}
        if isinstance(answer, str):
            text = answer.strip()
            if text.endswith("%"):
                if payload.get("percentage_output") is not True:
                    raise ValueError("Percentage output was not explicitly requested")
                representation = {"raw_return": answer, "return_representation": "percentage_points"}
                text = text[:-1].strip()
            if not re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", text):
                raise ValueError("String result is not a single canonical number")
            answer = Decimal(text)
        # Accept native numerical scalars, Decimal and numpy scalar values.
        # Noncanonical strings, sequences, complex values and missing returns fail.
        if type(answer) is bool or (type(answer).__module__ == "numpy" and type(answer).__name__ == "bool"):
            answer = bool(answer)
        elif isinstance(answer, numbers.Real) or isinstance(answer, Decimal) or (type(answer).__module__.startswith("sympy") and getattr(answer, "is_real", False)):
            answer = float(answer) if not isinstance(answer, int) else answer
            if not math.isfinite(answer):
                raise ValueError("Non-finite program result")
        else:
            raise ValueError("Program did not return a single real number or boolean")
        result = {"status": "ok", "answer": answer, **representation}
    except Exception as exc:
        result = {"status": "execution_error", "answer": None, "error": type(exc).__name__}
    print(json.dumps(result, allow_nan=False))


if __name__ == "__main__":
    main()
