(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_net_ppne Real)
(declare-const ppe Real)

(assert (! (= ppe 8738) :named evidence_ppe))

(assert (! (= computed_net_ppne ppe) :named formula_net_ppne))

(assert (! (<= (- computed_net_ppne 8740) 8.740000000000002) :named claim_upper))
(assert (! (<= (- 8740 computed_net_ppne) 8.740000000000002) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)