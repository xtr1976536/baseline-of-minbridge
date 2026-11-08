(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_assets_current_fy2026 Real)
(declare-const accounts_receivable_net_current_fy2026 Real)
(declare-const cash_and_cash_equivalents_at_carrying_value_fy2026 Real)
(declare-const inventory_net_fy2026 Real)
(declare-const other_assets_current_fy2026 Real)

(assert (! (= accounts_receivable_net_current_fy2026 5597) :named evidence_accounts_receivable_net_current_fy2026))
(assert (! (= cash_and_cash_equivalents_at_carrying_value_fy2026 1389) :named evidence_cash_and_cash_equivalents_at_carrying_value_fy2026))
(assert (! (= inventory_net_fy2026 25817) :named evidence_inventory_net_fy2026))
(assert (! (= other_assets_current_fy2026 1588) :named evidence_other_assets_current_fy2026))

(assert (! (= computed_assets_current_fy2026 (+ cash_and_cash_equivalents_at_carrying_value_fy2026 accounts_receivable_net_current_fy2026 inventory_net_fy2026 other_assets_current_fy2026)) :named formula_assets_current_fy2026))

(assert (! (<= (- computed_assets_current_fy2026 34391) 34.390999999999998) :named claim_upper))
(assert (! (<= (- 34391 computed_assets_current_fy2026) 34.390999999999998) :named claim_lower))

; XBRL calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccountsReceivableNetCurrent_instant_2026_02_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_AssetsCurrent_instant_2026_02_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2026_02_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_InventoryNet_instant_2026_02_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2026_02_01_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_AssetsCurrent_instant_2026_02_01_unit_USD_dims_none 34391) :named evidence_xbrl_fact_us_gaap_AssetsCurrent_instant_2026_02_01_unit_USD_dims_none))

; IR-to-XBRL bindings and independent instance-value witnesses.
(assert (! (= cash_and_cash_equivalents_at_carrying_value_fy2026 xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2026_02_01_unit_USD_dims_none) :named xbrl_bind_cash_and_cash_equivalents_at_carrying_value_fy2026_c_4))
(assert (! (= xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2026_02_01_unit_USD_dims_none 1389) :named xbrl_instance_cash_and_cash_equivalents_at_carrying_value_fy2026))
(assert (! (= accounts_receivable_net_current_fy2026 xbrl_fact_us_gaap_AccountsReceivableNetCurrent_instant_2026_02_01_unit_USD_dims_none) :named xbrl_bind_accounts_receivable_net_current_fy2026_c_4))
(assert (! (= xbrl_fact_us_gaap_AccountsReceivableNetCurrent_instant_2026_02_01_unit_USD_dims_none 5597) :named xbrl_instance_accounts_receivable_net_current_fy2026))
(assert (! (= inventory_net_fy2026 xbrl_fact_us_gaap_InventoryNet_instant_2026_02_01_unit_USD_dims_none) :named xbrl_bind_inventory_net_fy2026_c_4))
(assert (! (= xbrl_fact_us_gaap_InventoryNet_instant_2026_02_01_unit_USD_dims_none 25817) :named xbrl_instance_inventory_net_fy2026))
(assert (! (= other_assets_current_fy2026 xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2026_02_01_unit_USD_dims_none) :named xbrl_bind_other_assets_current_fy2026_c_4))
(assert (! (= xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2026_02_01_unit_USD_dims_none 1588) :named xbrl_instance_other_assets_current_fy2026))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_AssetsCurrent_instant_2026_02_01_unit_USD_dims_none (+ xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2026_02_01_unit_USD_dims_none xbrl_fact_us_gaap_AccountsReceivableNetCurrent_instant_2026_02_01_unit_USD_dims_none xbrl_fact_us_gaap_InventoryNet_instant_2026_02_01_unit_USD_dims_none xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2026_02_01_unit_USD_dims_none)) 2.5) :named xbrl_calc_4_591064512_AssetsCurrent_c_4_upper))
(assert (! (>= (- xbrl_fact_us_gaap_AssetsCurrent_instant_2026_02_01_unit_USD_dims_none (+ xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2026_02_01_unit_USD_dims_none xbrl_fact_us_gaap_AccountsReceivableNetCurrent_instant_2026_02_01_unit_USD_dims_none xbrl_fact_us_gaap_InventoryNet_instant_2026_02_01_unit_USD_dims_none xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2026_02_01_unit_USD_dims_none)) (- 2.5)) :named xbrl_calc_4_591064512_AssetsCurrent_c_4_lower))

(check-sat)
(get-unsat-core)
(get-model)