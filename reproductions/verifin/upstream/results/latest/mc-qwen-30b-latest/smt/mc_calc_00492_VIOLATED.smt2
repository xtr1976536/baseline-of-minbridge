(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_income_loss_from_continuing_operations_before_income_taxes_extraordinary_items_noncontrolling_interest_fy2025 Real)
(declare-const nonoperating_income_expense_fy2025 Real)
(declare-const operating_income_loss_fy2025 Real)

(assert (! (= nonoperating_income_expense_fy2025 -2288) :named evidence_nonoperating_income_expense_fy2025))
(assert (! (= operating_income_loss_fy2025 20890) :named evidence_operating_income_loss_fy2025))

(assert (! (= computed_income_loss_from_continuing_operations_before_income_taxes_extraordinary_items_noncontrolling_interest_fy2025 (+ operating_income_loss_fy2025 nonoperating_income_expense_fy2025)) :named formula_income_loss_from_continuing_operations_before_income_taxes_extraordinary_items_noncontrolling_interest_fy2025))

(assert (! (<= (- computed_income_loss_from_continuing_operations_before_income_taxes_extraordinary_items_noncontrolling_interest_fy2025 19406) 19.405999999999999) :named claim_upper))
(assert (! (<= (- 19406 computed_income_loss_from_continuing_operations_before_income_taxes_extraordinary_items_noncontrolling_interest_fy2025) 19.405999999999999) :named claim_lower))

; EDGAR-companyfacts fact bindings (no calculation-linkbase constraints).
(declare-const xbrl_fact_us_gaap_NonoperatingIncomeExpense_duration_2025_02_03_2026_02_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_02_03_2026_02_01_unit_USD_dims_none Real)

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= operating_income_loss_fy2025 xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_02_03_2026_02_01_unit_USD_dims_none) :named xbrl_bind_operating_income_loss_fy2025_edgar_2026_02_01_0001628280_26_019436))
(assert (! (= xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_02_03_2026_02_01_unit_USD_dims_none 20890) :named xbrl_instance_operating_income_loss_fy2025))
(assert (! (= nonoperating_income_expense_fy2025 xbrl_fact_us_gaap_NonoperatingIncomeExpense_duration_2025_02_03_2026_02_01_unit_USD_dims_none) :named xbrl_bind_nonoperating_income_expense_fy2025_edgar_2026_02_01_0001628280_26_019436))
(assert (! (= xbrl_fact_us_gaap_NonoperatingIncomeExpense_duration_2025_02_03_2026_02_01_unit_USD_dims_none -2288) :named xbrl_instance_nonoperating_income_expense_fy2025))

(check-sat)
(get-unsat-core)
(get-model)