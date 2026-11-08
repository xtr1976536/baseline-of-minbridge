(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_revenue_cagr_2year Real)
(declare-const revenue_end Real)
(declare-const revenue_start Real)

(assert (! (= revenue_end 65984) :named evidence_revenue_end))
(assert (! (= revenue_start 65398) :named evidence_revenue_start))

(assert (! (= (* revenue_start (+ 1 (/ computed_revenue_cagr_2year 100)) (+ 1 (/ computed_revenue_cagr_2year 100))) revenue_end) :named formula_revenue_cagr_2year))
(assert (! (> computed_revenue_cagr_2year -100) :named domain_revenue_cagr_2year_0))

(assert (! (<= (- computed_revenue_cagr_2year 0.80000000000000004) 0.050000000000000003) :named claim_upper))
(assert (! (<= (- 0.80000000000000004 computed_revenue_cagr_2year) 0.050000000000000003) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)