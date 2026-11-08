(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_liabilities_current_fy2025 Real)
(declare-const accounts_payable_current_fy2025 Real)
(declare-const accrued_liabilities_current_fy2025 Real)
(declare-const deferred_revenue_current_fy2025 Real)
(declare-const employee_related_liabilities_current_fy2025 Real)
(declare-const other_liabilities_current_fy2025 Real)

(assert (! (= accounts_payable_current_fy2025 19783) :named evidence_accounts_payable_current_fy2025))
(assert (! (= accrued_liabilities_current_fy2025 2677) :named evidence_accrued_liabilities_current_fy2025))
(assert (! (= deferred_revenue_current_fy2025 2854) :named evidence_deferred_revenue_current_fy2025))
(assert (! (= employee_related_liabilities_current_fy2025 5205) :named evidence_employee_related_liabilities_current_fy2025))
(assert (! (= other_liabilities_current_fy2025 6589) :named evidence_other_liabilities_current_fy2025))

(assert (! (= computed_liabilities_current_fy2025 (+ accounts_payable_current_fy2025 employee_related_liabilities_current_fy2025 accrued_liabilities_current_fy2025 deferred_revenue_current_fy2025 other_liabilities_current_fy2025)) :named formula_liabilities_current_fy2025))

(assert (! (<= (- computed_liabilities_current_fy2025 37108) 37.108000000000004) :named claim_upper))
(assert (! (<= (- 37108 computed_liabilities_current_fy2025) 37.108000000000004) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_08_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_AccruedLiabilitiesCurrent_instant_2025_08_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_DeferredRevenueCurrent_instant_2025_08_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2025_08_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_08_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2025_08_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_08_31_unit_USD_dims_none 37108) :named evidence_xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_08_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= accounts_payable_current_fy2025 xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_08_31_unit_USD_dims_none) :named xbrl_bind_accounts_payable_current_fy2025_edgar_2025_08_31_0000909832_25_000101))
(assert (! (= xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_08_31_unit_USD_dims_none 19783) :named xbrl_instance_accounts_payable_current_fy2025))
(assert (! (= employee_related_liabilities_current_fy2025 xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2025_08_31_unit_USD_dims_none) :named xbrl_bind_employee_related_liabilities_current_fy2025_edgar_2025_08_31_0000909832_25_000101))
(assert (! (= xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2025_08_31_unit_USD_dims_none 5205) :named xbrl_instance_employee_related_liabilities_current_fy2025))
(assert (! (= accrued_liabilities_current_fy2025 xbrl_fact_us_gaap_AccruedLiabilitiesCurrent_instant_2025_08_31_unit_USD_dims_none) :named xbrl_bind_accrued_liabilities_current_fy2025_edgar_2025_08_31_0000909832_25_000101))
(assert (! (= xbrl_fact_us_gaap_AccruedLiabilitiesCurrent_instant_2025_08_31_unit_USD_dims_none 2677) :named xbrl_instance_accrued_liabilities_current_fy2025))
(assert (! (= deferred_revenue_current_fy2025 xbrl_fact_us_gaap_DeferredRevenueCurrent_instant_2025_08_31_unit_USD_dims_none) :named xbrl_bind_deferred_revenue_current_fy2025_edgar_2025_08_31_0000909832_25_000101))
(assert (! (= xbrl_fact_us_gaap_DeferredRevenueCurrent_instant_2025_08_31_unit_USD_dims_none 2854) :named xbrl_instance_deferred_revenue_current_fy2025))
(assert (! (= other_liabilities_current_fy2025 xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2025_08_31_unit_USD_dims_none) :named xbrl_bind_other_liabilities_current_fy2025_edgar_2025_08_31_0000909832_25_000101))
(assert (! (= xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2025_08_31_unit_USD_dims_none 6589) :named xbrl_instance_other_liabilities_current_fy2025))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_08_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_08_31_unit_USD_dims_none xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2025_08_31_unit_USD_dims_none xbrl_fact_us_gaap_AccruedLiabilitiesCurrent_instant_2025_08_31_unit_USD_dims_none xbrl_fact_us_gaap_DeferredRevenueCurrent_instant_2025_08_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2025_08_31_unit_USD_dims_none)) 3) :named xbrl_calc_6_881368694_LiabilitiesCurrent_c_12_upper))
(assert (! (>= (- xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_08_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_08_31_unit_USD_dims_none xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2025_08_31_unit_USD_dims_none xbrl_fact_us_gaap_AccruedLiabilitiesCurrent_instant_2025_08_31_unit_USD_dims_none xbrl_fact_us_gaap_DeferredRevenueCurrent_instant_2025_08_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2025_08_31_unit_USD_dims_none)) (- 3)) :named xbrl_calc_6_881368694_LiabilitiesCurrent_c_12_lower))

(check-sat)
(get-unsat-core)
(get-model)