(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_liabilities_current_fy2024 Real)
(declare-const accounts_payable_current_fy2024 Real)
(declare-const accrued_liabilities_current_fy2024 Real)
(declare-const contract_with_customer_liability_current_fy2024 Real)

(assert (! (= accounts_payable_current_fy2024 94363) :named evidence_accounts_payable_current_fy2024))
(assert (! (= accrued_liabilities_current_fy2024 66965) :named evidence_accrued_liabilities_current_fy2024))
(assert (! (= contract_with_customer_liability_current_fy2024 18103) :named evidence_contract_with_customer_liability_current_fy2024))

(assert (! (= computed_liabilities_current_fy2024 (+ accounts_payable_current_fy2024 accrued_liabilities_current_fy2024 contract_with_customer_liability_current_fy2024)) :named formula_liabilities_current_fy2024))

(assert (! (<= (- computed_liabilities_current_fy2024 179431) 179.43100000000001) :named claim_upper))
(assert (! (<= (- 179431 computed_liabilities_current_fy2024) 179.43100000000001) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_AccruedLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_ContractWithCustomerLiabilityCurrent_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none 179431) :named evidence_xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= accounts_payable_current_fy2024 xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_accounts_payable_current_fy2024_edgar_2024_12_31_0001018724_25_000004))
(assert (! (= xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2024_12_31_unit_USD_dims_none 94363) :named xbrl_instance_accounts_payable_current_fy2024))
(assert (! (= accrued_liabilities_current_fy2024 xbrl_fact_us_gaap_AccruedLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_accrued_liabilities_current_fy2024_edgar_2024_12_31_0001018724_25_000004))
(assert (! (= xbrl_fact_us_gaap_AccruedLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none 66965) :named xbrl_instance_accrued_liabilities_current_fy2024))
(assert (! (= contract_with_customer_liability_current_fy2024 xbrl_fact_us_gaap_ContractWithCustomerLiabilityCurrent_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_contract_with_customer_liability_current_fy2024_edgar_2024_12_31_0001018724_25_000004))
(assert (! (= xbrl_fact_us_gaap_ContractWithCustomerLiabilityCurrent_instant_2024_12_31_unit_USD_dims_none 18103) :named xbrl_instance_contract_with_customer_liability_current_fy2024))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccruedLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_ContractWithCustomerLiabilityCurrent_instant_2024_12_31_unit_USD_dims_none)) 2) :named xbrl_calc_16_468678268_LiabilitiesCurrent_c_9_upper))
(assert (! (>= (- xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccruedLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_ContractWithCustomerLiabilityCurrent_instant_2024_12_31_unit_USD_dims_none)) (- 2)) :named xbrl_calc_16_468678268_LiabilitiesCurrent_c_9_lower))

(check-sat)
(get-unsat-core)
(get-model)