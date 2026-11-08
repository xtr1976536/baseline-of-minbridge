(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_liabilities_noncurrent_fy2025 Real)
(declare-const long_term_debt_noncurrent_fy2025 Real)
(declare-const other_liabilities_noncurrent_fy2025 Real)

(assert (! (= long_term_debt_noncurrent_fy2025 78328) :named evidence_long_term_debt_noncurrent_fy2025))
(assert (! (= other_liabilities_noncurrent_fy2025 41549) :named evidence_other_liabilities_noncurrent_fy2025))

(assert (! (= computed_liabilities_noncurrent_fy2025 (+ long_term_debt_noncurrent_fy2025 other_liabilities_noncurrent_fy2025)) :named formula_liabilities_noncurrent_fy2025))

(assert (! (<= (- computed_liabilities_noncurrent_fy2025 119877) 119.87700000000001) :named claim_upper))
(assert (! (<= (- 119877 computed_liabilities_noncurrent_fy2025) 119.87700000000001) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_LiabilitiesNoncurrent_instant_2025_09_27_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LongTermDebtCurrent_instant_2025_09_27_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LongTermDebtNoncurrent_instant_2025_09_27_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LongTermDebt_instant_2025_09_27_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherLiabilitiesNoncurrent_instant_2025_09_27_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_LiabilitiesNoncurrent_instant_2025_09_27_unit_USD_dims_none 119877) :named evidence_xbrl_fact_us_gaap_LiabilitiesNoncurrent_instant_2025_09_27_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_LongTermDebtCurrent_instant_2025_09_27_unit_USD_dims_none 12350) :named evidence_xbrl_fact_us_gaap_LongTermDebtCurrent_instant_2025_09_27_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_LongTermDebt_instant_2025_09_27_unit_USD_dims_none 90678) :named evidence_xbrl_fact_us_gaap_LongTermDebt_instant_2025_09_27_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= long_term_debt_noncurrent_fy2025 xbrl_fact_us_gaap_LongTermDebtNoncurrent_instant_2025_09_27_unit_USD_dims_none) :named xbrl_bind_long_term_debt_noncurrent_fy2025_edgar_2025_09_27_0000320193_25_000079))
(assert (! (= xbrl_fact_us_gaap_LongTermDebtNoncurrent_instant_2025_09_27_unit_USD_dims_none 78328) :named xbrl_instance_long_term_debt_noncurrent_fy2025))
(assert (! (= other_liabilities_noncurrent_fy2025 xbrl_fact_us_gaap_OtherLiabilitiesNoncurrent_instant_2025_09_27_unit_USD_dims_none) :named xbrl_bind_other_liabilities_noncurrent_fy2025_edgar_2025_09_27_0000320193_25_000079))
(assert (! (= xbrl_fact_us_gaap_OtherLiabilitiesNoncurrent_instant_2025_09_27_unit_USD_dims_none 41549) :named xbrl_instance_other_liabilities_noncurrent_fy2025))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_LiabilitiesNoncurrent_instant_2025_09_27_unit_USD_dims_none (+ xbrl_fact_us_gaap_LongTermDebtNoncurrent_instant_2025_09_27_unit_USD_dims_none xbrl_fact_us_gaap_OtherLiabilitiesNoncurrent_instant_2025_09_27_unit_USD_dims_none)) 1.5) :named xbrl_calc_11_745565710_LiabilitiesNoncurrent_c_20_upper))
(assert (! (>= (- xbrl_fact_us_gaap_LiabilitiesNoncurrent_instant_2025_09_27_unit_USD_dims_none (+ xbrl_fact_us_gaap_LongTermDebtNoncurrent_instant_2025_09_27_unit_USD_dims_none xbrl_fact_us_gaap_OtherLiabilitiesNoncurrent_instant_2025_09_27_unit_USD_dims_none)) (- 1.5)) :named xbrl_calc_11_745565710_LiabilitiesNoncurrent_c_20_lower))
(assert (! (<= (- xbrl_fact_us_gaap_LongTermDebt_instant_2025_09_27_unit_USD_dims_none (+ xbrl_fact_us_gaap_LongTermDebtCurrent_instant_2025_09_27_unit_USD_dims_none xbrl_fact_us_gaap_LongTermDebtNoncurrent_instant_2025_09_27_unit_USD_dims_none)) 1.5) :named xbrl_calc_64_877906095_LongTermDebt_c_20_upper))
(assert (! (>= (- xbrl_fact_us_gaap_LongTermDebt_instant_2025_09_27_unit_USD_dims_none (+ xbrl_fact_us_gaap_LongTermDebtCurrent_instant_2025_09_27_unit_USD_dims_none xbrl_fact_us_gaap_LongTermDebtNoncurrent_instant_2025_09_27_unit_USD_dims_none)) (- 1.5)) :named xbrl_calc_64_877906095_LongTermDebt_c_20_lower))

(check-sat)
(get-unsat-core)
(get-model)