(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_income_loss_fy2026 Real)
(declare-const gross_profit_fy2026 Real)
(declare-const operating_expenses_fy2026 Real)

(assert (! (= gross_profit_fy2026 32255) :named evidence_gross_profit_fy2026))
(assert (! (= operating_expenses_fy2026 23924) :named evidence_operating_expenses_fy2026))

(assert (! (= computed_operating_income_loss_fy2026 (+ gross_profit_fy2026 (* (- 1) operating_expenses_fy2026))) :named formula_operating_income_loss_fy2026))

(assert (! (<= (- computed_operating_income_loss_fy2026 8331) 8.3309999999999995) :named claim_upper))
(assert (! (<= (- 8331 computed_operating_income_loss_fy2026) 8.3309999999999995) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)