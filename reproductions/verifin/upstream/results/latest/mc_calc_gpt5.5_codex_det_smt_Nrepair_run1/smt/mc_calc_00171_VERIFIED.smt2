(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_assets_current_fy2024 Real)
(declare-const accounts_receivable_net_current_fy2024 Real)
(declare-const cash_cash_equivalents_and_short_term_investments_fy2024 Real)
(declare-const other_assets_current_fy2024 Real)

(assert (! (= accounts_receivable_net_current_fy2024 52340) :named evidence_accounts_receivable_net_current_fy2024))
(assert (! (= cash_cash_equivalents_and_short_term_investments_fy2024 95657) :named evidence_cash_cash_equivalents_and_short_term_investments_fy2024))
(assert (! (= other_assets_current_fy2024 15714) :named evidence_other_assets_current_fy2024))

(assert (! (= computed_assets_current_fy2024 (+ cash_cash_equivalents_and_short_term_investments_fy2024 accounts_receivable_net_current_fy2024 other_assets_current_fy2024)) :named formula_assets_current_fy2024))

(assert (! (<= (- computed_assets_current_fy2024 163711) 163.71100000000001) :named claim_upper))
(assert (! (<= (- 163711 computed_assets_current_fy2024) 163.71100000000001) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccountsReceivableNetCurrent_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_AssetsCurrent_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_CashCashEquivalentsAndShortTermInvestments_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_MarketableSecuritiesCurrent_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2024_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_AssetsCurrent_instant_2024_12_31_unit_USD_dims_none 163711) :named evidence_xbrl_fact_us_gaap_AssetsCurrent_instant_2024_12_31_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2024_12_31_unit_USD_dims_none 23466) :named evidence_xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2024_12_31_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_MarketableSecuritiesCurrent_instant_2024_12_31_unit_USD_dims_none 72191) :named evidence_xbrl_fact_us_gaap_MarketableSecuritiesCurrent_instant_2024_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= cash_cash_equivalents_and_short_term_investments_fy2024 xbrl_fact_us_gaap_CashCashEquivalentsAndShortTermInvestments_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_cash_cash_equivalents_and_short_term_investments_fy2024_edgar_2024_12_31_0001652044_25_000014))
(assert (! (= xbrl_fact_us_gaap_CashCashEquivalentsAndShortTermInvestments_instant_2024_12_31_unit_USD_dims_none 95657) :named xbrl_instance_cash_cash_equivalents_and_short_term_investments_fy2024))
(assert (! (= accounts_receivable_net_current_fy2024 xbrl_fact_us_gaap_AccountsReceivableNetCurrent_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_accounts_receivable_net_current_fy2024_edgar_2024_12_31_0001652044_25_000014))
(assert (! (= xbrl_fact_us_gaap_AccountsReceivableNetCurrent_instant_2024_12_31_unit_USD_dims_none 52340) :named xbrl_instance_accounts_receivable_net_current_fy2024))
(assert (! (= other_assets_current_fy2024 xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_other_assets_current_fy2024_edgar_2024_12_31_0001652044_25_000014))
(assert (! (= xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2024_12_31_unit_USD_dims_none 15714) :named xbrl_instance_other_assets_current_fy2024))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_CashCashEquivalentsAndShortTermInvestments_instant_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_MarketableSecuritiesCurrent_instant_2024_12_31_unit_USD_dims_none)) 1.5) :named xbrl_calc_2_922715934_CashCashEquivalentsAndShortTermInvestments_c_9_upper))
(assert (! (>= (- xbrl_fact_us_gaap_CashCashEquivalentsAndShortTermInvestments_instant_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_MarketableSecuritiesCurrent_instant_2024_12_31_unit_USD_dims_none)) (- 1.5)) :named xbrl_calc_2_922715934_CashCashEquivalentsAndShortTermInvestments_c_9_lower))
(assert (! (<= (- xbrl_fact_us_gaap_AssetsCurrent_instant_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_CashCashEquivalentsAndShortTermInvestments_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccountsReceivableNetCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2024_12_31_unit_USD_dims_none)) 2) :named xbrl_calc_3_922715934_AssetsCurrent_c_9_upper))
(assert (! (>= (- xbrl_fact_us_gaap_AssetsCurrent_instant_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_CashCashEquivalentsAndShortTermInvestments_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccountsReceivableNetCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2024_12_31_unit_USD_dims_none)) (- 2)) :named xbrl_calc_3_922715934_AssetsCurrent_c_9_lower))

(check-sat)
(get-unsat-core)
(get-model)