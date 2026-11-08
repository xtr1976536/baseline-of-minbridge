(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_assets_current_fy2026 Real)
(declare-const cash_and_cash_equivalents_at_carrying_value_fy2026 Real)
(declare-const inventory_net_fy2026 Real)
(declare-const prepaid_expense_and_other_assets_current_fy2026 Real)
(declare-const receivables_net_current_fy2026 Real)

(assert (! (= cash_and_cash_equivalents_at_carrying_value_fy2026 10727) :named evidence_cash_and_cash_equivalents_at_carrying_value_fy2026))
(assert (! (= inventory_net_fy2026 58851) :named evidence_inventory_net_fy2026))
(assert (! (= prepaid_expense_and_other_assets_current_fy2026 4124) :named evidence_prepaid_expense_and_other_assets_current_fy2026))
(assert (! (= receivables_net_current_fy2026 11172) :named evidence_receivables_net_current_fy2026))

(assert (! (= computed_assets_current_fy2026 (+ cash_and_cash_equivalents_at_carrying_value_fy2026 receivables_net_current_fy2026 inventory_net_fy2026 prepaid_expense_and_other_assets_current_fy2026)) :named formula_assets_current_fy2026))

(assert (! (<= (- computed_assets_current_fy2026 84874) 84.873999999999995) :named claim_upper))
(assert (! (<= (- 84874 computed_assets_current_fy2026) 84.873999999999995) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AssetsCurrent_instant_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_InventoryNet_instant_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_PrepaidExpenseAndOtherAssetsCurrent_instant_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_ReceivablesNetCurrent_instant_2026_01_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_AssetsCurrent_instant_2026_01_31_unit_USD_dims_none 84874) :named evidence_xbrl_fact_us_gaap_AssetsCurrent_instant_2026_01_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= cash_and_cash_equivalents_at_carrying_value_fy2026 xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2026_01_31_unit_USD_dims_none) :named xbrl_bind_cash_and_cash_equivalents_at_carrying_value_fy2026_edgar_2026_01_31_0000104169_26_000055))
(assert (! (= xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2026_01_31_unit_USD_dims_none 10727) :named xbrl_instance_cash_and_cash_equivalents_at_carrying_value_fy2026))
(assert (! (= receivables_net_current_fy2026 xbrl_fact_us_gaap_ReceivablesNetCurrent_instant_2026_01_31_unit_USD_dims_none) :named xbrl_bind_receivables_net_current_fy2026_edgar_2026_01_31_0000104169_26_000055))
(assert (! (= xbrl_fact_us_gaap_ReceivablesNetCurrent_instant_2026_01_31_unit_USD_dims_none 11172) :named xbrl_instance_receivables_net_current_fy2026))
(assert (! (= inventory_net_fy2026 xbrl_fact_us_gaap_InventoryNet_instant_2026_01_31_unit_USD_dims_none) :named xbrl_bind_inventory_net_fy2026_edgar_2026_01_31_0000104169_26_000055))
(assert (! (= xbrl_fact_us_gaap_InventoryNet_instant_2026_01_31_unit_USD_dims_none 58851) :named xbrl_instance_inventory_net_fy2026))
(assert (! (= prepaid_expense_and_other_assets_current_fy2026 xbrl_fact_us_gaap_PrepaidExpenseAndOtherAssetsCurrent_instant_2026_01_31_unit_USD_dims_none) :named xbrl_bind_prepaid_expense_and_other_assets_current_fy2026_edgar_2026_01_31_0000104169_26_000055))
(assert (! (= xbrl_fact_us_gaap_PrepaidExpenseAndOtherAssetsCurrent_instant_2026_01_31_unit_USD_dims_none 4124) :named xbrl_instance_prepaid_expense_and_other_assets_current_fy2026))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_AssetsCurrent_instant_2026_01_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2026_01_31_unit_USD_dims_none xbrl_fact_us_gaap_ReceivablesNetCurrent_instant_2026_01_31_unit_USD_dims_none xbrl_fact_us_gaap_InventoryNet_instant_2026_01_31_unit_USD_dims_none xbrl_fact_us_gaap_PrepaidExpenseAndOtherAssetsCurrent_instant_2026_01_31_unit_USD_dims_none)) 2.5) :named xbrl_calc_12_323192290_AssetsCurrent_c_16_upper))
(assert (! (>= (- xbrl_fact_us_gaap_AssetsCurrent_instant_2026_01_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2026_01_31_unit_USD_dims_none xbrl_fact_us_gaap_ReceivablesNetCurrent_instant_2026_01_31_unit_USD_dims_none xbrl_fact_us_gaap_InventoryNet_instant_2026_01_31_unit_USD_dims_none xbrl_fact_us_gaap_PrepaidExpenseAndOtherAssetsCurrent_instant_2026_01_31_unit_USD_dims_none)) (- 2.5)) :named xbrl_calc_12_323192290_AssetsCurrent_c_16_lower))

(check-sat)
(get-unsat-core)
(get-model)