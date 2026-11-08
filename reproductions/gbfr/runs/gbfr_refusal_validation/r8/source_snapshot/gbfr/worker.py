"""Subprocess arithmetic worker. Generated code was AST-validated by the parent.

This is a restricted executor, not an OS security sandbox for arbitrary software.
"""
import builtins
import json
import math
import sys


def bounded_range(*args):
    result = range(*args)
    if len(result) > 10000:
        raise ValueError("range exceeds 10000 elements")
    return result


def main():
    # The parent sends UTF-8 JSON even when Windows' isolated Python defaults
    # stdin to a legacy code page. Read bytes explicitly, including Chinese keys.
    request = json.loads(sys.stdin.buffer.read().decode('utf-8'))
    names = ["abs", "min", "max", "sum", "len", "round", "enumerate", "zip", "float", "int", "bool", "sorted", "pow","all","any","next"]
    scope = {"__builtins__": {n: getattr(builtins, n) for n in names}}
    scope["__builtins__"]["range"] = bounded_range
    scope['__builtins__']['ZeroDivisionError']=ZeroDivisionError
    scope['math']=math
    for name in ["sqrt", "log", "log10", "exp"]:
        scope["__builtins__"][name] = getattr(math, name)
    scope["__builtins__"]["ln"] = math.log
    try:
        exec(compile(request["code"], "<gbfr-arithmetic>", "exec"), scope)
        result = scope["compute"](request["values"])
        print(json.dumps({"result": result}, allow_nan=False))
    except ZeroDivisionError:
        print(json.dumps({"result": None}))
    except (ValueError,OverflowError) as exc:
        if isinstance(exc,OverflowError) or str(exc) in {'math domain error','math range error'}:
            print(json.dumps({'result':None}))
        else:print(json.dumps({'error':type(exc).__name__}))
    except Exception as exc:
        print(json.dumps({"error": type(exc).__name__}))


if __name__ == "__main__":
    main()
