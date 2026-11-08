(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_consumer_health_separation_gain Real)
(declare-const separation_gain Real)

(assert (! (= separation_gain 20000000000) :named evidence_separation_gain))

(assert (! (= computed_consumer_health_separation_gain (/ separation_gain 1000)) :named formula_consumer_health_separation_gain))

(assert (! (<= (- computed_consumer_health_separation_gain 20000) 0.01) :named claim_upper))
(assert (! (<= (- 20000 computed_consumer_health_separation_gain) 0.01) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)