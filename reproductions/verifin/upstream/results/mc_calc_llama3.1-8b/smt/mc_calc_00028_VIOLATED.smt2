(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_liabilities_current_fy2025 Real)
(declare-const accounts_payable_current_fy2025 Real)
(declare-const contract_with_customer_liability_current_fy2025 Real)
(declare-const debt_current_fy2025 Real)
(declare-const employee_related_liabilities_current_fy2025 Real)
(declare-const other_liabilities_current_fy2025 Real)

(assert (! (= accounts_payable_current_fy2025 3622.0) :named evidence_accounts_payable_current_fy2025))
(assert (! (= contract_with_customer_liability_current_fy2025 2710.0) :named evidence_contract_with_customer_liability_current_fy2025))
(assert (! (= debt_current_fy2025 3533.0) :named evidence_debt_current_fy2025))
(assert (! (= employee_related_liabilities_current_fy2025 1995.0) :named evidence_employee_related_liabilities_current_fy2025))
(assert (! (= other_liabilities_current_fy2025 3329.0) :named evidence_other_liabilities_current_fy2025))

(assert (! (= computed_liabilities_current_fy2025 (+ debt_current_fy2025 accounts_payable_current_fy2025 employee_related_liabilities_current_fy2025 contract_with_customer_liability_current_fy2025 other_liabilities_current_fy2025)) :named formula_liabilities_current_fy2025))

(assert (! (or (> other_liabilities_current_fy2025 0) (< other_liabilities_current_fy2025 0)) :named denom_nonzero))
(assert (! (or (> contract_with_customer_liability_current_fy2025 0) (< contract_with_customer_liability_current_fy2025 0)) :named denom_contract_with_customer_liability_current_fy2025))
(assert (! (or (> debt_current_fy2025 0) (< debt_current_fy2025 0)) :named denom_debt_current_fy2025))
(assert (! (or (> accounts_payable_current_fy2025 0) (< accounts_payable_current_fy2025 0)) :named denom_accounts_payable_current_fy2025))
(assert (! (or (> employee_related_liabilities_current_fy2025 0) (< employee_related_liabilities_current_fy2025 0)) :named denom_employee_related_liabilities_current_fy2025))

(assert (! (<= (- computed_liabilities_current_fy2025 13332.0) 133.32) :named claim_upper))
(assert (! (<= (- 13332.0 computed_liabilities_current_fy2025) 133.32) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_ContractWithCustomerLiabilityCurrent_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_DebtCurrent_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none 15189) :named evidence_xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= debt_current_fy2025 xbrl_fact_us_gaap_DebtCurrent_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_debt_current_fy2025_edgar_2025_12_31_0000097745_26_000018))
(assert (! (= xbrl_fact_us_gaap_DebtCurrent_instant_2025_12_31_unit_USD_dims_none 3533) :named xbrl_instance_debt_current_fy2025))
(assert (! (= accounts_payable_current_fy2025 xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_accounts_payable_current_fy2025_edgar_2025_12_31_0000097745_26_000018))
(assert (! (= xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_12_31_unit_USD_dims_none 3622) :named xbrl_instance_accounts_payable_current_fy2025))
(assert (! (= employee_related_liabilities_current_fy2025 xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_employee_related_liabilities_current_fy2025_edgar_2025_12_31_0000097745_26_000018))
(assert (! (= xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none 1995) :named xbrl_instance_employee_related_liabilities_current_fy2025))
(assert (! (= contract_with_customer_liability_current_fy2025 xbrl_fact_us_gaap_ContractWithCustomerLiabilityCurrent_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_contract_with_customer_liability_current_fy2025_edgar_2025_12_31_0000097745_26_000018))
(assert (! (= xbrl_fact_us_gaap_ContractWithCustomerLiabilityCurrent_instant_2025_12_31_unit_USD_dims_none 2710) :named xbrl_instance_contract_with_customer_liability_current_fy2025))
(assert (! (= other_liabilities_current_fy2025 xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_other_liabilities_current_fy2025_edgar_2025_12_31_0000097745_26_000018))
(assert (! (= xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none 3329) :named xbrl_instance_other_liabilities_current_fy2025))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_DebtCurrent_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_ContractWithCustomerLiabilityCurrent_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none)) 3) :named xbrl_calc_2_414810855_LiabilitiesCurrent_c_18_upper))
(assert (! (>= (- xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_DebtCurrent_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_ContractWithCustomerLiabilityCurrent_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none)) (- 3)) :named xbrl_calc_2_414810855_LiabilitiesCurrent_c_18_lower))

(check-sat)
(get-unsat-core)
(get-model)