(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_liabilities_current_fy2024 Real)
(declare-const accounts_payable_and_accrued_liabilities_current_fy2024 Real)
(declare-const accrued_income_taxes_current_fy2024 Real)
(declare-const long_term_debt_and_capital_lease_obligations_current_fy2024 Real)
(declare-const notes_and_loans_payable_fy2024 Real)

(assert (! (= accounts_payable_and_accrued_liabilities_current_fy2024 21715.0) :named evidence_accounts_payable_and_accrued_liabilities_current_fy2024))
(assert (! (= accrued_income_taxes_current_fy2024 1387.0) :named evidence_accrued_income_taxes_current_fy2024))
(assert (! (= long_term_debt_and_capital_lease_obligations_current_fy2024 648.0) :named evidence_long_term_debt_and_capital_lease_obligations_current_fy2024))
(assert (! (= notes_and_loans_payable_fy2024 1499.0) :named evidence_notes_and_loans_payable_fy2024))

(assert (! (= computed_liabilities_current_fy2024 (+ (+ accounts_payable_and_accrued_liabilities_current_fy2024 long_term_debt_and_capital_lease_obligations_current_fy2024) (+ accrued_income_taxes_current_fy2024 notes_and_loans_payable_fy2024))) :named formula_liabilities_current_fy2024))

(assert (! (or (> notes_and_loans_payable_fy2024 0) (< notes_and_loans_payable_fy2024 0)) :named denom_nonzero))
(assert (! (or (> long_term_debt_and_capital_lease_obligations_current_fy2024 0) (< long_term_debt_and_capital_lease_obligations_current_fy2024 0)) :named denom_nonzero2))

(assert (! (<= (- computed_liabilities_current_fy2024 23571.0) 235.71) :named claim_upper))
(assert (! (<= (- 23571.0 computed_liabilities_current_fy2024) 235.71) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccountsPayableAndAccruedLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_AccruedIncomeTaxesCurrent_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LongTermDebtAndCapitalLeaseObligationsCurrent_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_NotesAndLoansPayable_instant_2024_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none 25249) :named evidence_xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= notes_and_loans_payable_fy2024 xbrl_fact_us_gaap_NotesAndLoansPayable_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_notes_and_loans_payable_fy2024_edgar_2024_12_31_0000021344_25_000011))
(assert (! (= xbrl_fact_us_gaap_NotesAndLoansPayable_instant_2024_12_31_unit_USD_dims_none 1499) :named xbrl_instance_notes_and_loans_payable_fy2024))
(assert (! (= accounts_payable_and_accrued_liabilities_current_fy2024 xbrl_fact_us_gaap_AccountsPayableAndAccruedLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_accounts_payable_and_accrued_liabilities_current_fy2024_edgar_2024_12_31_0000021344_25_000011))
(assert (! (= xbrl_fact_us_gaap_AccountsPayableAndAccruedLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none 21715) :named xbrl_instance_accounts_payable_and_accrued_liabilities_current_fy2024))
(assert (! (= long_term_debt_and_capital_lease_obligations_current_fy2024 xbrl_fact_us_gaap_LongTermDebtAndCapitalLeaseObligationsCurrent_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_long_term_debt_and_capital_lease_obligations_current_fy2024_edgar_2024_12_31_0000021344_25_000011))
(assert (! (= xbrl_fact_us_gaap_LongTermDebtAndCapitalLeaseObligationsCurrent_instant_2024_12_31_unit_USD_dims_none 648) :named xbrl_instance_long_term_debt_and_capital_lease_obligations_current_fy2024))
(assert (! (= accrued_income_taxes_current_fy2024 xbrl_fact_us_gaap_AccruedIncomeTaxesCurrent_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_accrued_income_taxes_current_fy2024_edgar_2024_12_31_0000021344_25_000011))
(assert (! (= xbrl_fact_us_gaap_AccruedIncomeTaxesCurrent_instant_2024_12_31_unit_USD_dims_none 1387) :named xbrl_instance_accrued_income_taxes_current_fy2024))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_AccountsPayableAndAccruedLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_NotesAndLoansPayable_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_LongTermDebtAndCapitalLeaseObligationsCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccruedIncomeTaxesCurrent_instant_2024_12_31_unit_USD_dims_none)) 2.5) :named xbrl_calc_8_831632951_LiabilitiesCurrent_c_28_upper))
(assert (! (>= (- xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_AccountsPayableAndAccruedLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_NotesAndLoansPayable_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_LongTermDebtAndCapitalLeaseObligationsCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccruedIncomeTaxesCurrent_instant_2024_12_31_unit_USD_dims_none)) (- 2.5)) :named xbrl_calc_8_831632951_LiabilitiesCurrent_c_28_lower))

(check-sat)
(get-unsat-core)
(get-model)