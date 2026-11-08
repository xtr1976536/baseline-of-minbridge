"""Restricted arithmetic Python in a time-limited isolated Python subprocess."""
from __future__ import annotations

import ast
import asyncio
import json
import io
import keyword
from pathlib import Path
import re
import sys
import tokenize

from .types import ProtocolError, dumps, finite


ALLOWED_CALLS = {"abs", "min", "max", "sum", "len", "round", "range", "enumerate", "zip", "float", "int", "bool", "sorted",
                 "sqrt", "log", "ln", "log10", "exp", "pow","all","any","next"}
SAFE_METHODS={'get','keys','values','items','copy','append','extend','count','index'}
SAFE_MATH={'sqrt','log','log10','log2','exp','pow','fabs','ceil','floor','trunc','isfinite','isclose','pi','e'}
ALLOWED_NODES = {
    ast.Module, ast.FunctionDef, ast.arguments, ast.arg, ast.Return, ast.Assign,
    ast.AugAssign, ast.If, ast.IfExp, ast.For, ast.Break, ast.Continue, ast.Pass,
    ast.Expr, ast.Name, ast.Load, ast.Store, ast.Constant, ast.Subscript, ast.Slice,
    ast.Dict, ast.List, ast.Tuple, ast.Set, ast.BinOp, ast.UnaryOp, ast.BoolOp,
    ast.Compare, ast.Call, ast.keyword, ast.ListComp, ast.GeneratorExp, ast.comprehension,
    ast.Try, ast.ExceptHandler,
    ast.Attribute,ast.JoinedStr,ast.FormattedValue,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
    ast.USub, ast.UAdd, ast.Not, ast.And, ast.Or, ast.Eq, ast.NotEq,
    ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.In, ast.NotIn, ast.Is, ast.IsNot,
}


def clean_program(text: str) -> str:
    return re.sub(r"^```(?:python)?\s*\n?(.*?)\n?```$", r"\1", text.strip(), flags=re.S)


def joined_identifiers(text):
    """Repair a consistently split assignment identifier, never arithmetic.

    Only invalid Python is considered. The assignment target must be a split
    underscore-containing name, and joining it must not collide with a name
    already present. Matching NAME tokens are joined outside strings/comments;
    all numbers, operators and input keys remain untouched.
    """
    try:ast.parse(text);return text,{}
    except SyntaxError:pass
    try:ts=list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError,IndentationError):return text,{}
    existing={t.string for t in ts if t.type==tokenize.NAME}
    candidates={}
    for line in text.splitlines():
        m=re.match(r'^\s*([A-Za-z_]\w*(?:[ \t]+[A-Za-z_]\w*)+)[ \t]*=(?!=)',line)
        if not m:continue
        words=tuple(m[1].split());name=''.join(words)
        if '_' not in words[0] or any(keyword.iskeyword(w) for w in words) or name in existing:continue
        candidates[words]=name
    if not candidates:return text,{}
    offsets=[0]
    for line in text.splitlines(keepends=True):offsets.append(offsets[-1]+len(line))
    edits=[];changes={};i=0
    while i<len(ts):
        for words,name in sorted(candidates.items(),key=lambda p:-len(p[0])):
            group=ts[i:i+len(words)]
            if len(group)!=len(words) or any(t.type!=tokenize.NAME or t.string!=w for t,w in zip(group,words)):continue
            if any(a.end[0]!=b.start[0] for a,b in zip(group,group[1:])):continue
            start=offsets[group[0].start[0]-1]+group[0].start[1]
            end=offsets[group[-1].end[0]-1]+group[-1].end[1]
            if not re.fullmatch(r'[A-Za-z_\w \t]+',text[start:end]):continue
            edits.append((start,end,name));changes[text[start:end]]=name;i+=len(words);break
        else:i+=1
    result=text
    for start,end,name in reversed(edits):result=result[:start]+name+result[end:]
    try:ast.parse(result)
    except SyntaxError:return text,{}
    return result,changes


def python_literals(text):
    """Translate only unbound JSON literal spellings, never variable values."""
    try:tree=ast.parse(text)
    except SyntaxError:return text,[]
    bound={n.id for n in ast.walk(tree) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store)}
    changes=[]
    class Literals(ast.NodeTransformer):
        def visit_Name(self,node):
            if isinstance(node.ctx,ast.Load) and node.id in {'null','true','false'} and node.id not in bound:
                changes.append(node.id)
                return ast.copy_location(ast.Constant({'null':None,'true':True,'false':False}[node.id]),node)
            return node
    tree=Literals().visit(tree)
    return (ast.unparse(ast.fix_missing_locations(tree)),sorted(set(changes))) if changes else (text,[])


