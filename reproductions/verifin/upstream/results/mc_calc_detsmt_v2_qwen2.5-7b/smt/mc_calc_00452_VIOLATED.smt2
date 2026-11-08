(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_liabilities_current_fy2023 Real)
(declare-const accounts_payable_current_fy2023 Real)
(declare-const accrued_liabilities_current_fy2023 Real)
(declare-const contract_with_customer_liability_current_fy2023 Real)

(assert (! (= accounts_payable_current_fy2023 84981) :named evidence_accounts_payable_current_fy2023))
(assert (! (= accrued_liabilities_current_fy2023 64709) :named evidence_accrued_liabilities_current_fy2023))
(assert (! (= contract_with_customer_liability_current_fy2023 15227) :named evidence_contract_with_customer_liability_current_fy2023))

(assert (! (= computed_liabilities_current_fy2023 (+ accounts_payable_current_fy2023 accrued_liabilities_current_fy2023 contract_with_customer_liability_current_fy2023)) :named formula_liabilities_current_fy2023))

(assert (! (<= (- computed_liabilities_current_fy2023 273000) 273) :named claim_upper))
(assert (! (<= (- 273000 computed_liabilities_current_fy2023) 273) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2023_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_AccruedLiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_ContractWithCustomerLiabilityCurrent_instant_2023_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none 164917) :named evidence_xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= accounts_payable_current_fy2023 xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2023_12_31_unit_USD_dims_none) :named xbrl_bind_accounts_payable_current_fy2023_edgar_2023_12_31_0001018724_24_000008))
(assert (! (= xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2023_12_31_unit_USD_dims_none 84981) :named xbrl_instance_accounts_payable_current_fy2023))
(assert (! (= accrued_liabilities_current_fy2023 xbrl_fact_us_gaap_AccruedLiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none) :named xbrl_bind_accrued_liabilities_current_fy2023_edgar_2023_12_31_0001018724_24_000008))
(assert (! (= xbrl_fact_us_gaap_AccruedLiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none 64709) :named xbrl_instance_accrued_liabilities_current_fy2023))
(assert (! (= contract_with_customer_liability_current_fy2023 xbrl_fact_us_gaap_ContractWithCustomerLiabilityCurrent_instant_2023_12_31_unit_USD_dims_none) :named xbrl_bind_contract_with_customer_liability_current_fy2023_edgar_2023_12_31_0001018724_24_000008))
(assert (! (= xbrl_fact_us_gaap_ContractWithCustomerLiabilityCurrent_instant_2023_12_31_unit_USD_dims_none 15227) :named xbrl_instance_contract_with_customer_liability_current_fy2023))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2023_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccruedLiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none xbrl_fact_us_gaap_ContractWithCustomerLiabilityCurrent_instant_2023_12_31_unit_USD_dims_none)) 2) :named xbrl_calc_12_468678268_LiabilitiesCurrent_c_9_upper))
(assert (! (>= (- xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2023_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccruedLiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none xbrl_fact_us_gaap_ContractWithCustomerLiabilityCurrent_instant_2023_12_31_unit_USD_dims_none)) (- 2)) :named xbrl_calc_12_468678268_LiabilitiesCurrent_c_9_lower))

(check-sat)
(get-unsat-core)
(get-model)