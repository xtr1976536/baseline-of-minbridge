(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_kenvue_separation_cash_proceeds Real)
(declare-const cash_proceeds Real)

(assert (! (= cash_proceeds 13200) :named evidence_cash_proceeds))

(assert (! (= computed_kenvue_separation_cash_proceeds (/ cash_proceeds 1000)) :named formula_kenvue_separation_cash_proceeds))

(assert (! (<= (- computed_kenvue_separation_cash_proceeds 13200) 10) :named claim_upper))
(assert (! (<= (- 13200 computed_kenvue_separation_cash_proceeds) 10) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)