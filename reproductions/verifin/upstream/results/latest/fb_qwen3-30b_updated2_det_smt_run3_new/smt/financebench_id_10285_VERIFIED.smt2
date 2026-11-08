(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_net_ppne Real)
(declare-const ppe Real)

(assert (! (= ppe 12645) :named evidence_ppe))

(assert (! (= computed_net_ppne ppe) :named formula_net_ppne))

(assert (! (<= (- computed_net_ppne 12645) 12.645) :named claim_upper))
(assert (! (<= (- 12645 computed_net_ppne) 12.645) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)