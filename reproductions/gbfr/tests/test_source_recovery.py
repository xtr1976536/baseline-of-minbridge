from gbfr.source_recovery import cf_gold_arithmetic_checks


def test_ros_proof_uses_wan_and_yi_consistently_and_matches_option_c():
    proof = cf_gold_arithmetic_checks()[0]
    assert proof["normalized_operands_CNY"] == {"net_income": "-2148000.0", "sales": "579900000.000"}
    assert proof["computed_at_requested_precision"] == "-0.0037"
    assert proof["matching_official_option"] == "C"
    assert proof["official_declared_correct_option"] == "B"


def test_currency_depreciation_uses_the_value_of_cny_as_the_comparison_basis():
    proof = cf_gold_arithmetic_checks()[1]
    assert proof["computed_at_two_decimals_percent"] == "4.08"
    assert proof["gbfr_released_label"] == "4.26%"
