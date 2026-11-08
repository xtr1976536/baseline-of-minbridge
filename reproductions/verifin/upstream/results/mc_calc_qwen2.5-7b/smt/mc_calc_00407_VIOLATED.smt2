(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_liabilities_current_fy2025 Real)
(declare-const accounts_payable_and_other_accrued_liabilities_current_fy2025 Real)
(declare-const contract_with_customer_liability_current_fy2025 Real)
(declare-const convertible_debt_current_fy2025 Real)
(declare-const operating_lease_liability_current_fy2025 Real)

(assert (! (= accounts_payable_and_other_accrued_liabilities_current_fy2025 8253.0) :named evidence_accounts_payable))
(assert (! (= contract_with_customer_liability_current_fy2025 24317.0) :named evidence_contract))
(assert (! (= convertible_debt_current_fy2025 4000.0) :named evidence_convertible))
(assert (! (= operating_lease_liability_current_fy2025 548.0) :named evidence_operating))

(assert (! (= computed_liabilities_current_fy2025 (+ contract_with_customer_liability_current_fy2025 operating_lease_liability_current_fy2025 convertible_debt_current_fy2025 accounts_payable_and_other_accrued_liabilities_current_fy2025)) :named formula_liabilities))

(assert (! (or (> accounts_payable_and_other_accrued_liabilities_current_fy2025 0) (< accounts_payable_and_other_accrued_liabilities_current_fy2025 0)) :named denom_nonzero_accounts))
(assert (! (or (> contract_with_customer_liability_current_fy2025 0) (< contract_with_customer_liability_current_fy2025 0)) :named denom_nonzero_contract))
(assert (! (or (> convertible_debt_current_fy2025 0) (< convertible_debt_current_fy2025 0)) :named denom_nonzero_convertible))
(assert (! (or (> operating_lease_liability_current_fy2025 0) (< operating_lease_liability_current_fy2025 0)) :named denom_nonzero_operating))

(assert (! (<= (- computed_liabilities_current_fy2025 26631.0) 266.31) :named claim_upper))
(assert (! (<= (- 26631.0 computed_liabilities_current_fy2025) 266.31) :named claim_lower))

; EDGAR-companyfacts fact bindings (no calculation-linkbase constraints).
(declare-const xbrl_fact_us_gaap_AccountsPayableAndOtherAccruedLiabilitiesCurrent_instant_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_ContractWithCustomerLiabilityCurrent_instant_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_ConvertibleDebtCurrent_instant_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingLeaseLiabilityCurrent_instant_2026_01_31_unit_USD_dims_none Real)

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= contract_with_customer_liability_current_fy2025 xbrl_fact_us_gaap_ContractWithCustomerLiabilityCurrent_instant_2026_01_31_unit_USD_dims_none) :named xbrl_bind_contract_with_customer_liability_current_fy2025_edgar_2026_01_31_0001108524_26_000060))
(assert (! (= xbrl_fact_us_gaap_ContractWithCustomerLiabilityCurrent_instant_2026_01_31_unit_USD_dims_none 24317) :named xbrl_instance_contract_with_customer_liability_current_fy2025))
(assert (! (= operating_lease_liability_current_fy2025 xbrl_fact_us_gaap_OperatingLeaseLiabilityCurrent_instant_2026_01_31_unit_USD_dims_none) :named xbrl_bind_operating_lease_liability_current_fy2025_edgar_2026_01_31_0001108524_26_000060))
(assert (! (= xbrl_fact_us_gaap_OperatingLeaseLiabilityCurrent_instant_2026_01_31_unit_USD_dims_none 548) :named xbrl_instance_operating_lease_liability_current_fy2025))
(assert (! (= convertible_debt_current_fy2025 xbrl_fact_us_gaap_ConvertibleDebtCurrent_instant_2026_01_31_unit_USD_dims_none) :named xbrl_bind_convertible_debt_current_fy2025_edgar_2026_01_31_0001108524_26_000060))
(assert (! (= xbrl_fact_us_gaap_ConvertibleDebtCurrent_instant_2026_01_31_unit_USD_dims_none 4000) :named xbrl_instance_convertible_debt_current_fy2025))
(assert (! (= accounts_payable_and_other_accrued_liabilities_current_fy2025 xbrl_fact_us_gaap_AccountsPayableAndOtherAccruedLiabilitiesCurrent_instant_2026_01_31_unit_USD_dims_none) :named xbrl_bind_accounts_payable_and_other_accrued_liabilities_current_fy2025_edgar_2026_01_31_0001108524_26_000060))
(assert (! (= xbrl_fact_us_gaap_AccountsPayableAndOtherAccruedLiabilitiesCurrent_instant_2026_01_31_unit_USD_dims_none 8253) :named xbrl_instance_accounts_payable_and_other_accrued_liabilities_current_fy2025))

(check-sat)
(get-unsat-core)
(get-model)