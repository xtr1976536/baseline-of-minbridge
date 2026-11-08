(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_liabilities_current_fy2023 Real)
(declare-const accounts_payable_current_fy2023 Real)
(declare-const debt_current_fy2023 Real)
(declare-const deferred_revenue_current_fy2023 Real)
(declare-const employee_related_liabilities_current_fy2023 Real)
(declare-const liabilities_of_disposal_group_including_discontinued_operation_current_fy2023 Real)
(declare-const other_liabilities_current_fy2023 Real)

(assert (! (= accounts_payable_current_fy2023 1912.0) :named evidence_accounts_payable_current_fy2023))
(assert (! (= debt_current_fy2023 914.0) :named evidence_debt_current_fy2023))
(assert (! (= deferred_revenue_current_fy2023 293.0) :named evidence_deferred_revenue_current_fy2023))
(assert (! (= employee_related_liabilities_current_fy2023 1685.0) :named evidence_employee_related_liabilities_current_fy2023))
(assert (! (= liabilities_of_disposal_group_including_discontinued_operation_current_fy2023 333.0) :named evidence_liabilities_of_disposal_group_including_discontinued_operation_current_fy2023))
(assert (! (= other_liabilities_current_fy2023 4491.0) :named evidence_other_liabilities_current_fy2023))

(assert (! (= computed_liabilities_current_fy2023 (+ accounts_payable_current_fy2023 employee_related_liabilities_current_fy2023 deferred_revenue_current_fy2023 debt_current_fy2023 liabilities_of_disposal_group_including_discontinued_operation_current_fy2023 other_liabilities_current_fy2023)) :named formula_liabilities_current_fy2023))

(assert (! (or (> accounts_payable_current_fy2023 0) (< accounts_payable_current_fy2023 0)) :named denom_nonzero))
(assert (! (or (> debt_current_fy2023 0) (< debt_current_fy2023 0)) :named denom_nonzero1))
(assert (! (or (> deferred_revenue_current_fy2023 0) (< deferred_revenue_current_fy2023 0)) :named denom_nonzero2))
(assert (! (or (> employee_related_liabilities_current_fy2023 0) (< employee_related_liabilities_current_fy2023 0)) :named denom_nonzero3))
(assert (! (or (> liabilities_of_disposal_group_including_discontinued_operation_current_fy2023 0) (< liabilities_of_disposal_group_including_discontinued_operation_current_fy2023 0)) :named denom_nonzero4))
(assert (! (or (> other_liabilities_current_fy2023 0) (< other_liabilities_current_fy2023 0)) :named denom_nonzero5))

(assert (! (<= (- computed_liabilities_current_fy2023 11866.0) 118.66) :named claim_upper))
(assert (! (<= (- 11866.0 computed_liabilities_current_fy2023) 118.66) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2023_09_24_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_DebtCurrent_instant_2023_09_24_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_DeferredRevenueCurrent_instant_2023_09_24_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2023_09_24_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2023_09_24_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LiabilitiesOfDisposalGroupIncludingDiscontinuedOperationCurrent_instant_2023_09_24_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2023_09_24_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2023_09_24_unit_USD_dims_none 9628) :named evidence_xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2023_09_24_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= employee_related_liabilities_current_fy2023 xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2023_09_24_unit_USD_dims_none) :named xbrl_bind_employee_related_liabilities_current_fy2023_edgar_2023_09_24_0000804328_23_000055))
(assert (! (= xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2023_09_24_unit_USD_dims_none 1685) :named xbrl_instance_employee_related_liabilities_current_fy2023))
(assert (! (= accounts_payable_current_fy2023 xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2023_09_24_unit_USD_dims_none) :named xbrl_bind_accounts_payable_current_fy2023_edgar_2023_09_24_0000804328_23_000055))
(assert (! (= xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2023_09_24_unit_USD_dims_none 1912) :named xbrl_instance_accounts_payable_current_fy2023))
(assert (! (= deferred_revenue_current_fy2023 xbrl_fact_us_gaap_DeferredRevenueCurrent_instant_2023_09_24_unit_USD_dims_none) :named xbrl_bind_deferred_revenue_current_fy2023_edgar_2023_09_24_0000804328_23_000055))
(assert (! (= xbrl_fact_us_gaap_DeferredRevenueCurrent_instant_2023_09_24_unit_USD_dims_none 293) :named xbrl_instance_deferred_revenue_current_fy2023))
(assert (! (= debt_current_fy2023 xbrl_fact_us_gaap_DebtCurrent_instant_2023_09_24_unit_USD_dims_none) :named xbrl_bind_debt_current_fy2023_edgar_2023_09_24_0000804328_23_000055))
(assert (! (= xbrl_fact_us_gaap_DebtCurrent_instant_2023_09_24_unit_USD_dims_none 914) :named xbrl_instance_debt_current_fy2023))
(assert (! (= liabilities_of_disposal_group_including_discontinued_operation_current_fy2023 xbrl_fact_us_gaap_LiabilitiesOfDisposalGroupIncludingDiscontinuedOperationCurrent_instant_2023_09_24_unit_USD_dims_none) :named xbrl_bind_liabilities_of_disposal_group_including_discontinued_operation_current_fy2023_edgar_2023_09_24_0000804328_23_000055))
(assert (! (= xbrl_fact_us_gaap_LiabilitiesOfDisposalGroupIncludingDiscontinuedOperationCurrent_instant_2023_09_24_unit_USD_dims_none 333) :named xbrl_instance_liabilities_of_disposal_group_including_discontinued_operation_current_fy2023))
(assert (! (= other_liabilities_current_fy2023 xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2023_09_24_unit_USD_dims_none) :named xbrl_bind_other_liabilities_current_fy2023_edgar_2023_09_24_0000804328_23_000055))
(assert (! (= xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2023_09_24_unit_USD_dims_none 4491) :named xbrl_instance_other_liabilities_current_fy2023))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2023_09_24_unit_USD_dims_none (+ xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2023_09_24_unit_USD_dims_none xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2023_09_24_unit_USD_dims_none xbrl_fact_us_gaap_DeferredRevenueCurrent_instant_2023_09_24_unit_USD_dims_none xbrl_fact_us_gaap_DebtCurrent_instant_2023_09_24_unit_USD_dims_none xbrl_fact_us_gaap_LiabilitiesOfDisposalGroupIncludingDiscontinuedOperationCurrent_instant_2023_09_24_unit_USD_dims_none xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2023_09_24_unit_USD_dims_none)) 3.5) :named xbrl_calc_1_237022267_LiabilitiesCurrent_c_5_upper))
(assert (! (>= (- xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2023_09_24_unit_USD_dims_none (+ xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2023_09_24_unit_USD_dims_none xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2023_09_24_unit_USD_dims_none xbrl_fact_us_gaap_DeferredRevenueCurrent_instant_2023_09_24_unit_USD_dims_none xbrl_fact_us_gaap_DebtCurrent_instant_2023_09_24_unit_USD_dims_none xbrl_fact_us_gaap_LiabilitiesOfDisposalGroupIncludingDiscontinuedOperationCurrent_instant_2023_09_24_unit_USD_dims_none xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2023_09_24_unit_USD_dims_none)) (- 3.5)) :named xbrl_calc_1_237022267_LiabilitiesCurrent_c_5_lower))

(check-sat)
(get-unsat-core)
(get-model)