(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_liabilities_current_fy2025 Real)
(declare-const accounts_payable_current_fy2025 Real)
(declare-const accrued_liabilities_current_fy2025 Real)
(declare-const contract_with_customer_liability_current_fy2025 Real)

(assert (! (= accounts_payable_current_fy2025 121909) :named evidence_accounts_payable_current_fy2025))
(assert (! (= accrued_liabilities_current_fy2025 75520) :named evidence_accrued_liabilities_current_fy2025))
(assert (! (= contract_with_customer_liability_current_fy2025 20576) :named evidence_contract_with_customer_liability_current_fy2025))

(assert (! (= computed_liabilities_current_fy2025 (+ accounts_payable_current_fy2025 accrued_liabilities_current_fy2025 contract_with_customer_liability_current_fy2025)) :named formula_liabilities_current_fy2025))

(assert (! (<= (- computed_liabilities_current_fy2025 218005) 218.005) :named claim_upper))
(assert (! (<= (- 218005 computed_liabilities_current_fy2025) 218.005) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_AccruedLiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_ContractWithCustomerLiabilityCurrent_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none 218005) :named evidence_xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= accounts_payable_current_fy2025 xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_accounts_payable_current_fy2025_edgar_2025_12_31_0001018724_26_000004))
(assert (! (= xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_12_31_unit_USD_dims_none 121909) :named xbrl_instance_accounts_payable_current_fy2025))
(assert (! (= accrued_liabilities_current_fy2025 xbrl_fact_us_gaap_AccruedLiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_accrued_liabilities_current_fy2025_edgar_2025_12_31_0001018724_26_000004))
(assert (! (= xbrl_fact_us_gaap_AccruedLiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none 75520) :named xbrl_instance_accrued_liabilities_current_fy2025))
(assert (! (= contract_with_customer_liability_current_fy2025 xbrl_fact_us_gaap_ContractWithCustomerLiabilityCurrent_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_contract_with_customer_liability_current_fy2025_edgar_2025_12_31_0001018724_26_000004))
(assert (! (= xbrl_fact_us_gaap_ContractWithCustomerLiabilityCurrent_instant_2025_12_31_unit_USD_dims_none 20576) :named xbrl_instance_contract_with_customer_liability_current_fy2025))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccruedLiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_ContractWithCustomerLiabilityCurrent_instant_2025_12_31_unit_USD_dims_none)) 2) :named xbrl_calc_13_468678268_LiabilitiesCurrent_c_9_upper))
(assert (! (>= (- xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccruedLiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_ContractWithCustomerLiabilityCurrent_instant_2025_12_31_unit_USD_dims_none)) (- 2)) :named xbrl_calc_13_468678268_LiabilitiesCurrent_c_9_lower))

(check-sat)
(get-unsat-core)
(get-model)