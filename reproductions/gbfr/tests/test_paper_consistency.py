from gbfr.paper_consistency import compatible_correct_counts, audit_main_table, audit_directed_degree_claims


def test_table4_finqa_abstention_denominator_cannot_generate_98_80_percent():
    assert compatible_correct_counts(98.80, 97) == []
    assert compatible_correct_counts(72.16, 97) == [70]


def test_audit_checks_only_the_main_gbfr_cells_and_never_changes_references():
    report = audit_main_table()
    assert len(report["cells"]) == 16
    assert report["inconsistent_cell_count"] == 4


def test_directed_degree_handshake_detects_missing_averaging_scope():
    report = audit_directed_degree_claims(7521, 20152, "1.6", "2.3")
    assert not report["consistent_under_stated_assumption"]
    assert report["required_at_one_decimal"] == "2.7"
    assert audit_directed_degree_claims(3, 2, "0.7", "0.7")["consistent_under_stated_assumption"]
