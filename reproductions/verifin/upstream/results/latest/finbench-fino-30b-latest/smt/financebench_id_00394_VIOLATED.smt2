(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_net_income Real)
(declare-const net_income Real)

(assert (! (= net_income 3100) :named evidence_net_income))

(assert (! (= computed_net_income net_income) :named formula_net_income))

(assert (! (<= (- computed_net_income 8649) 8.6490000000000009) :named claim_upper))
(assert (! (<= (- 8649 computed_net_income) 8.6490000000000009) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)