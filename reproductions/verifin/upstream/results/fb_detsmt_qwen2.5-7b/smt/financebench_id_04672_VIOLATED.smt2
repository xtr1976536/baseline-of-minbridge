(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_net_ppne Real)
(declare-const accumulated_depreciation Real)
(declare-const ppe Real)

(assert (! (= accumulated_depreciation -16135) :named evidence_accumulated_depreciation))
(assert (! (= ppe 8738) :named evidence_ppe))

(assert (! (= computed_net_ppne (- ppe accumulated_depreciation)) :named formula_net_ppne))

(assert (! (<= (- computed_net_ppne 8738) 8.7379999999999995) :named claim_upper))
(assert (! (<= (- 8738 computed_net_ppne) 8.7379999999999995) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)