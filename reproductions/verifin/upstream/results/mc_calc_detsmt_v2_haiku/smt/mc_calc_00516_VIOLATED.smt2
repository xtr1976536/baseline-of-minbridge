(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_income_loss_from_continuing_operations_before_income_taxes_extraordinary_items_noncontrolling_interest_fy2025 Real)
(declare-const gain_loss_on_investments_fy2025 Real)
(declare-const operating_income_loss_fy2025 Real)
(declare-const other_nonoperating_income_expense_fy2025 Real)

(assert (! (= gain_loss_on_investments_fy2025 1017) :named evidence_gain_loss_on_investments_fy2025))
(assert (! (= operating_income_loss_fy2025 8331) :named evidence_operating_income_loss_fy2025))
(assert (! (= other_nonoperating_income_expense_fy2025 172) :named evidence_other_nonoperating_income_expense_fy2025))

(assert (! (= computed_income_loss_from_continuing_operations_before_income_taxes_extraordinary_items_noncontrolling_interest_fy2025 (+ gain_loss_on_investments_fy2025 operating_income_loss_fy2025 other_nonoperating_income_expense_fy2025)) :named formula_income_loss_from_continuing_operations_before_income_taxes_extraordinary_items_noncontrolling_interest_fy2025))

(assert (! (<= (- computed_income_loss_from_continuing_operations_before_income_taxes_extraordinary_items_noncontrolling_interest_fy2025 7438) 7.4379999999999997) :named claim_upper))
(assert (! (<= (- 7438 computed_income_loss_from_continuing_operations_before_income_taxes_extraordinary_items_noncontrolling_interest_fy2025) 7.4379999999999997) :named claim_lower))

; EDGAR-companyfacts fact bindings (no calculation-linkbase constraints).
(declare-const xbrl_fact_us_gaap_GainLossOnInvestments_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherNonoperatingIncomeExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= gain_loss_on_investments_fy2025 xbrl_fact_us_gaap_GainLossOnInvestments_duration_2025_02_01_2026_01_31_unit_USD_dims_none) :named xbrl_bind_gain_loss_on_investments_fy2025_edgar_2026_01_31_0001108524_26_000060))
(assert (! (= xbrl_fact_us_gaap_GainLossOnInvestments_duration_2025_02_01_2026_01_31_unit_USD_dims_none 1017) :named xbrl_instance_gain_loss_on_investments_fy2025))
(assert (! (= operating_income_loss_fy2025 xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_02_01_2026_01_31_unit_USD_dims_none) :named xbrl_bind_operating_income_loss_fy2025_edgar_2026_01_31_0001108524_26_000060))
(assert (! (= xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_02_01_2026_01_31_unit_USD_dims_none 8331) :named xbrl_instance_operating_income_loss_fy2025))
(assert (! (= other_nonoperating_income_expense_fy2025 xbrl_fact_us_gaap_OtherNonoperatingIncomeExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none) :named xbrl_bind_other_nonoperating_income_expense_fy2025_edgar_2026_01_31_0001108524_26_000060))
(assert (! (= xbrl_fact_us_gaap_OtherNonoperatingIncomeExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none 172) :named xbrl_instance_other_nonoperating_income_expense_fy2025))

(check-sat)
(get-unsat-core)
(get-model)