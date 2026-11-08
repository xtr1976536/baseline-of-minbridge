from verifiqa.agent.agent import _parse_number


def test_parse_number_skips_company_and_fiscal_year_context():
    answer = "Operating Margin for 3M in FY2022 has decreased by 1.7% primarily due to charges"

    assert _parse_number(answer) == 1.7


def test_parse_number_skips_company_and_apostrophe_date_context():
    answer = "No. The quick ratio for 3M was 0.96 by Jun'23 close"

    assert _parse_number(answer) == 0.96


def test_parse_number_skips_standalone_year_context():
    answer = "In 2022, the margin decreased by 1.7%"

    assert _parse_number(answer) == 1.7


def test_parse_number_keeps_simple_finance_values():
    assert _parse_number("$1577.00") == 1577.0
    assert _parse_number("24.69%") == 24.69
    assert _parse_number(".2") == 0.2
    assert _parse_number("-52.5%") == -52.5
