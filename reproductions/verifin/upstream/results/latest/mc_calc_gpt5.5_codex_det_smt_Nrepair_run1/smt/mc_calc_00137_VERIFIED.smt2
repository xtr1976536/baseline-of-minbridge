(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_assets_current_fy2025 Real)
(declare-const cash_and_cash_equivalents_at_carrying_value_fy2025 Real)
(declare-const inventory_net_fy2025 Real)
(declare-const other_assets_current_fy2025 Real)
(declare-const receivables_net_current_fy2025 Real)
(declare-const short_term_investments_fy2025 Real)

(assert (! (= cash_and_cash_equivalents_at_carrying_value_fy2025 14161) :named evidence_cash_and_cash_equivalents_at_carrying_value_fy2025))
(assert (! (= inventory_net_fy2025 18116) :named evidence_inventory_net_fy2025))
(assert (! (= other_assets_current_fy2025 1777) :named evidence_other_assets_current_fy2025))
(assert (! (= receivables_net_current_fy2025 3203) :named evidence_receivables_net_current_fy2025))
(assert (! (= short_term_investments_fy2025 1123) :named evidence_short_term_investments_fy2025))

(assert (! (= computed_assets_current_fy2025 (+ cash_and_cash_equivalents_at_carrying_value_fy2025 short_term_investments_fy2025 receivables_net_current_fy2025 inventory_net_fy2025 other_assets_current_fy2025)) :named formula_assets_current_fy2025))

(assert (! (<= (- computed_assets_current_fy2025 38380) 38.380000000000003) :named claim_upper))
(assert (! (<= (- 38380 computed_assets_current_fy2025) 38.380000000000003) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AssetsCurrent_instant_2025_08_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2025_08_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_InventoryNet_instant_2025_08_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2025_08_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_ReceivablesNetCurrent_instant_2025_08_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_ShortTermInvestments_instant_2025_08_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_AssetsCurrent_instant_2025_08_31_unit_USD_dims_none 38380) :named evidence_xbrl_fact_us_gaap_AssetsCurrent_instant_2025_08_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= cash_and_cash_equivalents_at_carrying_value_fy2025 xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2025_08_31_unit_USD_dims_none) :named xbrl_bind_cash_and_cash_equivalents_at_carrying_value_fy2025_edgar_2025_08_31_0000909832_25_000101))
(assert (! (= xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2025_08_31_unit_USD_dims_none 14161) :named xbrl_instance_cash_and_cash_equivalents_at_carrying_value_fy2025))
(assert (! (= short_term_investments_fy2025 xbrl_fact_us_gaap_ShortTermInvestments_instant_2025_08_31_unit_USD_dims_none) :named xbrl_bind_short_term_investments_fy2025_edgar_2025_08_31_0000909832_25_000101))
(assert (! (= xbrl_fact_us_gaap_ShortTermInvestments_instant_2025_08_31_unit_USD_dims_none 1123) :named xbrl_instance_short_term_investments_fy2025))
(assert (! (= receivables_net_current_fy2025 xbrl_fact_us_gaap_ReceivablesNetCurrent_instant_2025_08_31_unit_USD_dims_none) :named xbrl_bind_receivables_net_current_fy2025_edgar_2025_08_31_0000909832_25_000101))
(assert (! (= xbrl_fact_us_gaap_ReceivablesNetCurrent_instant_2025_08_31_unit_USD_dims_none 3203) :named xbrl_instance_receivables_net_current_fy2025))
(assert (! (= inventory_net_fy2025 xbrl_fact_us_gaap_InventoryNet_instant_2025_08_31_unit_USD_dims_none) :named xbrl_bind_inventory_net_fy2025_edgar_2025_08_31_0000909832_25_000101))
(assert (! (= xbrl_fact_us_gaap_InventoryNet_instant_2025_08_31_unit_USD_dims_none 18116) :named xbrl_instance_inventory_net_fy2025))
(assert (! (= other_assets_current_fy2025 xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2025_08_31_unit_USD_dims_none) :named xbrl_bind_other_assets_current_fy2025_edgar_2025_08_31_0000909832_25_000101))
(assert (! (= xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2025_08_31_unit_USD_dims_none 1777) :named xbrl_instance_other_assets_current_fy2025))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_AssetsCurrent_instant_2025_08_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2025_08_31_unit_USD_dims_none xbrl_fact_us_gaap_ShortTermInvestments_instant_2025_08_31_unit_USD_dims_none xbrl_fact_us_gaap_ReceivablesNetCurrent_instant_2025_08_31_unit_USD_dims_none xbrl_fact_us_gaap_InventoryNet_instant_2025_08_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2025_08_31_unit_USD_dims_none)) 3) :named xbrl_calc_8_881368694_AssetsCurrent_c_12_upper))
(assert (! (>= (- xbrl_fact_us_gaap_AssetsCurrent_instant_2025_08_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2025_08_31_unit_USD_dims_none xbrl_fact_us_gaap_ShortTermInvestments_instant_2025_08_31_unit_USD_dims_none xbrl_fact_us_gaap_ReceivablesNetCurrent_instant_2025_08_31_unit_USD_dims_none xbrl_fact_us_gaap_InventoryNet_instant_2025_08_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2025_08_31_unit_USD_dims_none)) (- 3)) :named xbrl_calc_8_881368694_AssetsCurrent_c_12_lower))

(check-sat)
(get-unsat-core)
(get-model)