import pytest

from gbfr.metrics import correct, unit_contract
from gbfr.units import target_meta


def sample(answer=2, question="Compute the value", context="", answer_meta=None):
    return {"answer": answer, "question": question, "context": context,
            "answer_meta": answer_meta or {}, "unanswerable": False}


def prediction(value=2, **meta):
    return {"status": "answered", "value": value, "meta": meta}


@pytest.mark.parametrize("meta", [
    {"currency": "USD"}, {"currency": "GBP", "scale": "ones"},
    {"scale": "million"}, {"scale": "thousand", "unit": "shares"},
    {"unit": "currency/share"}, {"unit": "USD/share"},
    {"unit": "currency/warrant"}, {"unit": "currency/unit"},
])
def test_identical_raw_values_do_not_erase_explicit_prediction_units(meta):
    s, p = sample(), prediction(**meta)
    contract = unit_contract(p, s)
    assert contract["status"] == "unresolved"
    assert contract["target_meta"] == {"currency": None, "scale": None, "unit": None}
    assert not correct(p, s, precision_policy="fixed")
    assert not correct(p, s, precision_policy="reference_display")


@pytest.mark.parametrize("value", [0, 2, -2, 2_000_000_000])
def test_unresolved_contract_does_not_depend_on_magnitude_or_equality(value):
    s = sample(value)
    for amount in [value, value + 1]:
        p = prediction(amount, scale="million")
        assert unit_contract(p, s)["status"] == "unresolved"
        assert not correct(p, s)


@pytest.mark.parametrize("meta", [{}, {"scale": "ones"}, {"unit": "ratio"},
                                   {"unit": "count", "scale": "ones"}])
def test_native_unscaled_display_still_accepts_identical_scalar(meta):
    s, p = sample(), prediction(**meta)
    assert unit_contract(p, s)["status"] == "native_display"
    assert correct(p, s)
    assert not correct(prediction(0.02, **meta), s)


def test_native_display_does_not_search_for_a_ratio_factor():
    assert not correct(prediction(200, unit="percentage"), sample(2))
    assert correct(prediction(2, unit="ratio"), sample(2))


def test_known_reference_contract_still_converts_and_rejects_wrong_units():
    s = sample("$2000000")
    assert unit_contract(prediction(2, currency="USD", scale="million"), s)["status"] == "resolved"
    assert correct(prediction(2, currency="USD", scale="million"), s)
    assert not correct(prediction(2, currency="GBP", scale="million"), s)
    assert not correct(prediction(2_000_000, currency="USD", scale="million"), s)


def test_explicit_query_scale_is_target_evidence_without_size_heuristic():
    s = sample(2, "What was the amount in millions?")
    assert unit_contract(prediction(2000, scale="thousand"), s)["status"] == "resolved"
    assert correct(prediction(2000, scale="thousand"), s)
    assert not correct(prediction(2, scale="thousand"), s)


@pytest.mark.parametrize("noun,scale", [("amounts", "millions"), ("value", "thousands"),
                                       ("cost", "billions"), ("proceeds", "millions")])
def test_parenthesized_scale_binds_to_requested_output_quantity(noun, scale):
    s = sample(327, f"What were the total {noun} ( {scale} ) of the issuance?")
    p = prediction(327, currency="USD", scale=scale)
    assert unit_contract(p, s)["status"] == "resolved"
    assert correct(p, s)
    assert not correct(prediction(327, scale="ones"), s)


def test_actual_etr_parenthesized_target_scale_is_source_supported():
    s = sample(327, "relating to the texas securitization bonds , what were the total amounts "
               "( millions ) of the issuance when considering the transaction costs and the "
               "related deferred income tax benefits?")
    assert target_meta(s, {})["scale"] == "million"
    assert correct(prediction(327, currency="USD", scale="million"), s)
    assert not correct(prediction(327, currency="USD", scale="thousand"), s)


@pytest.mark.parametrize("question", [
    "Given the total amounts (millions), what was the result?",
    "What was the result using expenses (millions)?",
    "What was the result based on values (millions)?",
    "What was the result (millions)?",
])
def test_unbound_or_input_parenthesized_scale_does_not_supply_target_unit(question):
    s = sample(2, question)
    assert target_meta(s, {})["scale"] is None
    assert unit_contract(prediction(2, scale="million"), s)["status"] == "unresolved"


@pytest.mark.parametrize("question,expected_unit", [
    ("Given the amounts (millions), what percentage changed?", "percentage"),
    ("Given the amounts (millions), how many years exceeded the threshold?", "count"),
    ("Given the amounts (millions), what was the price per share?", "currency/share"),
    ("What percentage of amounts (millions) changed?", "percentage"),
])
def test_parenthesized_monetary_input_scale_does_not_change_output_dimension(question, expected_unit):
    meta = target_meta(sample(2, question), {})
    assert meta["scale"] is None
    assert meta["unit"] == expected_unit


def test_actual_amt_approximate_output_stays_incorrect_and_units_unresolved():
    s = sample("45984064", "was was the total amount spent on stock repurchases in the fourth quarter?",
               "Repurchased 619314 shares for approximately $46.0 million, including commissions and fees. "
               "The table's remaining authorization column is in millions. "
               "The program was authorized for $1.5 billion. "
               "Average price per share $74.25 excludes commissions and fees.")
    p = prediction(46, currency="USD", scale="million")
    assert unit_contract(p, s)["status"] == "unresolved"
    assert not correct(p, s, precision_policy="fixed")
    assert not correct(p, s, precision_policy="reference_display")
    # The old metadata-erasing path incorrectly accepted this identical raw
    # number even though its explicit million multiplier was unverified.
    assert not correct(prediction(45_984_064, currency="USD", scale="million"), s)


def test_diagnostics_do_not_reinterpret_nonanswers_or_invalid_metadata():
    assert unit_contract({"status": "abstained"}, sample())["status"] == "not_applicable"
    assert unit_contract(prediction(), {**sample(), "unanswerable": True})["status"] == "not_applicable"
    assert unit_contract(prediction(), sample("two"))["status"] == "not_numeric"
    assert unit_contract(prediction(scale="unsupported"), sample())["status"] == "invalid"


def test_diagnostic_does_not_mutate_prediction_or_reference():
    s, p = sample(), prediction(currency="USD", scale="million")
    unit_contract(p, s)
    assert p["meta"] == {"currency": "USD", "scale": "million"}
    assert s["answer_meta"] == {}
