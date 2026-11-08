(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_assets_current_fy2025 Real)
(declare-const accounts_receivable_net_current_fy2025 Real)
(declare-const cash_and_cash_equivalents_at_carrying_value_fy2025 Real)
(declare-const inventory_net_fy2025 Real)
(declare-const marketable_securities_current_fy2025 Real)
(declare-const other_assets_current_fy2025 Real)

(assert (! (= accounts_receivable_net_current_fy2025 11775) :named evidence_accounts_receivable_net_current_fy2025))
(assert (! (= cash_and_cash_equivalents_at_carrying_value_fy2025 14565) :named evidence_cash_and_cash_equivalents_at_carrying_value_fy2025))
(assert (! (= inventory_net_fy2025 6658) :named evidence_inventory_net_fy2025))
(assert (! (= marketable_securities_current_fy2025 0) :named evidence_marketable_securities_current_fy2025))
(assert (! (= other_assets_current_fy2025 10518) :named evidence_other_assets_current_fy2025))

(assert (! (= computed_assets_current_fy2025 (+ cash_and_cash_equivalents_at_carrying_value_fy2025 marketable_securities_current_fy2025 other_assets_current_fy2025 accounts_receivable_net_current_fy2025 inventory_net_fy2025)) :named formula_assets_current_fy2025))

(assert (! (<= (- computed_assets_current_fy2025 43516) 43.515999999999998) :named claim_upper))
(assert (! (<= (- 43516 computed_assets_current_fy2025) 43.515999999999998) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_mrk_InventoryNetAndInventoryNoncurrent_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_AccountsReceivableNetCurrent_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_AssetsCurrent_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_InventoryNet_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_InventoryNoncurrent_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_MarketableSecuritiesCurrent_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2025_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_mrk_InventoryNetAndInventoryNoncurrent_instant_2025_12_31_unit_USD_dims_none 12339) :named evidence_xbrl_fact_mrk_InventoryNetAndInventoryNoncurrent_instant_2025_12_31_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_AssetsCurrent_instant_2025_12_31_unit_USD_dims_none 43516) :named evidence_xbrl_fact_us_gaap_AssetsCurrent_instant_2025_12_31_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_InventoryNoncurrent_instant_2025_12_31_unit_USD_dims_none 5681) :named evidence_xbrl_fact_us_gaap_InventoryNoncurrent_instant_2025_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= cash_and_cash_equivalents_at_carrying_value_fy2025 xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_cash_and_cash_equivalents_at_carrying_value_fy2025_edgar_2025_12_31_0000310158_26_000063))
(assert (! (= xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2025_12_31_unit_USD_dims_none 14565) :named xbrl_instance_cash_and_cash_equivalents_at_carrying_value_fy2025))
(assert (! (= marketable_securities_current_fy2025 xbrl_fact_us_gaap_MarketableSecuritiesCurrent_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_marketable_securities_current_fy2025_edgar_2025_12_31_0000310158_26_000063))
(assert (! (= xbrl_fact_us_gaap_MarketableSecuritiesCurrent_instant_2025_12_31_unit_USD_dims_none 0) :named xbrl_instance_marketable_securities_current_fy2025))
(assert (! (= other_assets_current_fy2025 xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_other_assets_current_fy2025_edgar_2025_12_31_0000310158_26_000063))
(assert (! (= xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2025_12_31_unit_USD_dims_none 10518) :named xbrl_instance_other_assets_current_fy2025))
(assert (! (= accounts_receivable_net_current_fy2025 xbrl_fact_us_gaap_AccountsReceivableNetCurrent_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_accounts_receivable_net_current_fy2025_edgar_2025_12_31_0000310158_26_000063))
(assert (! (= xbrl_fact_us_gaap_AccountsReceivableNetCurrent_instant_2025_12_31_unit_USD_dims_none 11775) :named xbrl_instance_accounts_receivable_net_current_fy2025))
(assert (! (= inventory_net_fy2025 xbrl_fact_us_gaap_InventoryNet_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_inventory_net_fy2025_edgar_2025_12_31_0000310158_26_000063))
(assert (! (= xbrl_fact_us_gaap_InventoryNet_instant_2025_12_31_unit_USD_dims_none 6658) :named xbrl_instance_inventory_net_fy2025))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_AssetsCurrent_instant_2025_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_MarketableSecuritiesCurrent_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccountsReceivableNetCurrent_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_InventoryNet_instant_2025_12_31_unit_USD_dims_none)) 3) :named xbrl_calc_8_514495634_AssetsCurrent_c_14_upper))
(assert (! (>= (- xbrl_fact_us_gaap_AssetsCurrent_instant_2025_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_MarketableSecuritiesCurrent_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccountsReceivableNetCurrent_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_InventoryNet_instant_2025_12_31_unit_USD_dims_none)) (- 3)) :named xbrl_calc_8_514495634_AssetsCurrent_c_14_lower))
(assert (! (<= (- xbrl_fact_mrk_InventoryNetAndInventoryNoncurrent_instant_2025_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_InventoryNet_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_InventoryNoncurrent_instant_2025_12_31_unit_USD_dims_none)) 1.5) :named xbrl_calc_31_730307604_InventoryNetAndInventoryNoncurrent_c_14_upper))
(assert (! (>= (- xbrl_fact_mrk_InventoryNetAndInventoryNoncurrent_instant_2025_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_InventoryNet_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_InventoryNoncurrent_instant_2025_12_31_unit_USD_dims_none)) (- 1.5)) :named xbrl_calc_31_730307604_InventoryNetAndInventoryNoncurrent_c_14_lower))

(check-sat)
(get-unsat-core)
(get-model)