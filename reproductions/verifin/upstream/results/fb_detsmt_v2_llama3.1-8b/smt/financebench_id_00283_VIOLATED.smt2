(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_upjohn_spinoff_future_costs Real)
(declare-const percent_incurred Real)
(declare-const separation_costs Real)

(assert (! (= percent_incurred 700) :named evidence_percent_incurred))
(assert (! (= separation_costs 700) :named evidence_separation_costs))

(assert (! (= computed_upjohn_spinoff_future_costs (/ (* separation_costs (- 100 percent_incurred)) percent_incurred)) :named formula_upjohn_spinoff_future_costs))
(assert (! (or (> percent_incurred 0) (< percent_incurred 0)) :named domain_upjohn_spinoff_future_costs_0))

(assert (! (<= (- computed_upjohn_spinoff_future_costs 630) 0.63) :named claim_upper))
(assert (! (<= (- 630 computed_upjohn_spinoff_future_costs) 0.63) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)