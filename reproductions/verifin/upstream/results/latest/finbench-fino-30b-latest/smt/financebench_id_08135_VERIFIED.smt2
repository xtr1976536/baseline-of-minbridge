(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_revenue_yoy_change_percent Real)
(declare-const revenue_end Real)
(declare-const revenue_start Real)

(assert (! (= revenue_end 177866) :named evidence_revenue_end))
(assert (! (= revenue_start 135987) :named evidence_revenue_start))

(assert (! (= computed_revenue_yoy_change_percent (* (/ (- revenue_end revenue_start) revenue_start) 100)) :named formula_revenue_yoy_change_percent))
(assert (! (or (> revenue_start 0) (< revenue_start 0)) :named domain_revenue_yoy_change_percent_0))

(assert (! (<= (- computed_revenue_yoy_change_percent 30.800000000000001) 0.050000000000000003) :named claim_upper))
(assert (! (<= (- 30.800000000000001 computed_revenue_yoy_change_percent) 0.050000000000000003) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)