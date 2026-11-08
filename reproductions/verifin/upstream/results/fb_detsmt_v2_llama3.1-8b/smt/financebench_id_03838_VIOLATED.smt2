(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_revenue_yoy_change_percent Real)
(declare-const revenue_2019 Real)
(declare-const revenue_2020 Real)

(assert (! (= revenue_2019 3710.9450000000002) :named evidence_revenue_2019))
(assert (! (= revenue_2020 3294.9780000000001) :named evidence_revenue_2020))

(assert (! (= computed_revenue_yoy_change_percent (* (/ (- revenue_2020 revenue_2019) revenue_2019) 100)) :named formula_revenue_yoy_change_percent))
(assert (! (or (> revenue_2019 0) (< revenue_2019 0)) :named domain_revenue_yoy_change_percent_0))

(assert (! (<= (- computed_revenue_yoy_change_percent 12.1) 0.050000000000000003) :named claim_upper))
(assert (! (<= (- 12.1 computed_revenue_yoy_change_percent) 0.050000000000000003) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)