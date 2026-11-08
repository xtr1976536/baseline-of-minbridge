(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_income_loss_from_continuing_operations_before_income_taxes_extraordinary_items_noncontrolling_interest_fy2026 Real)
(declare-const gain_loss_on_investments_fy2026 Real)
(declare-const operating_income_loss_fy2026 Real)
(declare-const other_nonoperating_income_expense_fy2026 Real)

(assert (! (= gain_loss_on_investments_fy2026 1017) :named evidence_gain_loss_on_investments_fy2026))
(assert (! (= operating_income_loss_fy2026 8331) :named evidence_operating_income_loss_fy2026))
(assert (! (= other_nonoperating_income_expense_fy2026 172) :named evidence_other_nonoperating_income_expense_fy2026))

(assert (! (= computed_income_loss_from_continuing_operations_before_income_taxes_extraordinary_items_noncontrolling_interest_fy2026 (+ gain_loss_on_investments_fy2026 operating_income_loss_fy2026 other_nonoperating_income_expense_fy2026)) :named formula_income_loss_from_continuing_operations_before_income_taxes_extraordinary_items_noncontrolling_interest_fy2026))

(assert (! (<= (- computed_income_loss_from_continuing_operations_before_income_taxes_extraordinary_items_noncontrolling_interest_fy2026 8331) 8.3309999999999995) :named claim_upper))
(assert (! (<= (- 8331 computed_income_loss_from_continuing_operations_before_income_taxes_extraordinary_items_noncontrolling_interest_fy2026) 8.3309999999999995) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)