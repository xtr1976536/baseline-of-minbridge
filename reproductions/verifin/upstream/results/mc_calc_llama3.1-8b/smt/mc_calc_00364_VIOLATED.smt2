(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_liabilities_current_fy2023 Real)
(declare-const accounts_payable_current_fy2023 Real)
(declare-const contract_with_customer_liability_current_fy2023 Real)
(declare-const debt_current_fy2023 Real)
(declare-const employee_related_liabilities_current_fy2023 Real)
(declare-const other_liabilities_current_fy2023 Real)

(assert (! (= accounts_payable_current_fy2023 2872.0) :named evidence_accounts_payable_current_fy2023))
(assert (! (= contract_with_customer_liability_current_fy2023 2689.0) :named evidence_contract_with_customer_liability_current_fy2023))
(assert (! (= debt_current_fy2023 3609.0) :named evidence_debt_current_fy2023))
(assert (! (= employee_related_liabilities_current_fy2023 1596.0) :named evidence_employee_related_liabilities_current_fy2023))
(assert (! (= other_liabilities_current_fy2023 3246.0) :named evidence_other_liabilities_current_fy2023))

(assert (! (= computed_liabilities_current_fy2023 (+ debt_current_fy2023 accounts_payable_current_fy2023 employee_related_liabilities_current_fy2023 contract_with_customer_liability_current_fy2023 other_liabilities_current_fy2023)) :named formula_liabilities_current_fy2023))

(assert (! (or (> debt_current_fy2023 0) (< debt_current_fy2023 0)) :named denom_nonzero))
(assert (! (or (> accounts_payable_current_fy2023 0) (< accounts_payable_current_fy2023 0)) :named denom_nonzero_1))
(assert (! (or (> contract_with_customer_liability_current_fy2023 0) (< contract_with_customer_liability_current_fy2023 0)) :named denom_nonzero_2))
(assert (! (or (> employee_related_liabilities_current_fy2023 0) (< employee_related_liabilities_current_fy2023 0)) :named denom_nonzero_3))
(assert (! (or (> other_liabilities_current_fy2023 0) (< other_liabilities_current_fy2023 0)) :named denom_nonzero_4))

(assert (! (<= (- computed_liabilities_current_fy2023 17010.0) 170.1) :named claim_upper))
(assert (! (<= (- 17010.0 computed_liabilities_current_fy2023) 170.1) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2023_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_ContractWithCustomerLiabilityCurrent_instant_2023_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_DebtCurrent_instant_2023_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none 14012) :named evidence_xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= accounts_payable_current_fy2023 xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2023_12_31_unit_USD_dims_none) :named xbrl_bind_accounts_payable_current_fy2023_edgar_2023_12_31_0000097745_24_000007))
(assert (! (= xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2023_12_31_unit_USD_dims_none 2872) :named xbrl_instance_accounts_payable_current_fy2023))
(assert (! (= debt_current_fy2023 xbrl_fact_us_gaap_DebtCurrent_instant_2023_12_31_unit_USD_dims_none) :named xbrl_bind_debt_current_fy2023_edgar_2023_12_31_0000097745_24_000007))
(assert (! (= xbrl_fact_us_gaap_DebtCurrent_instant_2023_12_31_unit_USD_dims_none 3609) :named xbrl_instance_debt_current_fy2023))
(assert (! (= employee_related_liabilities_current_fy2023 xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none) :named xbrl_bind_employee_related_liabilities_current_fy2023_edgar_2023_12_31_0000097745_24_000007))
(assert (! (= xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none 1596) :named xbrl_instance_employee_related_liabilities_current_fy2023))
(assert (! (= contract_with_customer_liability_current_fy2023 xbrl_fact_us_gaap_ContractWithCustomerLiabilityCurrent_instant_2023_12_31_unit_USD_dims_none) :named xbrl_bind_contract_with_customer_liability_current_fy2023_edgar_2023_12_31_0000097745_24_000007))
(assert (! (= xbrl_fact_us_gaap_ContractWithCustomerLiabilityCurrent_instant_2023_12_31_unit_USD_dims_none 2689) :named xbrl_instance_contract_with_customer_liability_current_fy2023))
(assert (! (= other_liabilities_current_fy2023 xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none) :named xbrl_bind_other_liabilities_current_fy2023_edgar_2023_12_31_0000097745_24_000007))
(assert (! (= xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none 3246) :named xbrl_instance_other_liabilities_current_fy2023))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_DebtCurrent_instant_2023_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2023_12_31_unit_USD_dims_none xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none xbrl_fact_us_gaap_ContractWithCustomerLiabilityCurrent_instant_2023_12_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none)) 3) :named xbrl_calc_3_415921018_LiabilitiesCurrent_c_21_upper))
(assert (! (>= (- xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_DebtCurrent_instant_2023_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2023_12_31_unit_USD_dims_none xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none xbrl_fact_us_gaap_ContractWithCustomerLiabilityCurrent_instant_2023_12_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none)) (- 3)) :named xbrl_calc_3_415921018_LiabilitiesCurrent_c_21_lower))

(check-sat)
(get-unsat-core)
(get-model)