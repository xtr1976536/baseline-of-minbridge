(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_assets_current_fy2022 Real)
(declare-const accounts_notes_and_loans_receivable_net_current_fy2022 Real)
(declare-const cash_and_cash_equivalents_at_carrying_value_fy2022 Real)
(declare-const inventory_net_fy2022 Real)
(declare-const prepaid_expense_and_other_assets_current_fy2022 Real)

(assert (! (= accounts_notes_and_loans_receivable_net_current_fy2022 2115) :named evidence_accounts_notes_and_loans_receivable_net_current_fy2022))
(assert (! (= cash_and_cash_equivalents_at_carrying_value_fy2022 2583.8000000000002) :named evidence_cash_and_cash_equivalents_at_carrying_value_fy2022))
(assert (! (= inventory_net_fy2022 52) :named evidence_inventory_net_fy2022))
(assert (! (= prepaid_expense_and_other_assets_current_fy2022 673.39999999999998) :named evidence_prepaid_expense_and_other_assets_current_fy2022))

(assert (! (= computed_assets_current_fy2022 (+ cash_and_cash_equivalents_at_carrying_value_fy2022 accounts_notes_and_loans_receivable_net_current_fy2022 inventory_net_fy2022 prepaid_expense_and_other_assets_current_fy2022)) :named formula_assets_current_fy2022))

(assert (! (<= (- computed_assets_current_fy2022 5424) 5.4240000000000004) :named claim_upper))
(assert (! (<= (- 5424 computed_assets_current_fy2022) 5.4240000000000004) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccountsNotesAndLoansReceivableNetCurrent_instant_2022_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_AssetsCurrent_instant_2022_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2022_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_InventoryNet_instant_2022_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_PrepaidExpenseAndOtherAssetsCurrent_instant_2022_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_AssetsCurrent_instant_2022_12_31_unit_USD_dims_none 5424.1999999999998) :named evidence_xbrl_fact_us_gaap_AssetsCurrent_instant_2022_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= cash_and_cash_equivalents_at_carrying_value_fy2022 xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2022_12_31_unit_USD_dims_none) :named xbrl_bind_cash_and_cash_equivalents_at_carrying_value_fy2022_edgar_2022_12_31_0000063908_23_000012))
(assert (! (= xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2022_12_31_unit_USD_dims_none 2583.8) :named xbrl_instance_cash_and_cash_equivalents_at_carrying_value_fy2022))
(assert (! (= accounts_notes_and_loans_receivable_net_current_fy2022 xbrl_fact_us_gaap_AccountsNotesAndLoansReceivableNetCurrent_instant_2022_12_31_unit_USD_dims_none) :named xbrl_bind_accounts_notes_and_loans_receivable_net_current_fy2022_edgar_2022_12_31_0000063908_23_000012))
(assert (! (= xbrl_fact_us_gaap_AccountsNotesAndLoansReceivableNetCurrent_instant_2022_12_31_unit_USD_dims_none 2115) :named xbrl_instance_accounts_notes_and_loans_receivable_net_current_fy2022))
(assert (! (= inventory_net_fy2022 xbrl_fact_us_gaap_InventoryNet_instant_2022_12_31_unit_USD_dims_none) :named xbrl_bind_inventory_net_fy2022_edgar_2022_12_31_0000063908_23_000012))
(assert (! (= xbrl_fact_us_gaap_InventoryNet_instant_2022_12_31_unit_USD_dims_none 52) :named xbrl_instance_inventory_net_fy2022))
(assert (! (= prepaid_expense_and_other_assets_current_fy2022 xbrl_fact_us_gaap_PrepaidExpenseAndOtherAssetsCurrent_instant_2022_12_31_unit_USD_dims_none) :named xbrl_bind_prepaid_expense_and_other_assets_current_fy2022_edgar_2022_12_31_0000063908_23_000012))
(assert (! (= xbrl_fact_us_gaap_PrepaidExpenseAndOtherAssetsCurrent_instant_2022_12_31_unit_USD_dims_none 673.4) :named xbrl_instance_prepaid_expense_and_other_assets_current_fy2022))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_AssetsCurrent_instant_2022_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2022_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccountsNotesAndLoansReceivableNetCurrent_instant_2022_12_31_unit_USD_dims_none xbrl_fact_us_gaap_InventoryNet_instant_2022_12_31_unit_USD_dims_none xbrl_fact_us_gaap_PrepaidExpenseAndOtherAssetsCurrent_instant_2022_12_31_unit_USD_dims_none)) 0.25) :named xbrl_calc_12_337340623_AssetsCurrent_if07f4a5c323146239993eea7480997e4_I20221231_upper))
(assert (! (>= (- xbrl_fact_us_gaap_AssetsCurrent_instant_2022_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_CashAndCashEquivalentsAtCarryingValue_instant_2022_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccountsNotesAndLoansReceivableNetCurrent_instant_2022_12_31_unit_USD_dims_none xbrl_fact_us_gaap_InventoryNet_instant_2022_12_31_unit_USD_dims_none xbrl_fact_us_gaap_PrepaidExpenseAndOtherAssetsCurrent_instant_2022_12_31_unit_USD_dims_none)) (- 0.25)) :named xbrl_calc_12_337340623_AssetsCurrent_if07f4a5c323146239993eea7480997e4_I20221231_lower))

(check-sat)
(get-unsat-core)
(get-model)