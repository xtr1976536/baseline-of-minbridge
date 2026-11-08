(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_capex Real)
(declare-const ppe_y1 Real)
(declare-const ppe_y2 Real)

(assert (! (= ppe_y1 -1577) :named evidence_ppe_y1))
(assert (! (= ppe_y2 -1577) :named evidence_ppe_y2))

(assert (! (= computed_capex (- ppe_y1 ppe_y2)) :named formula_capex))

(assert (! (<= (- computed_capex -1575) 1.575) :named claim_upper))
(assert (! (<= (- -1575 computed_capex) 1.575) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)