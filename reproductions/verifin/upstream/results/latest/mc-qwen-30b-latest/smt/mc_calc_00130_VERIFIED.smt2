(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_income_loss_from_continuing_operations_before_income_taxes_extraordinary_items_noncontrolling_interest_fy2026 Real)
(declare-const interest_expense_nonoperating_fy2026 Real)
(declare-const investment_income_interest_and_dividend_fy2026 Real)
(declare-const operating_income_loss_fy2026 Real)

(assert (! (= interest_expense_nonoperating_fy2026 2412) :named evidence_interest_expense_nonoperating_fy2026))
(assert (! (= investment_income_interest_and_dividend_fy2026 124) :named evidence_investment_income_interest_and_dividend_fy2026))
(assert (! (= operating_income_loss_fy2026 20890) :named evidence_operating_income_loss_fy2026))

(assert (! (= computed_income_loss_from_continuing_operations_before_income_taxes_extraordinary_items_noncontrolling_interest_fy2026 (+ operating_income_loss_fy2026 (* (- 1) interest_expense_nonoperating_fy2026) investment_income_interest_and_dividend_fy2026)) :named formula_income_loss_from_continuing_operations_before_income_taxes_extraordinary_items_noncontrolling_interest_fy2026))

(assert (! (<= (- computed_income_loss_from_continuing_operations_before_income_taxes_extraordinary_items_noncontrolling_interest_fy2026 18602) 18.602) :named claim_upper))
(assert (! (<= (- 18602 computed_income_loss_from_continuing_operations_before_income_taxes_extraordinary_items_noncontrolling_interest_fy2026) 18.602) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)