(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_assets_current_fy2024 Real)
(declare-const accounts_receivable_net_current_fy2024 Real)
(declare-const cash_and_cash_equivalents_at_carrying_value_fy2024 Real)
(declare-const inventory_net_fy2024 Real)
(declare-const marketable_securities_current_fy2024 Real)
(declare-const other_assets_current_fy2024 Real)

(assert (! (= accounts_receivable_net_current_fy2024 10278) :named evidence_accounts_receivable_net_current_fy2024))
(assert (! (= cash_and_cash_equivalents_at_carrying_value_fy2024 13242) :named evidence_cash_and_cash_equivalents_at_carrying_value_fy2024))
(assert (! (= inventory_net_fy2024 6109) :named evidence_inventory_net_fy2024))
(assert (! (= marketable_securities_current_fy2024 447) :named evidence_marketable_securities_current_fy2024))
(assert (! (= other_assets_current_fy2024 8706) :named evidence_other_assets_current_fy2024))

(assert (! (= computed_assets_current_fy2024 (+ cash_and_cash_equivalents_at_carrying_value_fy2024 marketable_securities_current_fy2024 other_assets_current_fy2024 accounts_receivable_net_current_fy2024 inventory_net_fy2024)) :named formula_assets_current_fy2024))

(assert (! (<= (- computed_assets_current_fy2024 38782) 38.782000000000004) :named claim_upper))
(assert (! (<= (- 38782 computed_assets_current_fy2024) 38.782000000000004) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_mrk_InventoryNetAndInventoryNoncurrent_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_AccountsReceivableNetCurrent_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_AssetsCurrent_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_InventoryNet_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_InventoryNoncurrent_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_MarketableSecuritiesCurrent_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2024_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_mrk_InventoryNetAndInventoryNoncurrent_instant_2024_12_31_unit_USD_dims_none 10302) :named evidence_xbrl_fact_mrk_InventoryNetAndInventoryNoncurrent_instant_2024_12_31_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_AssetsCurrent_instant_2024_12_31_unit_USD_dims_none 38782) :named evidence_xbrl_fact_us_gaap_AssetsCurrent_instant_2024_12_31_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_InventoryNoncurrent_instant_2024_12_31_unit_USD_dims_none 4193) :named evidence_xbrl_fact_us_gaap_InventoryNoncurrent_instant_2024_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= cash_and_cash_equivalents_at_carrying_value_fy2024 xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_cash_and_cash_equivalents_at_carrying_value_fy2024_edgar_2024_12_31_0001628280_25_007732))
(assert (! (= xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2024_12_31_unit_USD_dims_none 13242) :named xbrl_instance_cash_and_cash_equivalents_at_carrying_value_fy2024))
(assert (! (= marketable_securities_current_fy2024 xbrl_fact_us_gaap_MarketableSecuritiesCurrent_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_marketable_securities_current_fy2024_edgar_2024_12_31_0001628280_25_007732))
(assert (! (= xbrl_fact_us_gaap_MarketableSecuritiesCurrent_instant_2024_12_31_unit_USD_dims_none 447) :named xbrl_instance_marketable_securities_current_fy2024))
(assert (! (= other_assets_current_fy2024 xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_other_assets_current_fy2024_edgar_2024_12_31_0001628280_25_007732))
(assert (! (= xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2024_12_31_unit_USD_dims_none 8706) :named xbrl_instance_other_assets_current_fy2024))
(assert (! (= accounts_receivable_net_current_fy2024 xbrl_fact_us_gaap_AccountsReceivableNetCurrent_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_accounts_receivable_net_current_fy2024_edgar_2024_12_31_0001628280_25_007732))
(assert (! (= xbrl_fact_us_gaap_AccountsReceivableNetCurrent_instant_2024_12_31_unit_USD_dims_none 10278) :named xbrl_instance_accounts_receivable_net_current_fy2024))
(assert (! (= inventory_net_fy2024 xbrl_fact_us_gaap_InventoryNet_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_inventory_net_fy2024_edgar_2024_12_31_0001628280_25_007732))
(assert (! (= xbrl_fact_us_gaap_InventoryNet_instant_2024_12_31_unit_USD_dims_none 6109) :named xbrl_instance_inventory_net_fy2024))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_AssetsCurrent_instant_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_MarketableSecuritiesCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccountsReceivableNetCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_InventoryNet_instant_2024_12_31_unit_USD_dims_none)) 3) :named xbrl_calc_12_514495634_AssetsCurrent_c_14_upper))
(assert (! (>= (- xbrl_fact_us_gaap_AssetsCurrent_instant_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_MarketableSecuritiesCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccountsReceivableNetCurrent_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_InventoryNet_instant_2024_12_31_unit_USD_dims_none)) (- 3)) :named xbrl_calc_12_514495634_AssetsCurrent_c_14_lower))
(assert (! (<= (- xbrl_fact_mrk_InventoryNetAndInventoryNoncurrent_instant_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_InventoryNet_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_InventoryNoncurrent_instant_2024_12_31_unit_USD_dims_none)) 1.5) :named xbrl_calc_31_844988216_InventoryNetAndInventoryNoncurrent_c_14_upper))
(assert (! (>= (- xbrl_fact_mrk_InventoryNetAndInventoryNoncurrent_instant_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_InventoryNet_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_InventoryNoncurrent_instant_2024_12_31_unit_USD_dims_none)) (- 1.5)) :named xbrl_calc_31_844988216_InventoryNetAndInventoryNoncurrent_c_14_lower))

(check-sat)
(get-unsat-core)
(get-model)