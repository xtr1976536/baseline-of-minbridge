(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_net_ppe Real)
(declare-const ppe Real)

(assert (! (= ppe 12645) :named evidence_ppe))

(assert (! (= computed_net_ppe ppe) :named formula_net_ppe))

(assert (! (<= (- computed_net_ppe 12645) 12.645) :named claim_upper))
(assert (! (<= (- 12645 computed_net_ppe) 12.645) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)