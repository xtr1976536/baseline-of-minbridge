(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_assets_current_fy2025 Real)
(declare-const cash_and_cash_equivalents_at_carrying_value_fy2025 Real)
(declare-const inventory_net_fy2025 Real)
(declare-const prepaid_expense_and_other_assets_current_fy2025 Real)
(declare-const receivables_net_current_fy2025 Real)

(assert (! (= cash_and_cash_equivalents_at_carrying_value_fy2025 9037) :named evidence_cash_and_cash_equivalents_at_carrying_value_fy2025))
(assert (! (= inventory_net_fy2025 56435) :named evidence_inventory_net_fy2025))
(assert (! (= prepaid_expense_and_other_assets_current_fy2025 4011) :named evidence_prepaid_expense_and_other_assets_current_fy2025))
(assert (! (= receivables_net_current_fy2025 9975) :named evidence_receivables_net_current_fy2025))

(assert (! (= computed_assets_current_fy2025 (+ cash_and_cash_equivalents_at_carrying_value_fy2025 receivables_net_current_fy2025 inventory_net_fy2025 prepaid_expense_and_other_assets_current_fy2025)) :named formula_assets_current_fy2025))

(assert (! (<= (- computed_assets_current_fy2025 96584) 96.584000000000003) :named claim_upper))
(assert (! (<= (- 96584 computed_assets_current_fy2025) 96.584000000000003) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AssetsCurrent_instant_2025_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2025_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_InventoryNet_instant_2025_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_PrepaidExpenseAndOtherAssetsCurrent_instant_2025_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_ReceivablesNetCurrent_instant_2025_01_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_AssetsCurrent_instant_2025_01_31_unit_USD_dims_none 79458) :named evidence_xbrl_fact_us_gaap_AssetsCurrent_instant_2025_01_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= cash_and_cash_equivalents_at_carrying_value_fy2025 xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2025_01_31_unit_USD_dims_none) :named xbrl_bind_cash_and_cash_equivalents_at_carrying_value_fy2025_edgar_2025_01_31_0000104169_25_000021))
(assert (! (= xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2025_01_31_unit_USD_dims_none 9037) :named xbrl_instance_cash_and_cash_equivalents_at_carrying_value_fy2025))
(assert (! (= receivables_net_current_fy2025 xbrl_fact_us_gaap_ReceivablesNetCurrent_instant_2025_01_31_unit_USD_dims_none) :named xbrl_bind_receivables_net_current_fy2025_edgar_2025_01_31_0000104169_25_000021))
(assert (! (= xbrl_fact_us_gaap_ReceivablesNetCurrent_instant_2025_01_31_unit_USD_dims_none 9975) :named xbrl_instance_receivables_net_current_fy2025))
(assert (! (= inventory_net_fy2025 xbrl_fact_us_gaap_InventoryNet_instant_2025_01_31_unit_USD_dims_none) :named xbrl_bind_inventory_net_fy2025_edgar_2025_01_31_0000104169_25_000021))
(assert (! (= xbrl_fact_us_gaap_InventoryNet_instant_2025_01_31_unit_USD_dims_none 56435) :named xbrl_instance_inventory_net_fy2025))
(assert (! (= prepaid_expense_and_other_assets_current_fy2025 xbrl_fact_us_gaap_PrepaidExpenseAndOtherAssetsCurrent_instant_2025_01_31_unit_USD_dims_none) :named xbrl_bind_prepaid_expense_and_other_assets_current_fy2025_edgar_2025_01_31_0000104169_25_000021))
(assert (! (= xbrl_fact_us_gaap_PrepaidExpenseAndOtherAssetsCurrent_instant_2025_01_31_unit_USD_dims_none 4011) :named xbrl_instance_prepaid_expense_and_other_assets_current_fy2025))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_AssetsCurrent_instant_2025_01_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2025_01_31_unit_USD_dims_none xbrl_fact_us_gaap_ReceivablesNetCurrent_instant_2025_01_31_unit_USD_dims_none xbrl_fact_us_gaap_InventoryNet_instant_2025_01_31_unit_USD_dims_none xbrl_fact_us_gaap_PrepaidExpenseAndOtherAssetsCurrent_instant_2025_01_31_unit_USD_dims_none)) 2.5) :named xbrl_calc_10_323192290_AssetsCurrent_c_16_upper))
(assert (! (>= (- xbrl_fact_us_gaap_AssetsCurrent_instant_2025_01_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2025_01_31_unit_USD_dims_none xbrl_fact_us_gaap_ReceivablesNetCurrent_instant_2025_01_31_unit_USD_dims_none xbrl_fact_us_gaap_InventoryNet_instant_2025_01_31_unit_USD_dims_none xbrl_fact_us_gaap_PrepaidExpenseAndOtherAssetsCurrent_instant_2025_01_31_unit_USD_dims_none)) (- 2.5)) :named xbrl_calc_10_323192290_AssetsCurrent_c_16_lower))

(check-sat)
(get-unsat-core)
(get-model)