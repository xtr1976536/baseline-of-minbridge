(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_liabilities_current_fy2023 Real)
(declare-const accounts_payable_current_fy2023 Real)
(declare-const accrued_income_taxes_current_fy2023 Real)
(declare-const debt_current_fy2023 Real)
(declare-const dividends_payable_current_fy2023 Real)
(declare-const other_liabilities_current_fy2023 Real)

(assert (! (= accounts_payable_current_fy2023 3922) :named evidence_accounts_payable_current_fy2023))
(assert (! (= accrued_income_taxes_current_fy2023 2649) :named evidence_accrued_income_taxes_current_fy2023))
(assert (! (= debt_current_fy2023 1372) :named evidence_debt_current_fy2023))
(assert (! (= dividends_payable_current_fy2023 1985) :named evidence_dividends_payable_current_fy2023))
(assert (! (= other_liabilities_current_fy2023 15766) :named evidence_other_liabilities_current_fy2023))

(assert (! (= computed_liabilities_current_fy2023 (+ debt_current_fy2023 accounts_payable_current_fy2023 other_liabilities_current_fy2023 accrued_income_taxes_current_fy2023 dividends_payable_current_fy2023)) :named formula_liabilities_current_fy2023))

(assert (! (<= (- computed_liabilities_current_fy2023 25694) 25.693999999999999) :named claim_upper))
(assert (! (<= (- 25694 computed_liabilities_current_fy2023) 25.693999999999999) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2023_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_AccruedIncomeTaxesCurrent_instant_2023_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_DebtCurrent_instant_2023_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_DividendsPayableCurrent_instant_2023_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none 25694) :named evidence_xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= debt_current_fy2023 xbrl_fact_us_gaap_DebtCurrent_instant_2023_12_31_unit_USD_dims_none) :named xbrl_bind_debt_current_fy2023_edgar_2023_12_31_0001628280_24_006850))
(assert (! (= xbrl_fact_us_gaap_DebtCurrent_instant_2023_12_31_unit_USD_dims_none 1372) :named xbrl_instance_debt_current_fy2023))
(assert (! (= accounts_payable_current_fy2023 xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2023_12_31_unit_USD_dims_none) :named xbrl_bind_accounts_payable_current_fy2023_edgar_2023_12_31_0001628280_24_006850))
(assert (! (= xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2023_12_31_unit_USD_dims_none 3922) :named xbrl_instance_accounts_payable_current_fy2023))
(assert (! (= other_liabilities_current_fy2023 xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none) :named xbrl_bind_other_liabilities_current_fy2023_edgar_2023_12_31_0001628280_24_006850))
(assert (! (= xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none 15766) :named xbrl_instance_other_liabilities_current_fy2023))
(assert (! (= accrued_income_taxes_current_fy2023 xbrl_fact_us_gaap_AccruedIncomeTaxesCurrent_instant_2023_12_31_unit_USD_dims_none) :named xbrl_bind_accrued_income_taxes_current_fy2023_edgar_2023_12_31_0001628280_24_006850))
(assert (! (= xbrl_fact_us_gaap_AccruedIncomeTaxesCurrent_instant_2023_12_31_unit_USD_dims_none 2649) :named xbrl_instance_accrued_income_taxes_current_fy2023))
(assert (! (= dividends_payable_current_fy2023 xbrl_fact_us_gaap_DividendsPayableCurrent_instant_2023_12_31_unit_USD_dims_none) :named xbrl_bind_dividends_payable_current_fy2023_edgar_2023_12_31_0001628280_24_006850))
(assert (! (= xbrl_fact_us_gaap_DividendsPayableCurrent_instant_2023_12_31_unit_USD_dims_none 1985) :named xbrl_instance_dividends_payable_current_fy2023))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_DebtCurrent_instant_2023_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2023_12_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccruedIncomeTaxesCurrent_instant_2023_12_31_unit_USD_dims_none xbrl_fact_us_gaap_DividendsPayableCurrent_instant_2023_12_31_unit_USD_dims_none)) 3) :named xbrl_calc_10_514495634_LiabilitiesCurrent_c_10_upper))
(assert (! (>= (- xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_DebtCurrent_instant_2023_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccountsPayableCurrent_instant_2023_12_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherLiabilitiesCurrent_instant_2023_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccruedIncomeTaxesCurrent_instant_2023_12_31_unit_USD_dims_none xbrl_fact_us_gaap_DividendsPayableCurrent_instant_2023_12_31_unit_USD_dims_none)) (- 3)) :named xbrl_calc_10_514495634_LiabilitiesCurrent_c_10_lower))

(check-sat)
(get-unsat-core)
(get-model)