(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_liabilities_current_fy2024 Real)
(declare-const accounts_payable_current_fy2024 Real)
(declare-const accrued_income_taxes_current_fy2024 Real)
(declare-const debt_current_fy2024 Real)
(declare-const dividends_payable_current_fy2024 Real)
(declare-const other_liabilities_current_fy2024 Real)

(assert (! (= accounts_payable_current_fy2024 4079) :named evidence_accounts_payable_current_fy2024))
(assert (! (= accrued_income_taxes_current_fy2024 3914) :named evidence_accrued_income_taxes_current_fy2024))
(assert (! (= debt_current_fy2024 2649) :named evidence_debt_current_fy2024))
(assert (! (= dividends_payable_current_fy2024 2084) :named evidence_dividends_payable_current_fy2024))
(assert (! (= other_liabilities_current_fy2024 15694) :named evidence_other_liabilities_current_fy2024))

(assert (! (= computed_liabilities_current_fy2024 (+ debt_current_fy2024 accounts_payable_current_fy2024 other_liabilities_current_fy2024 accrued_income_taxes_current_fy2024 dividends_payable_current_fy2024)) :named formula_liabilities_current_fy2024))

(assert (! (<= (- computed_liabilities_current_fy2024 28420) 28.420000000000002) :named claim_upper))
(assert (! (<= (- 28420 computed_liabilities_current_fy2024) 28.420000000000002) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_AccruedIncomeTaxesCurrent_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_DebtCurrent_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_DividendsPayableCurrent_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none 28420) :named evidence_xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= debt_current_fy2024 xbrl_fact_us_gaap_DebtCurrent_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_debt_current_fy2024_edgar_2024_12_31_0001628280_25_007732))
(assert (! (= xbrl_fact_us_gaap_DebtCurrent_instant_2024_12_31_unit_USD_dims_none 2649) :named xbrl_instance_debt_current_fy2024))
(assert (! (= accounts_payable_current_fy2024 xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_accounts_payable_current_fy2024_edgar_2024_12_31_0001628280_25_007732))
(assert (! (= xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2024_12_31_unit_USD_dims_none 4079) :named xbrl_instance_accounts_payable_current_fy2024))
(assert (! (= other_liabilities_current_fy2024 xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_other_liabilities_current_fy2024_edgar_2024_12_31_0001628280_25_007732))
(assert (! (= xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none 15694) :named xbrl_instance_other_liabilities_current_fy2024))
(assert (! (= accrued_income_taxes_current_fy2024 xbrl_fact_us_gaap_AccruedIncomeTaxesCurrent_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_accrued_income_taxes_current_fy2024_edgar_2024_12_31_0001628280_25_007732))
(assert (! (= xbrl_fact_us_gaap_AccruedIncomeTaxesCurrent_instant_2024_12_31_unit_USD_dims_none 3914) :named xbrl_instance_accrued_income_taxes_current_fy2024))
(assert (! (= dividends_payable_current_fy2024 xbrl_fact_us_gaap_DividendsPayableCurrent_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_dividends_payable_current_fy2024_edgar_2024_12_31_0001628280_25_007732))
(assert (! (= xbrl_fact_us_gaap_DividendsPayableCurrent_instant_2024_12_31_unit_USD_dims_none 2084) :named xbrl_instance_dividends_payable_current_fy2024))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_DebtCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccruedIncomeTaxesCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_DividendsPayableCurrent_instant_2024_12_31_unit_USD_dims_none)) 3) :named xbrl_calc_6_514495634_LiabilitiesCurrent_c_14_upper))
(assert (! (>= (- xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_DebtCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccruedIncomeTaxesCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_DividendsPayableCurrent_instant_2024_12_31_unit_USD_dims_none)) (- 3)) :named xbrl_calc_6_514495634_LiabilitiesCurrent_c_14_lower))

(check-sat)
(get-unsat-core)
(get-model)