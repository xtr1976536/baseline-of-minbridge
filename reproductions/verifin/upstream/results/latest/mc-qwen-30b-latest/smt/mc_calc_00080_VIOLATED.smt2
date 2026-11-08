(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_liabilities_current_fy2025 Real)
(declare-const accounts_payable_current_fy2025 Real)
(declare-const debt_current_fy2025 Real)
(declare-const deferred_revenue_current_fy2025 Real)
(declare-const employee_related_liabilities_current_fy2025 Real)
(declare-const other_liabilities_current_fy2025 Real)

(assert (! (= accounts_payable_current_fy2025 2791) :named evidence_accounts_payable_current_fy2025))
(assert (! (= debt_current_fy2025 0) :named evidence_debt_current_fy2025))
(assert (! (= deferred_revenue_current_fy2025 358) :named evidence_deferred_revenue_current_fy2025))
(assert (! (= employee_related_liabilities_current_fy2025 1839) :named evidence_employee_related_liabilities_current_fy2025))
(assert (! (= other_liabilities_current_fy2025 4156) :named evidence_other_liabilities_current_fy2025))

(assert (! (= computed_liabilities_current_fy2025 (+ accounts_payable_current_fy2025 employee_related_liabilities_current_fy2025 deferred_revenue_current_fy2025 debt_current_fy2025 other_liabilities_current_fy2025)) :named formula_liabilities_current_fy2025))

(assert (! (<= (- computed_liabilities_current_fy2025 10504) 10.504) :named claim_upper))
(assert (! (<= (- 10504 computed_liabilities_current_fy2025) 10.504) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_09_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_DebtCurrent_instant_2025_09_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_DeferredRevenueCurrent_instant_2025_09_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none 9144) :named evidence_xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= accounts_payable_current_fy2025 xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_09_28_unit_USD_dims_none) :named xbrl_bind_accounts_payable_current_fy2025_edgar_2025_09_28_0000804328_25_000085))
(assert (! (= xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_09_28_unit_USD_dims_none 2791) :named xbrl_instance_accounts_payable_current_fy2025))
(assert (! (= employee_related_liabilities_current_fy2025 xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none) :named xbrl_bind_employee_related_liabilities_current_fy2025_edgar_2025_09_28_0000804328_25_000085))
(assert (! (= xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none 1839) :named xbrl_instance_employee_related_liabilities_current_fy2025))
(assert (! (= deferred_revenue_current_fy2025 xbrl_fact_us_gaap_DeferredRevenueCurrent_instant_2025_09_28_unit_USD_dims_none) :named xbrl_bind_deferred_revenue_current_fy2025_edgar_2025_09_28_0000804328_25_000085))
(assert (! (= xbrl_fact_us_gaap_DeferredRevenueCurrent_instant_2025_09_28_unit_USD_dims_none 358) :named xbrl_instance_deferred_revenue_current_fy2025))
(assert (! (= debt_current_fy2025 xbrl_fact_us_gaap_DebtCurrent_instant_2025_09_28_unit_USD_dims_none) :named xbrl_bind_debt_current_fy2025_edgar_2025_09_28_0000804328_25_000085))
(assert (! (= xbrl_fact_us_gaap_DebtCurrent_instant_2025_09_28_unit_USD_dims_none 0) :named xbrl_instance_debt_current_fy2025))
(assert (! (= other_liabilities_current_fy2025 xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none) :named xbrl_bind_other_liabilities_current_fy2025_edgar_2025_09_28_0000804328_25_000085))
(assert (! (= xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none 4156) :named xbrl_instance_other_liabilities_current_fy2025))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none (+ xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_09_28_unit_USD_dims_none xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none xbrl_fact_us_gaap_DeferredRevenueCurrent_instant_2025_09_28_unit_USD_dims_none xbrl_fact_us_gaap_DebtCurrent_instant_2025_09_28_unit_USD_dims_none xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none)) 3) :named xbrl_calc_5_237022267_LiabilitiesCurrent_c_7_upper))
(assert (! (>= (- xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none (+ xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_09_28_unit_USD_dims_none xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none xbrl_fact_us_gaap_DeferredRevenueCurrent_instant_2025_09_28_unit_USD_dims_none xbrl_fact_us_gaap_DebtCurrent_instant_2025_09_28_unit_USD_dims_none xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2025_09_28_unit_USD_dims_none)) (- 3)) :named xbrl_calc_5_237022267_LiabilitiesCurrent_c_7_lower))

(check-sat)
(get-unsat-core)
(get-model)