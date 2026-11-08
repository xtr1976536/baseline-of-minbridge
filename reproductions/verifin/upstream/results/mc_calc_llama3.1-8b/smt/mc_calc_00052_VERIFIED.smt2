(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_liabilities_fy2025 Real)
(declare-const deferred_revenue_noncurrent_fy2025 Real)
(declare-const liabilities_current_fy2025 Real)
(declare-const long_term_debt_fy2025 Real)
(declare-const other_liabilities_fy2025 Real)

(assert (! (= deferred_revenue_noncurrent_fy2025 71.0) :named evidence_deferred_revenue_noncurrent_fy2025))
(assert (! (= liabilities_current_fy2025 9144.0) :named evidence_liabilities_current_fy2025))
(assert (! (= long_term_debt_fy2025 14811.0) :named evidence_long_term_debt_fy2025))
(assert (! (= other_liabilities_fy2025 4911.0) :named evidence_other_liabilities_fy2025))

(assert (! (= computed_liabilities_fy2025 (+ liabilities_current_fy2025 deferred_revenue_noncurrent_fy2025 long_term_debt_fy2025 other_liabilities_fy2025)) :named formula_liabilities_fy2025))

(assert (! (or (> liabilities_current_fy2025 0) (< liabilities_current_fy2025 0)) :named denom_nonzero))
(assert (! (or (> deferred_revenue_noncurrent_fy2025 0) (< deferred_revenue_noncurrent_fy2025 0)) :named denom_deferred_revenue_noncurrent_fy2025))
(assert (! (or (> long_term_debt_fy2025 0) (< long_term_debt_fy2025 0)) :named denom_long_term_debt_fy2025))
(assert (! (or (> other_liabilities_fy2025 0) (< other_liabilities_fy2025 0)) :named denom_other_liabilities_fy2025))

(assert (! (<= (- computed_liabilities_fy2025 28880.0) 288.8) :named claim_upper))
(assert (! (<= (- 28880.0 computed_liabilities_fy2025) 288.8) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_09_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_DebtCurrent_instant_2025_09_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_DeferredRevenueCurrent_instant_2025_09_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_DeferredRevenueNoncurrent_instant_2025_09_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_Liabilities_instant_2025_09_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LongTermDebt_instant_2025_09_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherLiabilities_instant_2025_09_28_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_09_28_unit_USD_dims_none 2791) :named evidence_xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_09_28_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_DebtCurrent_instant_2025_09_28_unit_USD_dims_none 0) :named evidence_xbrl_fact_us_gaap_DebtCurrent_instant_2025_09_28_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_DeferredRevenueCurrent_instant_2025_09_28_unit_USD_dims_none 358) :named evidence_xbrl_fact_us_gaap_DeferredRevenueCurrent_instant_2025_09_28_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none 1839) :named evidence_xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_Liabilities_instant_2025_09_28_unit_USD_dims_none 28937) :named evidence_xbrl_fact_us_gaap_Liabilities_instant_2025_09_28_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none 4156) :named evidence_xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= liabilities_current_fy2025 xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none) :named xbrl_bind_liabilities_current_fy2025_edgar_2025_09_28_0000804328_25_000085))
(assert (! (= xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none 9144) :named xbrl_instance_liabilities_current_fy2025))
(assert (! (= deferred_revenue_noncurrent_fy2025 xbrl_fact_us_gaap_DeferredRevenueNoncurrent_instant_2025_09_28_unit_USD_dims_none) :named xbrl_bind_deferred_revenue_noncurrent_fy2025_edgar_2025_09_28_0000804328_25_000085))
(assert (! (= xbrl_fact_us_gaap_DeferredRevenueNoncurrent_instant_2025_09_28_unit_USD_dims_none 71) :named xbrl_instance_deferred_revenue_noncurrent_fy2025))
(assert (! (= long_term_debt_fy2025 xbrl_fact_us_gaap_LongTermDebt_instant_2025_09_28_unit_USD_dims_none) :named xbrl_bind_long_term_debt_fy2025_edgar_2025_09_28_0000804328_25_000085))
(assert (! (= xbrl_fact_us_gaap_LongTermDebt_instant_2025_09_28_unit_USD_dims_none 14811) :named xbrl_instance_long_term_debt_fy2025))
(assert (! (= other_liabilities_fy2025 xbrl_fact_us_gaap_OtherLiabilities_instant_2025_09_28_unit_USD_dims_none) :named xbrl_bind_other_liabilities_fy2025_edgar_2025_09_28_0000804328_25_000085))
(assert (! (= xbrl_fact_us_gaap_OtherLiabilities_instant_2025_09_28_unit_USD_dims_none 4911) :named xbrl_instance_other_liabilities_fy2025))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_Liabilities_instant_2025_09_28_unit_USD_dims_none (+ xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none xbrl_fact_us_gaap_DeferredRevenueNoncurrent_instant_2025_09_28_unit_USD_dims_none xbrl_fact_us_gaap_LongTermDebt_instant_2025_09_28_unit_USD_dims_none xbrl_fact_us_gaap_OtherLiabilities_instant_2025_09_28_unit_USD_dims_none)) 2.5) :named xbrl_calc_2_237022267_Liabilities_c_7_upper))
(assert (! (>= (- xbrl_fact_us_gaap_Liabilities_instant_2025_09_28_unit_USD_dims_none (+ xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none xbrl_fact_us_gaap_DeferredRevenueNoncurrent_instant_2025_09_28_unit_USD_dims_none xbrl_fact_us_gaap_LongTermDebt_instant_2025_09_28_unit_USD_dims_none xbrl_fact_us_gaap_OtherLiabilities_instant_2025_09_28_unit_USD_dims_none)) (- 2.5)) :named xbrl_calc_2_237022267_Liabilities_c_7_lower))
(assert (! (<= (- xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none (+ xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_09_28_unit_USD_dims_none xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none xbrl_fact_us_gaap_DeferredRevenueCurrent_instant_2025_09_28_unit_USD_dims_none xbrl_fact_us_gaap_DebtCurrent_instant_2025_09_28_unit_USD_dims_none xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none)) 3) :named xbrl_calc_5_237022267_LiabilitiesCurrent_c_7_upper))
(assert (! (>= (- xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none (+ xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_09_28_unit_USD_dims_none xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none xbrl_fact_us_gaap_DeferredRevenueCurrent_instant_2025_09_28_unit_USD_dims_none xbrl_fact_us_gaap_DebtCurrent_instant_2025_09_28_unit_USD_dims_none xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none)) (- 3)) :named xbrl_calc_5_237022267_LiabilitiesCurrent_c_7_lower))

(check-sat)
(get-unsat-core)
(get-model)