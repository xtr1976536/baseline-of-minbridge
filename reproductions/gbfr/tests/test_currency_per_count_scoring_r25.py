import pytest

from gbfr.metrics import correct, unit_contract
from gbfr.units import normalize_meta, target_meta, unit_name


def sample(question, context="Currency figures are in U.S. dollars.", answer="2", answer_meta=None):
    return {"question": question, "context": context, "answer": answer,
            "answer_meta": answer_meta or {}, "unanswerable": False}


def prediction(value=2, currency="USD", scale="ones", unit="USD per transaction"):
    return {"status": "answered", "value": value,
            "meta": {"currency": currency, "scale": scale, "unit": unit}}


@pytest.mark.parametrize("raw,canonical", [
    ("USD per transaction", "currency/transaction"),
    ("dollars/transactions", "currency/transaction"),
    ("EUR per employee", "currency/employee"),
    ("currency per employees", "currency/employee"),
    ("GBP/item", "currency/item"),
    ("currency/items", "currency/item"),
    ("USD per unit", "currency/unit"),
])
def test_monetary_per_count_labels_have_canonical_denominators(raw, canonical):
    assert unit_name(raw) == canonical


def test_explicit_currency_inside_unit_is_preserved_and_cannot_conflict():
    assert normalize_meta({"unit": "EUR per employee"}) == {
        "currency": "EUR", "scale": None, "unit": "currency/employee"}
    with pytest.raises(ValueError, match="Currency conflicts with unit label"):
        normalize_meta({"currency": "USD", "unit": "EUR per employee"})


@pytest.mark.parametrize("question,unit", [
    ("What is the average payment volume per transaction?", "currency/transaction"),
    ("What is revenue per employee?", "currency/employee"),
    ("What is average cost per item?", "currency/item"),
    ("What is the price per unit?", "currency/unit"),
])
def test_independent_monetary_targets_use_explicit_source_currency(question, unit):
    s = sample(question)
    assert target_meta(s, {}) == {"currency": "USD", "scale": "ones", "unit": unit}
    assert correct(prediction(unit=unit), s)
    assert not correct(prediction(currency="GBP", unit=unit), s)
    assert not correct(prediction(scale="million", unit=unit), s)


def test_visa_style_input_scales_cancel_without_inheriting_cards_scale():
    s = sample("What is the average payment volume per transaction?",
               "| Payments Volume (billions) | Transactions (billions) | Cards (millions) |\n"
               "Currency figures are in u.s .\ndollars .", "44.9")
    p = prediction(2793 / 62.2)
    assert unit_contract(p, s)["status"] == "resolved"
    assert correct(p, s, precision_policy="fixed")
    assert correct(p, s, precision_policy="reference_display")
    assert not correct(prediction(2793 / 62.2, scale="billion"), s)
    assert not correct(prediction(2793 / 62.2 / 1000), s)


def test_attached_monetary_header_is_independent_currency_evidence():
    s = sample("What is revenue per employee?", "Revenue (EUR millions); Employees (thousands).")
    assert target_meta(s, {}) == {"currency": "EUR", "scale": "ones", "unit": "currency/employee"}
    assert correct(prediction(currency="EUR", unit="EUR per employee"), s)


@pytest.mark.parametrize("context", [
    "Currency figures are in U.S. dollars. Currency figures are in euros.",
    "Revenue was 20 million. Employees numbered100.",
    "An unrelated bond pays USD interest. Revenue is disclosed separately.",
])
def test_ambiguous_or_unrelated_source_currency_does_not_establish_contract(context):
    s = sample("What is revenue per employee?", context)
    assert target_meta(s, {})["unit"] != "currency/employee"
    assert unit_contract(prediction(unit="USD per employee"), s)["status"] == "unresolved"


def test_currency_codes_are_not_substrings_of_geographical_names():
    s = sample("What is revenue per employee in Europe?", "Revenue and employees were reported.")
    assert target_meta(s, {})["currency"] is None
    assert unit_contract(prediction(unit="USD per employee"), s)["status"] == "unresolved"


@pytest.mark.parametrize("question", [
    "What is average time per transaction?", "What is average physical volume per unit?",
    "What is transaction count per employee?", "What was the value using revenue per employee?",
])
def test_nonmonetary_or_input_per_count_phrases_are_not_monetary_targets(question):
    assert target_meta(sample(question), {})["unit"] not in {
        "currency/transaction", "currency/employee", "currency/item", "currency/unit"}


def test_percentage_ratio_count_and_share_price_keep_their_dimensions():
    assert target_meta(sample("What percentage of revenue per employee changed?"), {})["unit"] == "percentage"
    assert target_meta(sample("What is the ratio of revenue per employee across departments?"), {})["unit"] == "ratio"
    assert target_meta(sample("How many years had revenue per employee above the threshold?"), {})["unit"] == "count"
    assert target_meta(sample("What was the price per share?"), {})["unit"] == "currency/share"


def test_input_scale_is_not_the_per_count_output_scale():
    s = sample("Given revenue in millions, what is revenue per employee?")
    assert target_meta(s, {})["scale"] == "ones"
    assert correct(prediction(unit="USD per employee"), s)
    assert not correct(prediction(scale="million", unit="USD per employee"), s)


@pytest.mark.parametrize("question", [
    "What is revenue per employee in thousands?",
    "In thousands, what is revenue per employee?",
    "What is the amount (thousands) per employee?",
])
def test_explicit_output_scale_is_preserved(question):
    s = sample(question)
    assert target_meta(s, {})["scale"] == "thousand"
    assert correct(prediction(2000, unit="USD per employee"), s)
    assert not correct(prediction(2, unit="USD per employee"), s)


def test_official_display_scale_is_preserved_without_query_override():
    s = sample("What is revenue per employee?", answer_meta={"scale": "thousand"})
    assert target_meta(s, {})["scale"] == "thousand"
    assert correct(prediction(2000, unit="USD per employee"), s)


def test_contract_does_not_depend_on_reference_value_or_prediction():
    q = "What is cost per item?"
    assert target_meta(sample(q, answer="2"), {}) == target_meta(sample(q, answer="9000000"), {})
    assert not correct(prediction(unit="USD per transaction"), sample(q))
