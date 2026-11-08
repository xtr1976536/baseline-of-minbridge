(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_liabilities_fy2025 Real)
(declare-const liabilities_current_fy2025 Real)
(declare-const long_term_debt_noncurrent_fy2025 Real)
(declare-const operating_lease_liability_noncurrent_fy2025 Real)
(declare-const other_liabilities_noncurrent_fy2025 Real)

(assert (! (= liabilities_current_fy2025 37118) :named evidence_liabilities_current_fy2025))
(assert (! (= long_term_debt_noncurrent_fy2025 10439) :named evidence_long_term_debt_noncurrent_fy2025))
(assert (! (= operating_lease_liability_noncurrent_fy2025 2189) :named evidence_operating_lease_liability_noncurrent_fy2025))
(assert (! (= other_liabilities_noncurrent_fy2025 3417) :named evidence_other_liabilities_noncurrent_fy2025))

(assert (! (= computed_liabilities_fy2025 (+ liabilities_current_fy2025 long_term_debt_noncurrent_fy2025 operating_lease_liability_noncurrent_fy2025 other_liabilities_noncurrent_fy2025)) :named formula_liabilities_fy2025))

(assert (! (<= (- computed_liabilities_fy2025 41755) 41.755000000000003) :named claim_upper))
(assert (! (<= (- 41755 computed_liabilities_fy2025) 41.755000000000003) :named claim_lower))

; EDGAR-companyfacts fact bindings (no calculation-linkbase constraints).
(declare-const xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LongTermDebtNoncurrent_instant_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingLeaseLiabilityNoncurrent_instant_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherLiabilitiesNoncurrent_instant_2026_01_31_unit_USD_dims_none Real)

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= liabilities_current_fy2025 xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2026_01_31_unit_USD_dims_none) :named xbrl_bind_liabilities_current_fy2025_edgar_2026_01_31_0001108524_26_000060))
(assert (! (= xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2026_01_31_unit_USD_dims_none 37118) :named xbrl_instance_liabilities_current_fy2025))
(assert (! (= long_term_debt_noncurrent_fy2025 xbrl_fact_us_gaap_LongTermDebtNoncurrent_instant_2026_01_31_unit_USD_dims_none) :named xbrl_bind_long_term_debt_noncurrent_fy2025_edgar_2026_01_31_0001108524_26_000060))
(assert (! (= xbrl_fact_us_gaap_LongTermDebtNoncurrent_instant_2026_01_31_unit_USD_dims_none 10439) :named xbrl_instance_long_term_debt_noncurrent_fy2025))
(assert (! (= operating_lease_liability_noncurrent_fy2025 xbrl_fact_us_gaap_OperatingLeaseLiabilityNoncurrent_instant_2026_01_31_unit_USD_dims_none) :named xbrl_bind_operating_lease_liability_noncurrent_fy2025_edgar_2026_01_31_0001108524_26_000060))
(assert (! (= xbrl_fact_us_gaap_OperatingLeaseLiabilityNoncurrent_instant_2026_01_31_unit_USD_dims_none 2189) :named xbrl_instance_operating_lease_liability_noncurrent_fy2025))
(assert (! (= other_liabilities_noncurrent_fy2025 xbrl_fact_us_gaap_OtherLiabilitiesNoncurrent_instant_2026_01_31_unit_USD_dims_none) :named xbrl_bind_other_liabilities_noncurrent_fy2025_edgar_2026_01_31_0001108524_26_000060))
(assert (! (= xbrl_fact_us_gaap_OtherLiabilitiesNoncurrent_instant_2026_01_31_unit_USD_dims_none 3417) :named xbrl_instance_other_liabilities_noncurrent_fy2025))

(check-sat)
(get-unsat-core)
(get-model)