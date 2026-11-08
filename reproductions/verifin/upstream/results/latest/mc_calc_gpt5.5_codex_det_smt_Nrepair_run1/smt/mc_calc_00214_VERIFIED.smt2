(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_income_loss_fy2026 Real)
(declare-const gross_profit_fy2026 Real)
(declare-const operating_expenses_fy2026 Real)

(assert (! (= gross_profit_fy2026 54865) :named evidence_gross_profit_fy2026))
(assert (! (= operating_expenses_fy2026 33975) :named evidence_operating_expenses_fy2026))

(assert (! (= computed_operating_income_loss_fy2026 (+ gross_profit_fy2026 (* (- 1) operating_expenses_fy2026))) :named formula_operating_income_loss_fy2026))

(assert (! (<= (- computed_operating_income_loss_fy2026 20890) 20.890000000000001) :named claim_upper))
(assert (! (<= (- 20890 computed_operating_income_loss_fy2026) 20.890000000000001) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)