def validate_program(text: str):
    if len(text) > 50000:
        raise ProtocolError("Generated program exceeds 50 KB")
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        raise ProtocolError("Invalid generated Python syntax") from exc
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
        raise ProtocolError("Only one compute(vars) function is permitted")
    fn = tree.body[0]
    if (fn.name != "compute" or len(fn.args.args) != 1 or fn.args.args[0].arg != "vars"
            or fn.decorator_list or fn.args.defaults or fn.args.kw_defaults
            or fn.args.vararg or fn.args.kwarg or fn.args.kwonlyargs or fn.args.posonlyargs
            or fn.returns or fn.args.args[0].annotation):
        raise ProtocolError("Expected plain def compute(vars)")
    for node in ast.walk(tree):
        if type(node) not in ALLOWED_NODES:
            raise ProtocolError(f"Forbidden Python syntax: {type(node).__name__}")
        if isinstance(node, ast.FunctionDef) and node is not fn:
            raise ProtocolError("Nested functions are forbidden")
        if isinstance(node,ast.Try):
            if (node.orelse or node.finalbody or len(node.handlers)!=1
                    or not isinstance(node.handlers[0].type,ast.Name)
                    or node.handlers[0].type.id!='ZeroDivisionError'
                    or node.handlers[0].name is not None
                    or len(node.handlers[0].body)!=1
                    or not isinstance(node.handlers[0].body[0],ast.Return)
                    or not isinstance(node.handlers[0].body[0].value,ast.Constant)
                    or node.handlers[0].body[0].value.value is not None):
                raise ProtocolError('Only except ZeroDivisionError: return None is permitted')
        if isinstance(node, ast.Name) and node.id.startswith("_"):
            raise ProtocolError("Private names are forbidden")
        if isinstance(node,ast.Attribute):
            math_attr=isinstance(node.value,ast.Name) and node.value.id=='math' and node.attr in SAFE_MATH
            if not math_attr and node.attr not in SAFE_METHODS:raise ProtocolError('Only safe numeric/dictionary attributes are permitted')
        if isinstance(node, ast.Call):
            builtin=isinstance(node.func,ast.Name) and node.func.id in ALLOWED_CALLS
            method=isinstance(node.func,ast.Attribute) and (node.func.attr in SAFE_METHODS or
                   isinstance(node.func.value,ast.Name) and node.func.value.id=='math' and node.func.attr in SAFE_MATH)
            if not builtin and not method:raise ProtocolError("Only arithmetic builtins and safe container methods may be called")
        if isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes)) and len(node.value) > 10000:
            raise ProtocolError("Oversized literal")


async def execute(text: str, values: dict[str, float], timeout: float = 5, *, allow_boolean_result: bool = False) -> dict | None:
    text = clean_program(text)
    text,identifier_changes=joined_identifiers(text)
    text,literal_changes=python_literals(text)
    validate_program(text)
    for value in values.values():
        finite(value)
    worker = Path(__file__).with_name("worker.py")
    process = await asyncio.create_subprocess_exec(
        sys.executable, "-I", "-S", str(worker),
        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(dumps({"code": text, "values": values}).encode()), timeout=timeout)
    except asyncio.CancelledError:
        process.kill()
        await process.wait()
        raise
    except asyncio.TimeoutError as exc:
        process.kill()
        await process.wait()
        raise ProtocolError("Generated program exceeded execution deadline") from exc
    if process.returncode != 0:
        raise ProtocolError("Arithmetic worker failed")
    obj = json.loads(stdout)
    if obj.get("error"):
        raise ProtocolError("Generated program failed: " + obj["error"])
    result = obj["result"]
    if result is None:
        return None
    if not isinstance(result, dict) or not {"value", "trace"} <= result.keys() or not isinstance(result["trace"], dict):
        raise ProtocolError("compute(vars) must return {value, trace} or None")
    if result["value"] is None:
        return None
    if isinstance(result["value"], bool) and allow_boolean_result:
        result["trace"]["boolean_value"] = result["value"]
        result["value"] = int(result["value"])
        meta = result["trace"].setdefault("output_meta", {})
        if not isinstance(meta, dict):
            raise ProtocolError("Invalid output_meta for comparison")
        meta.update(currency=None, scale=None, unit="boolean")
    else:
        if isinstance(result['value'],str):
            from .metrics import parse_number
            parsed=parse_number(result['value'])
            if parsed is None:raise ProtocolError('compute returned non-scalar text')
            result['value']=float(parsed.value)
            result['trace']['output_meta']={**parsed.meta,**result['trace'].get('output_meta',{})}
        result["value"] = finite(result["value"])
    protocol={}
    if literal_changes:protocol['json_literals_to_python']=literal_changes
    if identifier_changes:protocol.update(identifier_joins=identifier_changes,effective_program=text)
    if protocol:result['trace']['executor_protocol']={**result['trace'].get('executor_protocol',{}),**protocol}
    return result
