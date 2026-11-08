(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_liabilities_current_fy2024 Real)
(declare-const accounts_payable_current_fy2024 Real)
(declare-const accrued_income_taxes_current_fy2024 Real)
(declare-const employee_related_liabilities_current_fy2024 Real)
(declare-const long_term_debt_current_fy2024 Real)
(declare-const other_liabilities_current_fy2024 Real)

(assert (! (= accounts_payable_current_fy2024 820.0) :named evidence_accounts_payable_current_fy2024))
(assert (! (= accrued_income_taxes_current_fy2024 159.0) :named evidence_accrued_income_taxes_current_fy2024))
(assert (! (= employee_related_liabilities_current_fy2024 839.0) :named evidence_employee_related_liabilities_current_fy2024))
(assert (! (= long_term_debt_current_fy2024 750.0) :named evidence_long_term_debt_current_fy2024))
(assert (! (= other_liabilities_current_fy2024 1075.0) :named evidence_other_liabilities_current_fy2024))

(assert (! (= computed_liabilities_current_fy2024 (+ long_term_debt_current_fy2024 accounts_payable_current_fy2024 employee_related_liabilities_current_fy2024 accrued_income_taxes_current_fy2024 other_liabilities_current_fy2024)) :named formula_liabilities_current_fy2024))

(assert (! (or (> other_liabilities_current_fy2024 0) (< other_liabilities_current_fy2024 0)) :named denom_nonzero))
(assert (! (or (> accounts_payable_current_fy2024 0) (< accounts_payable_current_fy2024 0)) :named denom_accounts_payable_nonzero))
(assert (! (or (> accrued_income_taxes_current_fy2024 0) (< accrued_income_taxes_current_fy2024 0)) :named denom_accrued_income_taxes_nonzero))
(assert (! (or (> employee_related_liabilities_current_fy2024 0) (< employee_related_liabilities_current_fy2024 0)) :named denom_employee_related_liabilities_nonzero))
(assert (! (or (> long_term_debt_current_fy2024 0) (< long_term_debt_current_fy2024 0)) :named denom_long_term_debt_nonzero))

(assert (! (<= (- computed_liabilities_current_fy2024 3320.0) 33.2) :named claim_upper))
(assert (! (<= (- 3320.0 computed_liabilities_current_fy2024) 33.2) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_txn_AccruedConstructionRetainageCurrent_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_AccruedIncomeTaxesCurrent_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LongTermDebtCurrent_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LongTermDebtNoncurrent_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LongTermDebt_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherSundryLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_txn_AccruedConstructionRetainageCurrent_instant_2024_12_31_unit_USD_dims_none 352) :named evidence_xbrl_fact_txn_AccruedConstructionRetainageCurrent_instant_2024_12_31_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none 3643) :named evidence_xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_LongTermDebtNoncurrent_instant_2024_12_31_unit_USD_dims_none 12846) :named evidence_xbrl_fact_us_gaap_LongTermDebtNoncurrent_instant_2024_12_31_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_LongTermDebt_instant_2024_12_31_unit_USD_dims_none 13600) :named evidence_xbrl_fact_us_gaap_LongTermDebt_instant_2024_12_31_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_OtherSundryLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none 723) :named evidence_xbrl_fact_us_gaap_OtherSundryLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= accounts_payable_current_fy2024 xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_accounts_payable_current_fy2024_edgar_2024_12_31_0000097476_25_000007))
(assert (! (= xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2024_12_31_unit_USD_dims_none 820) :named xbrl_instance_accounts_payable_current_fy2024))
(assert (! (= long_term_debt_current_fy2024 xbrl_fact_us_gaap_LongTermDebtCurrent_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_long_term_debt_current_fy2024_edgar_2024_12_31_0000097476_25_000007))
(assert (! (= xbrl_fact_us_gaap_LongTermDebtCurrent_instant_2024_12_31_unit_USD_dims_none 750) :named xbrl_instance_long_term_debt_current_fy2024))
(assert (! (= employee_related_liabilities_current_fy2024 xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_employee_related_liabilities_current_fy2024_edgar_2024_12_31_0000097476_25_000007))
(assert (! (= xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none 839) :named xbrl_instance_employee_related_liabilities_current_fy2024))
(assert (! (= accrued_income_taxes_current_fy2024 xbrl_fact_us_gaap_AccruedIncomeTaxesCurrent_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_accrued_income_taxes_current_fy2024_edgar_2024_12_31_0000097476_25_000007))
(assert (! (= xbrl_fact_us_gaap_AccruedIncomeTaxesCurrent_instant_2024_12_31_unit_USD_dims_none 159) :named xbrl_instance_accrued_income_taxes_current_fy2024))
(assert (! (= other_liabilities_current_fy2024 xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_other_liabilities_current_fy2024_edgar_2024_12_31_0000097476_25_000007))
(assert (! (= xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none 1075) :named xbrl_instance_other_liabilities_current_fy2024))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_LongTermDebtCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccruedIncomeTaxesCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none)) 3) :named xbrl_calc_14_569867223_LiabilitiesCurrent_c_6_upper))
(assert (! (>= (- xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_LongTermDebtCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_EmployeeRelatedLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccruedIncomeTaxesCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none)) (- 3)) :named xbrl_calc_14_569867223_LiabilitiesCurrent_c_6_lower))
(assert (! (<= (- xbrl_fact_us_gaap_LongTermDebt_instant_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_LongTermDebtCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_LongTermDebtNoncurrent_instant_2024_12_31_unit_USD_dims_none)) 6) :named xbrl_calc_42_713236993_LongTermDebt_c_6_upper))
(assert (! (>= (- xbrl_fact_us_gaap_LongTermDebt_instant_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_LongTermDebtCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_LongTermDebtNoncurrent_instant_2024_12_31_unit_USD_dims_none)) (- 6)) :named xbrl_calc_42_713236993_LongTermDebt_c_6_lower))
(assert (! (<= (- xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none (+ xbrl_fact_txn_AccruedConstructionRetainageCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherSundryLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none)) 1.5) :named xbrl_calc_49_625331665_OtherLiabilitiesCurrent_c_6_upper))
(assert (! (>= (- xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none (+ xbrl_fact_txn_AccruedConstructionRetainageCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherSundryLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none)) (- 1.5)) :named xbrl_calc_49_625331665_OtherLiabilitiesCurrent_c_6_lower))

(check-sat)
(get-unsat-core)
(get-model)