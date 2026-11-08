(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_net_income_loss_fy2026 Real)
(declare-const income_loss_from_continuing_operations_before_income_taxes_extraordinary_items_noncontrolling_interest_fy2026 Real)
(declare-const income_tax_expense_benefit_fy2026 Real)

(assert (! (= income_loss_from_continuing_operations_before_income_taxes_extraordinary_items_noncontrolling_interest_fy2026 9520) :named evidence_income_loss_from_continuing_operations_before_income_taxes_extraordinary_items_noncontrolling_interest_fy2026))
(assert (! (= income_tax_expense_benefit_fy2026 2063) :named evidence_income_tax_expense_benefit_fy2026))

(assert (! (= computed_net_income_loss_fy2026 (+ (* (- 1) income_tax_expense_benefit_fy2026) income_loss_from_continuing_operations_before_income_taxes_extraordinary_items_noncontrolling_interest_fy2026)) :named formula_net_income_loss_fy2026))

(assert (! (<= (- computed_net_income_loss_fy2026 7457) 7.4569999999999999) :named claim_upper))
(assert (! (<= (- 7457 computed_net_income_loss_fy2026) 7.4569999999999999) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)