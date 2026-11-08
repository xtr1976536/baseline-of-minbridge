(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_assets_current_fy2025 Real)
(declare-const accounts_notes_and_loans_receivable_net_current_fy2025 Real)
(declare-const cash_and_cash_equivalents_at_carrying_value_fy2025 Real)
(declare-const inventory_net_fy2025 Real)
(declare-const prepaid_expense_and_other_assets_current_fy2025 Real)

(assert (! (= accounts_notes_and_loans_receivable_net_current_fy2025 2466) :named evidence_accounts_notes_and_loans_receivable_net_current_fy2025))
(assert (! (= cash_and_cash_equivalents_at_carrying_value_fy2025 774) :named evidence_cash_and_cash_equivalents_at_carrying_value_fy2025))
(assert (! (= inventory_net_fy2025 61) :named evidence_inventory_net_fy2025))
(assert (! (= prepaid_expense_and_other_assets_current_fy2025 863) :named evidence_prepaid_expense_and_other_assets_current_fy2025))

(assert (! (= computed_assets_current_fy2025 (+ cash_and_cash_equivalents_at_carrying_value_fy2025 accounts_notes_and_loans_receivable_net_current_fy2025 inventory_net_fy2025 prepaid_expense_and_other_assets_current_fy2025)) :named formula_assets_current_fy2025))

(assert (! (<= (- computed_assets_current_fy2025 4164) 4.1639999999999997) :named claim_upper))
(assert (! (<= (- 4164 computed_assets_current_fy2025) 4.1639999999999997) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccountsNotesAndLoansReceivableNetCurrent_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_AssetsCurrent_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_InventoryNet_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_PrepaidExpenseAndOtherAssetsCurrent_instant_2025_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_AssetsCurrent_instant_2025_12_31_unit_USD_dims_none 4163) :named evidence_xbrl_fact_us_gaap_AssetsCurrent_instant_2025_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= cash_and_cash_equivalents_at_carrying_value_fy2025 xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_cash_and_cash_equivalents_at_carrying_value_fy2025_edgar_2025_12_31_0000063908_26_000035))
(assert (! (= xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2025_12_31_unit_USD_dims_none 774) :named xbrl_instance_cash_and_cash_equivalents_at_carrying_value_fy2025))
(assert (! (= accounts_notes_and_loans_receivable_net_current_fy2025 xbrl_fact_us_gaap_AccountsNotesAndLoansReceivableNetCurrent_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_accounts_notes_and_loans_receivable_net_current_fy2025_edgar_2025_12_31_0000063908_26_000035))
(assert (! (= xbrl_fact_us_gaap_AccountsNotesAndLoansReceivableNetCurrent_instant_2025_12_31_unit_USD_dims_none 2466) :named xbrl_instance_accounts_notes_and_loans_receivable_net_current_fy2025))
(assert (! (= inventory_net_fy2025 xbrl_fact_us_gaap_InventoryNet_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_inventory_net_fy2025_edgar_2025_12_31_0000063908_26_000035))
(assert (! (= xbrl_fact_us_gaap_InventoryNet_instant_2025_12_31_unit_USD_dims_none 61) :named xbrl_instance_inventory_net_fy2025))
(assert (! (= prepaid_expense_and_other_assets_current_fy2025 xbrl_fact_us_gaap_PrepaidExpenseAndOtherAssetsCurrent_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_prepaid_expense_and_other_assets_current_fy2025_edgar_2025_12_31_0000063908_26_000035))
(assert (! (= xbrl_fact_us_gaap_PrepaidExpenseAndOtherAssetsCurrent_instant_2025_12_31_unit_USD_dims_none 863) :named xbrl_instance_prepaid_expense_and_other_assets_current_fy2025))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_AssetsCurrent_instant_2025_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccountsNotesAndLoansReceivableNetCurrent_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_InventoryNet_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_PrepaidExpenseAndOtherAssetsCurrent_instant_2025_12_31_unit_USD_dims_none)) 2.5) :named xbrl_calc_13_337340623_AssetsCurrent_c_6_upper))
(assert (! (>= (- xbrl_fact_us_gaap_AssetsCurrent_instant_2025_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccountsNotesAndLoansReceivableNetCurrent_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_InventoryNet_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_PrepaidExpenseAndOtherAssetsCurrent_instant_2025_12_31_unit_USD_dims_none)) (- 2.5)) :named xbrl_calc_13_337340623_AssetsCurrent_c_6_lower))

(check-sat)
(get-unsat-core)
(get-model)