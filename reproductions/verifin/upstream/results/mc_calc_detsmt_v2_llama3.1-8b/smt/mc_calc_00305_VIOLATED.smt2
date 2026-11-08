(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_assets_current_fy2024 Real)
(declare-const cash_and_cash_equivalents_at_carrying_value_fy2024 Real)
(declare-const inventory_net_fy2024 Real)
(declare-const other_assets_current_fy2024 Real)
(declare-const receivables_net_current_fy2024 Real)
(declare-const short_term_investments_fy2024 Real)

(assert (! (= cash_and_cash_equivalents_at_carrying_value_fy2024 9906) :named evidence_cash_and_cash_equivalents_at_carrying_value_fy2024))
(assert (! (= inventory_net_fy2024 18647) :named evidence_inventory_net_fy2024))
(assert (! (= other_assets_current_fy2024 1734) :named evidence_other_assets_current_fy2024))
(assert (! (= receivables_net_current_fy2024 2721) :named evidence_receivables_net_current_fy2024))
(assert (! (= short_term_investments_fy2024 1238) :named evidence_short_term_investments_fy2024))

(assert (! (= computed_assets_current_fy2024 (+ cash_and_cash_equivalents_at_carrying_value_fy2024 short_term_investments_fy2024 receivables_net_current_fy2024 inventory_net_fy2024 other_assets_current_fy2024)) :named formula_assets_current_fy2024))

(assert (! (<= (- computed_assets_current_fy2024 35879) 35.878999999999998) :named claim_upper))
(assert (! (<= (- 35879 computed_assets_current_fy2024) 35.878999999999998) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AssetsCurrent_instant_2024_09_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2024_09_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_InventoryNet_instant_2024_09_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2024_09_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_ReceivablesNetCurrent_instant_2024_09_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_ShortTermInvestments_instant_2024_09_01_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_AssetsCurrent_instant_2024_09_01_unit_USD_dims_none 34246) :named evidence_xbrl_fact_us_gaap_AssetsCurrent_instant_2024_09_01_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= cash_and_cash_equivalents_at_carrying_value_fy2024 xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2024_09_01_unit_USD_dims_none) :named xbrl_bind_cash_and_cash_equivalents_at_carrying_value_fy2024_edgar_2024_09_01_0000909832_24_000049))
(assert (! (= xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2024_09_01_unit_USD_dims_none 9906) :named xbrl_instance_cash_and_cash_equivalents_at_carrying_value_fy2024))
(assert (! (= short_term_investments_fy2024 xbrl_fact_us_gaap_ShortTermInvestments_instant_2024_09_01_unit_USD_dims_none) :named xbrl_bind_short_term_investments_fy2024_edgar_2024_09_01_0000909832_24_000049))
(assert (! (= xbrl_fact_us_gaap_ShortTermInvestments_instant_2024_09_01_unit_USD_dims_none 1238) :named xbrl_instance_short_term_investments_fy2024))
(assert (! (= receivables_net_current_fy2024 xbrl_fact_us_gaap_ReceivablesNetCurrent_instant_2024_09_01_unit_USD_dims_none) :named xbrl_bind_receivables_net_current_fy2024_edgar_2024_09_01_0000909832_24_000049))
(assert (! (= xbrl_fact_us_gaap_ReceivablesNetCurrent_instant_2024_09_01_unit_USD_dims_none 2721) :named xbrl_instance_receivables_net_current_fy2024))
(assert (! (= inventory_net_fy2024 xbrl_fact_us_gaap_InventoryNet_instant_2024_09_01_unit_USD_dims_none) :named xbrl_bind_inventory_net_fy2024_edgar_2024_09_01_0000909832_24_000049))
(assert (! (= xbrl_fact_us_gaap_InventoryNet_instant_2024_09_01_unit_USD_dims_none 18647) :named xbrl_instance_inventory_net_fy2024))
(assert (! (= other_assets_current_fy2024 xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2024_09_01_unit_USD_dims_none) :named xbrl_bind_other_assets_current_fy2024_edgar_2024_09_01_0000909832_24_000049))
(assert (! (= xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2024_09_01_unit_USD_dims_none 1734) :named xbrl_instance_other_assets_current_fy2024))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_AssetsCurrent_instant_2024_09_01_unit_USD_dims_none (+ xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2024_09_01_unit_USD_dims_none xbrl_fact_us_gaap_ShortTermInvestments_instant_2024_09_01_unit_USD_dims_none xbrl_fact_us_gaap_ReceivablesNetCurrent_instant_2024_09_01_unit_USD_dims_none xbrl_fact_us_gaap_InventoryNet_instant_2024_09_01_unit_USD_dims_none xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2024_09_01_unit_USD_dims_none)) 3) :named xbrl_calc_7_881368694_AssetsCurrent_c_12_upper))
(assert (! (>= (- xbrl_fact_us_gaap_AssetsCurrent_instant_2024_09_01_unit_USD_dims_none (+ xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2024_09_01_unit_USD_dims_none xbrl_fact_us_gaap_ShortTermInvestments_instant_2024_09_01_unit_USD_dims_none xbrl_fact_us_gaap_ReceivablesNetCurrent_instant_2024_09_01_unit_USD_dims_none xbrl_fact_us_gaap_InventoryNet_instant_2024_09_01_unit_USD_dims_none xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2024_09_01_unit_USD_dims_none)) (- 3)) :named xbrl_calc_7_881368694_AssetsCurrent_c_12_lower))

(check-sat)
(get-unsat-core)
(get-model)