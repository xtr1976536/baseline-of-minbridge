(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_assets_current_fy2023 Real)
(declare-const cash_and_cash_equivalents_at_carrying_value_fy2023 Real)
(declare-const inventory_net_fy2023 Real)
(declare-const other_assets_current_fy2023 Real)
(declare-const receivables_net_current_fy2023 Real)
(declare-const short_term_investments_fy2023 Real)

(assert (! (= cash_and_cash_equivalents_at_carrying_value_fy2023 13700) :named evidence_cash_and_cash_equivalents_at_carrying_value_fy2023))
(assert (! (= inventory_net_fy2023 16651) :named evidence_inventory_net_fy2023))
(assert (! (= other_assets_current_fy2023 1709) :named evidence_other_assets_current_fy2023))
(assert (! (= receivables_net_current_fy2023 2285) :named evidence_receivables_net_current_fy2023))
(assert (! (= short_term_investments_fy2023 1534) :named evidence_short_term_investments_fy2023))

(assert (! (= computed_assets_current_fy2023 (+ cash_and_cash_equivalents_at_carrying_value_fy2023 short_term_investments_fy2023 receivables_net_current_fy2023 inventory_net_fy2023 other_assets_current_fy2023)) :named formula_assets_current_fy2023))

(assert (! (<= (- computed_assets_current_fy2023 35979) 35.978999999999999) :named claim_upper))
(assert (! (<= (- 35979 computed_assets_current_fy2023) 35.978999999999999) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AssetsCurrent_instant_2023_09_03_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2023_09_03_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_InventoryNet_instant_2023_09_03_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2023_09_03_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_ReceivablesNetCurrent_instant_2023_09_03_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_ShortTermInvestments_instant_2023_09_03_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_AssetsCurrent_instant_2023_09_03_unit_USD_dims_none 35879) :named evidence_xbrl_fact_us_gaap_AssetsCurrent_instant_2023_09_03_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= cash_and_cash_equivalents_at_carrying_value_fy2023 xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2023_09_03_unit_USD_dims_none) :named xbrl_bind_cash_and_cash_equivalents_at_carrying_value_fy2023_edgar_2023_09_03_0000909832_23_000042))
(assert (! (= xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2023_09_03_unit_USD_dims_none 13700) :named xbrl_instance_cash_and_cash_equivalents_at_carrying_value_fy2023))
(assert (! (= short_term_investments_fy2023 xbrl_fact_us_gaap_ShortTermInvestments_instant_2023_09_03_unit_USD_dims_none) :named xbrl_bind_short_term_investments_fy2023_edgar_2023_09_03_0000909832_23_000042))
(assert (! (= xbrl_fact_us_gaap_ShortTermInvestments_instant_2023_09_03_unit_USD_dims_none 1534) :named xbrl_instance_short_term_investments_fy2023))
(assert (! (= receivables_net_current_fy2023 xbrl_fact_us_gaap_ReceivablesNetCurrent_instant_2023_09_03_unit_USD_dims_none) :named xbrl_bind_receivables_net_current_fy2023_edgar_2023_09_03_0000909832_23_000042))
(assert (! (= xbrl_fact_us_gaap_ReceivablesNetCurrent_instant_2023_09_03_unit_USD_dims_none 2285) :named xbrl_instance_receivables_net_current_fy2023))
(assert (! (= inventory_net_fy2023 xbrl_fact_us_gaap_InventoryNet_instant_2023_09_03_unit_USD_dims_none) :named xbrl_bind_inventory_net_fy2023_edgar_2023_09_03_0000909832_23_000042))
(assert (! (= xbrl_fact_us_gaap_InventoryNet_instant_2023_09_03_unit_USD_dims_none 16651) :named xbrl_instance_inventory_net_fy2023))
(assert (! (= other_assets_current_fy2023 xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2023_09_03_unit_USD_dims_none) :named xbrl_bind_other_assets_current_fy2023_edgar_2023_09_03_0000909832_23_000042))
(assert (! (= xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2023_09_03_unit_USD_dims_none 1709) :named xbrl_instance_other_assets_current_fy2023))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_AssetsCurrent_instant_2023_09_03_unit_USD_dims_none (+ xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2023_09_03_unit_USD_dims_none xbrl_fact_us_gaap_ShortTermInvestments_instant_2023_09_03_unit_USD_dims_none xbrl_fact_us_gaap_ReceivablesNetCurrent_instant_2023_09_03_unit_USD_dims_none xbrl_fact_us_gaap_InventoryNet_instant_2023_09_03_unit_USD_dims_none xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2023_09_03_unit_USD_dims_none)) 3) :named xbrl_calc_6_881368694_AssetsCurrent_c_12_upper))
(assert (! (>= (- xbrl_fact_us_gaap_AssetsCurrent_instant_2023_09_03_unit_USD_dims_none (+ xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2023_09_03_unit_USD_dims_none xbrl_fact_us_gaap_ShortTermInvestments_instant_2023_09_03_unit_USD_dims_none xbrl_fact_us_gaap_ReceivablesNetCurrent_instant_2023_09_03_unit_USD_dims_none xbrl_fact_us_gaap_InventoryNet_instant_2023_09_03_unit_USD_dims_none xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2023_09_03_unit_USD_dims_none)) (- 3)) :named xbrl_calc_6_881368694_AssetsCurrent_c_12_lower))

(check-sat)
(get-unsat-core)
(get-model)