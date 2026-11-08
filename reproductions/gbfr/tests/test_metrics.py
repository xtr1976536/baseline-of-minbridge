from decimal import Decimal

import pytest

from gbfr.metrics import correct, parse_number, precision_from_query, summarize


def sample(answer, question="Compute the value", negative=False):
    return {"id": "a", "question": question, "answer": answer, "unanswerable": negative}


def pred(value=None, *, status="answered", meta=None):
    return {"sample_id": "a", "value": value, "status": status, "meta": meta or {}}


def test_explicit_three_decimals_requires_exact_resolution():
    assert not correct(pred(.213), sample(.214, "Answer to three decimal places"))
    assert correct(pred(.2131), sample(.213, "Answer to three decimal places"))


def test_unspecified_precision_rounds_both_to_configured_resolution():
    assert correct(pred(.213), sample(.21))
    assert not correct(pred(.216), sample(.21))


def test_bare_output_uses_task_display_units_and_explicit_ratio_is_converted():
    assert correct(pred(.213, meta={"unit": "ratio"}), sample("21.3%", "Answer to one decimal place"))
    assert correct(pred(21.3, meta={"unit": "percentage"}), sample("21.3%", "Answer to one decimal place"))
    assert not correct(pred(.213), sample("21.3%", "Answer to one decimal place"))
    assert correct(pred(21.3), sample("21.3%", "Answer to one decimal place"))


def test_unscaled_dimensionless_annotation_preserves_identical_bare_scalar():
    assert correct(pred(2,meta={'unit':'ratio'}),sample(2))
    assert not correct(pred(.02,meta={'unit':'ratio'}),sample(2))
    assert not correct(pred(200,meta={'unit':'percentage'}),sample(2))
    assert not correct(pred(2,meta={'unit':'ratio'}),sample('$2'))


def test_explicit_base_currency_word_is_not_a_multiplicative_scale():
    from gbfr.metrics import canonical
    assert canonical(Decimal(42),{'currency':'CNY','scale':'yuan','unit':'monetary'})==(Decimal(42),('CNY',''))
    with pytest.raises(ValueError):
        canonical(Decimal(42),{'currency':'USD','scale':'yuan','unit':'monetary'})
    assert not correct(pred(42,meta={'currency':'CNY','scale':'yuan','unit':'monetary'}),sample('$42'))


def test_scale_normalization_and_incompatible_currency():
    assert correct(pred(1, meta={"scale": "millions", "currency": "USD"}), sample("$1000000"))
    assert not correct(pred(1, meta={"scale": "millions", "currency": "CNY"}), sample("$1000000"))


def test_error_is_not_an_abstention():
    s = sample(None, negative=True)
    assert correct(pred(status="abstained"), s)
    assert not correct(pred(status="error"), s)
    result = summarize([s], [pred(status="error")])
    assert result["abstention_accuracy"] == 0 and result["errors"] == 1 and not result["complete"]


def test_native_finance_reasoning_boolean_labels_preserved_as_comparisons():
    s = {**sample(True), "dataset": "FinanceReasoning", "answer_type": "boolean"}
    assert correct(pred(1, meta={"unit": "boolean"}), s)
    assert not correct(pred(0, meta={"unit": "boolean"}), s)
    assert not correct(pred(1, meta={"unit": "ratio"}), s)
    assert not correct(pred(status="abstained"), s)


def test_missing_predictions_are_in_denominator():
    result = summarize([sample(2)], [])
    assert result["missing"] == 1 and result["total_accuracy"] == 0


@pytest.mark.parametrize("text,expected", [("保留两位小数", 2), ("nearest integer", 0), ("nearest cent", 2),
                                           ("three decimal places", 3), ("保留3位", 3), ("no format", None)])
def test_precision(text, expected):
    assert precision_from_query(text) == expected


@pytest.mark.parametrize("text", [True, False, "yes", "2019, 2018", "income was 20 million", [1,2], "N/A"])
def test_excludes_nonnumeric_and_multiple_values(text):
    assert parse_number(text) is None


def test_financial_number_formats():
    assert parse_number("$ 1,234.50 million").value == Decimal("1234.50")
    assert parse_number("(100)").value == -100
    assert parse_number(".536%").value == Decimal(".536")
    assert parse_number("US$6 million").meta == {"currency": "USD", "scale": "million"}
    assert parse_number("Decreased $54.7 million").value == Decimal("-54.7")


def test_labelled_monetary_scalar_preserves_label_without_losing_units():
    number = parse_number("United States non-current assets of $182.4 million")
    assert number.value == Decimal("182.4")
    assert number.meta == {"currency": "USD", "scale": "million", "label": "United States non-current assets"}


@pytest.mark.parametrize("answer", [
    "a minimum ratio of 2.00 to 1.00 and capital expenditures of $100.0 million",
    "Revenue of $20 million and Cost of $10 million",
    "2019 non-current assets of $182.4 million",
])
def test_labelled_amount_does_not_extract_one_value_from_multi_field_answers(answer):
    assert parse_number(answer) is None
