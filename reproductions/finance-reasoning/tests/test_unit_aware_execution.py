"""Gold-independent regression tests for standard maths and declared return units."""
import pytest

from fr_repro.execution import execute, percentage_output_requested
from fr_repro.metrics import correct


@pytest.mark.parametrize("question,expected", [
    ("Synthetic rate? Answer as a percentage to two decimal places.", True),
    ("Synthetic rate? Provide your answer as a percentage rounded to two decimal places.", True),
    ("What is the synthetic return (expressed as a percentage)?", True),
    ("Report the result in percent.", True),
    ("Answer as a percent with four decimal places.", True),
    ("What is the synthetic rate? Answer as a decimal to four decimal places.", False),
    ("Answer as a fraction.", False),
    ("A rate is expressed as a percentage. Answer as a decimal.", False),
    ("Answer as a decimal initially. Provide your answer as a percentage.", True),
    ("Answer as a percentage point difference.", False),
    ("A historical rate was given as a percentage. What is the cash value?", False),
    ("A historical rate is expressed as a percentage. What is the cash value?", False),
    ("A historical rate is expressed as a percentage; find the cash value.", False),
    ("Answer to two decimal places.", False),
])
def test_unit_contract_uses_explicit_question_instructions_only(question, expected):
    assert percentage_output_requested(question) is expected


@pytest.mark.parametrize("text,value", [("7.25%", 7.25), (" -2.50 % ", -2.5), ("0%", 0), ("1e2%", 100)])
def test_percentage_display_magnitude_is_preserved_without_rescaling(text, value):
    result = execute(f"def solution():\n    return {text!r}", percentage_output=True)
    assert result["status"] == "ok", result
    assert result["answer"] == value
    assert result["raw_return"] == text
    assert result["return_representation"] == "percentage_points"
    if value:
        assert not correct(result["answer"], value/100)


@pytest.mark.parametrize("text", ["7.25%", "-2.5%"])
def test_percentage_literal_is_rejected_without_an_explicit_percentage_request(text):
    result = execute(f"def solution():\n    return {text!r}", percentage_output=False)
    assert result["status"] == "execution_error" and result["answer"] is None


@pytest.mark.parametrize("text", ["7% or 8%", "USD 7%", "7%%", "%7", "NaN%", "1e99999%", "7% / 2"])
def test_ambiguous_units_multivalue_and_expressions_still_fail(text):
    result = execute(f"def solution():\n    return {text!r}", percentage_output=True)
    assert result["status"] == "execution_error" and result["answer"] is None


@pytest.mark.parametrize("program", [
    "def solution():\n    from statistics import NormalDist\n    return NormalDist().cdf(0)",
    "def solution():\n    import statistics\n    return statistics.NormalDist().cdf(0)",
])
def test_standard_library_normal_distribution_is_available(program):
    result = execute(program)
    assert result["status"] == "ok" and result["answer"] == .5


def test_native_numeric_results_are_never_rescaled_by_the_unit_flag():
    for value in [.0725, 7.25, True]:
        program = f"def solution():\n    return {value!r}"
        normal = execute(program, percentage_output=False)
        percent_requested = execute(program, percentage_output=True)
        assert normal == percent_requested
        assert normal["status"] == "ok" and normal["answer"] == value
        assert type(normal["answer"]) is type(value)
        assert "return_representation" not in normal
