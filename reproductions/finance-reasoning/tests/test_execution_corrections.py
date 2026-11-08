"""Regressions for legal PoT syntax and value-preserving number formatting."""
import pytest

from fr_repro.execution import execute


@pytest.mark.parametrize("code,expected", [
    ("def solution():\n    total = 0\n    for _ in range(4):\n        total += 3\n    return total", 12),
    ("def solution():\n    def _discount(amount):\n        return amount / 2\n    return _discount(10)", 5),
    ("def solution():\n    from datetime import datetime\n    return (datetime.strptime('2023-09-12', '%Y-%m-%d') - datetime.strptime('2023-03-15', '%Y-%m-%d')).days", 181),
    ("def solution():\n    return f'{1.235:.2f}'", 1.24),
    ("def solution():\n    return '-1.25e2'", -125),
    ("def solution():\n    return '  -125.50  '", -125.5),
])
def test_legal_constructs_and_canonical_scalar_formatting(code, expected):
    result = execute(code)
    assert result["status"] == "ok", result
    assert result["answer"] == expected


@pytest.mark.parametrize("text", ["5%", "$5", "5 and 6", "5+6", "NaN", "1e99999"])
def test_no_semantic_repair_or_expression_evaluation(text):
    result = execute(f"def solution():\n    return {text!r}")
    assert result["status"] == "execution_error" and result["answer"] is None
