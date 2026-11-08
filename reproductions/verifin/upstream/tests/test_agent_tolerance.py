import pytest

from verifiqa.agent.agent import _build_ir
from verifiqa.agent.types import ClaimSpec, GroundedFact
from verifiqa.answer_spec import answer_spec_from_question, effective_tolerance_from_answer


@pytest.mark.parametrize(
    ("question", "answer", "claimed_value", "expected_tolerance"),
    [
        (
            "what is the rate of return of an investment in nasdaq from 2017 to 2018?",
            "-3.6%",
            -3.6,
            0.05,
        ),
        (
            "what was the percentage change in the unrecognized tax benefits from 2015 to 2016?",
            "-1%",
            -1.0,
            0.5,
        ),
        (
            "what was the ratio of the free cash flow to the cash provided by operating activities in 2015",
            "0.07",
            0.07,
            0.005,
        ),
        (
            "what was the percent of the impairment charges to the net revenue in 2013",
            "0.5%",
            0.5,
            0.05,
        ),
        (
            "what was the percentage change in the unrecognized tax benefits from 2014 to 2015?",
            "-5%",
            -5.0,
            0.5,
        ),
    ],
)
def test_agent_uses_displayed_answer_precision_tolerance(
    question,
    answer,
    claimed_value,
    expected_tolerance,
):
    spec = answer_spec_from_question(question, answer)

    tolerance, precision_digits, tolerance_source = effective_tolerance_from_answer(
        spec,
        claimed_value,
        answer,
    )

    assert tolerance == pytest.approx(expected_tolerance)
    assert precision_digits is not None
    assert tolerance_source == "answer_precision"


def test_agent_build_ir_does_not_rescale_absolute_answer_tolerance():
    claim_spec = ClaimSpec(
        metric="impairment_percent",
        formula="impairment_charges / net_revenue * 100",
        roles=[],
        claim_unit="percent",
        tolerance=0.05,
        formula_source="generic_operation",
    )
    facts = {
        "impairment_charges": GroundedFact(
            "impairment_charges",
            240.0,
            "USD millions",
            "impairment charges 240",
        ),
        "net_revenue": GroundedFact(
            "net_revenue",
            52708.0,
            "USD millions",
            "net revenue 52708",
        ),
    }

    ir = _build_ir(
        claim_spec,
        facts,
        claimed_value=0.5,
        tolerance=0.05,
        precision_digits=1,
        tolerance_source="answer_precision",
    )

    assert ir.tolerance == pytest.approx(0.05)
    assert ir.precision_digits == 1
    assert ir.tolerance_source == "answer_precision"


def test_answer_spec_round_to_nearest_million_sets_half_million_tolerance():
    spec = answer_spec_from_question(
        "What was IBM's FY2025 income before income taxes, in USD millions? "
        "Round to the nearest million.",
        "10,328",
    )

    assert spec.expected_unit == "USD millions"
    assert spec.tolerance == pytest.approx(0.5)
    assert spec.tolerance_source == "default"
