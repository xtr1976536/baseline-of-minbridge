import asyncio

import pytest

from gbfr.executor import execute, validate_program
from gbfr.types import ProtocolError


def test_executes_arithmetic_and_returns_trace():
    result = asyncio.run(execute('def compute(vars):\n    v = vars["a"] / vars["b"]\n    return {"value": v, "trace": {"a": vars["a"]}}', {"a": 10, "b": 4}))
    assert result == {"value": 2.5, "trace": {"a": 10}}


def test_isolated_worker_uses_utf8_for_chinese_code_keys_and_trace():
    code='def compute(vars):\n    return {"value": vars["流动资产"], "trace": {"单位": "元"}}'
    result=asyncio.run(execute(code,{'流动资产':42}))
    assert result=={'value':42,'trace':{'单位':'元'}}


def test_zero_division_propagates_none():
    assert asyncio.run(execute('def compute(vars):\n    return {"value": vars["a"] / vars["b"], "trace": {}}', {"a": 1, "b": 0})) is None


def test_explicit_zero_division_handler_matches_paper_program_contract():
    code='def compute(vars):\n    try:\n        return {"value": vars["a"] / vars["b"], "trace": {}}\n    except ZeroDivisionError:\n        return None'
    assert asyncio.run(execute(code,{'a':10,'b':2}))['value']==5
    assert asyncio.run(execute(code,{'a':10,'b':0})) is None
    for exception in ['Exception','ValueError','BaseException']:
        with pytest.raises(ProtocolError):
            validate_program(code.replace('ZeroDivisionError',exception))


def test_financial_log_exp_functions_without_imports():
    result = asyncio.run(execute('def compute(vars):\n    return {"value": exp(log(vars["a"])) + sqrt(4), "trace": {}}', {"a": 10}))
    assert result["value"] == pytest.approx(12)


def test_boolean_result_only_allowed_for_explicit_final_comparison():
    code = 'def compute(vars):\n    return {"value": vars["a"] > vars["b"], "trace": {}}'
    with pytest.raises(ProtocolError):
        asyncio.run(execute(code, {"a": 10, "b": 5}))
    result = asyncio.run(execute(code, {"a": 10, "b": 5}, allow_boolean_result=True))
    assert result["value"] == 1 and result["trace"]["boolean_value"] is True
    assert result["trace"]["output_meta"]["unit"] == "boolean"


@pytest.mark.parametrize("program", [
    'import os\ndef compute(vars):\n    return 1',
    'def compute(vars):\n    return open("secret")',
    'def compute(vars):\n    return vars.__class__',
    'def compute(vars):\n    return eval("1")',
    'def compute(vars):\n    while True:\n        pass',
    'def compute(vars):\n    def hidden():\n        return 1\n    return 1',
    'def compute(vars):\n    return __import__("os")',
])
def test_forbids_non_arithmetic_operations(program):
    with pytest.raises(ProtocolError):
        validate_program(program)


def test_bounded_range_and_runtime_errors_are_not_abstentions():
    with pytest.raises(ProtocolError):
        asyncio.run(execute('def compute(vars):\n    return {"value": sum(range(10001)), "trace": {}}', {}))


def test_process_timeout_is_error():
    with pytest.raises(ProtocolError):
        asyncio.run(execute('def compute(vars):\n    return {"value": sum(range(2)), "trace": {}}', {}, timeout=0.0001))
