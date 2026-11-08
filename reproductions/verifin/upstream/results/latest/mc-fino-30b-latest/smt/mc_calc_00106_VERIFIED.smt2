(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_liabilities_current_fy2025 Real)
(declare-const accounts_payable_current_fy2025 Real)
(declare-const accrued_income_taxes_current_fy2025 Real)
(declare-const debt_current_fy2025 Real)
(declare-const dividends_payable_current_fy2025 Real)
(declare-const other_liabilities_current_fy2025 Real)

(assert (! (= accounts_payable_current_fy2025 4404) :named evidence_accounts_payable_current_fy2025))
(assert (! (= accrued_income_taxes_current_fy2025 4726) :named evidence_accrued_income_taxes_current_fy2025))
(assert (! (= debt_current_fy2025 2589) :named evidence_debt_current_fy2025))
(assert (! (= dividends_payable_current_fy2025 2140) :named evidence_dividends_payable_current_fy2025))
(assert (! (= other_liabilities_current_fy2025 14468) :named evidence_other_liabilities_current_fy2025))

(assert (! (= computed_liabilities_current_fy2025 (+ debt_current_fy2025 accounts_payable_current_fy2025 other_liabilities_current_fy2025 accrued_income_taxes_current_fy2025 dividends_payable_current_fy2025)) :named formula_liabilities_current_fy2025))

(assert (! (<= (- computed_liabilities_current_fy2025 28327) 28.327000000000002) :named claim_upper))
(assert (! (<= (- 28327 computed_liabilities_current_fy2025) 28.327000000000002) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_AccruedIncomeTaxesCurrent_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_DebtCurrent_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_DividendsPayableCurrent_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none 28327) :named evidence_xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= debt_current_fy2025 xbrl_fact_us_gaap_DebtCurrent_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_debt_current_fy2025_edgar_2025_12_31_0000310158_26_000063))
(assert (! (= xbrl_fact_us_gaap_DebtCurrent_instant_2025_12_31_unit_USD_dims_none 2589) :named xbrl_instance_debt_current_fy2025))
(assert (! (= accounts_payable_current_fy2025 xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_accounts_payable_current_fy2025_edgar_2025_12_31_0000310158_26_000063))
(assert (! (= xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_12_31_unit_USD_dims_none 4404) :named xbrl_instance_accounts_payable_current_fy2025))
(assert (! (= other_liabilities_current_fy2025 xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_other_liabilities_current_fy2025_edgar_2025_12_31_0000310158_26_000063))
(assert (! (= xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none 14468) :named xbrl_instance_other_liabilities_current_fy2025))
(assert (! (= accrued_income_taxes_current_fy2025 xbrl_fact_us_gaap_AccruedIncomeTaxesCurrent_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_accrued_income_taxes_current_fy2025_edgar_2025_12_31_0000310158_26_000063))
(assert (! (= xbrl_fact_us_gaap_AccruedIncomeTaxesCurrent_instant_2025_12_31_unit_USD_dims_none 4726) :named xbrl_instance_accrued_income_taxes_current_fy2025))
(assert (! (= dividends_payable_current_fy2025 xbrl_fact_us_gaap_DividendsPayableCurrent_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_dividends_payable_current_fy2025_edgar_2025_12_31_0000310158_26_000063))
(assert (! (= xbrl_fact_us_gaap_DividendsPayableCurrent_instant_2025_12_31_unit_USD_dims_none 2140) :named xbrl_instance_dividends_payable_current_fy2025))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_DebtCurrent_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccruedIncomeTaxesCurrent_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_DividendsPayableCurrent_instant_2025_12_31_unit_USD_dims_none)) 3) :named xbrl_calc_9_514495634_LiabilitiesCurrent_c_14_upper))
(assert (! (>= (- xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_DebtCurrent_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccruedIncomeTaxesCurrent_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_DividendsPayableCurrent_instant_2025_12_31_unit_USD_dims_none)) (- 3)) :named xbrl_calc_9_514495634_LiabilitiesCurrent_c_14_lower))

(check-sat)
(get-unsat-core)
(get-model)