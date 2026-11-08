(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_assets_current_fy2025 Real)
(declare-const accounts_receivable_net_current_fy2025 Real)
(declare-const cash_and_cash_equivalents_at_carrying_value_fy2025 Real)
(declare-const inventory_net_fy2025 Real)
(declare-const other_assets_current_fy2025 Real)

(assert (! (= accounts_receivable_net_current_fy2025 5597) :named evidence_accounts_receivable_net_current_fy2025))
(assert (! (= cash_and_cash_equivalents_at_carrying_value_fy2025 1389) :named evidence_cash_and_cash_equivalents_at_carrying_value_fy2025))
(assert (! (= inventory_net_fy2025 25817) :named evidence_inventory_net_fy2025))
(assert (! (= other_assets_current_fy2025 1588) :named evidence_other_assets_current_fy2025))

(assert (! (= computed_assets_current_fy2025 (+ cash_and_cash_equivalents_at_carrying_value_fy2025 accounts_receivable_net_current_fy2025 inventory_net_fy2025 other_assets_current_fy2025)) :named formula_assets_current_fy2025))

(assert (! (<= (- computed_assets_current_fy2025 31683) 31.683) :named claim_upper))
(assert (! (<= (- 31683 computed_assets_current_fy2025) 31.683) :named claim_lower))

; EDGAR-companyfacts fact bindings (no calculation-linkbase constraints).
(declare-const xbrl_fact_us_gaap_AccountsReceivableNetCurrent_instant_2026_02_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2026_02_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_InventoryNet_instant_2026_02_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2026_02_01_unit_USD_dims_none Real)

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= cash_and_cash_equivalents_at_carrying_value_fy2025 xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2026_02_01_unit_USD_dims_none) :named xbrl_bind_cash_and_cash_equivalents_at_carrying_value_fy2025_edgar_2026_02_01_0001628280_26_019436))
(assert (! (= xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2026_02_01_unit_USD_dims_none 1389) :named xbrl_instance_cash_and_cash_equivalents_at_carrying_value_fy2025))
(assert (! (= accounts_receivable_net_current_fy2025 xbrl_fact_us_gaap_AccountsReceivableNetCurrent_instant_2026_02_01_unit_USD_dims_none) :named xbrl_bind_accounts_receivable_net_current_fy2025_edgar_2026_02_01_0001628280_26_019436))
(assert (! (= xbrl_fact_us_gaap_AccountsReceivableNetCurrent_instant_2026_02_01_unit_USD_dims_none 5597) :named xbrl_instance_accounts_receivable_net_current_fy2025))
(assert (! (= inventory_net_fy2025 xbrl_fact_us_gaap_InventoryNet_instant_2026_02_01_unit_USD_dims_none) :named xbrl_bind_inventory_net_fy2025_edgar_2026_02_01_0001628280_26_019436))
(assert (! (= xbrl_fact_us_gaap_InventoryNet_instant_2026_02_01_unit_USD_dims_none 25817) :named xbrl_instance_inventory_net_fy2025))
(assert (! (= other_assets_current_fy2025 xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2026_02_01_unit_USD_dims_none) :named xbrl_bind_other_assets_current_fy2025_edgar_2026_02_01_0001628280_26_019436))
(assert (! (= xbrl_fact_us_gaap_OtherAssetsCurrent_instant_2026_02_01_unit_USD_dims_none 1588) :named xbrl_instance_other_assets_current_fy2025))

(check-sat)
(get-unsat-core)
(get-model)