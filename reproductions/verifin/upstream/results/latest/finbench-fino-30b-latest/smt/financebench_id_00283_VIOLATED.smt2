(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_expected_future_separation_costs Real)
(declare-const incurred_separation_costs Real)
(declare-const total_expected_separation_costs Real)

(assert (! (= incurred_separation_costs 630) :named evidence_incurred_separation_costs))
(assert (! (= total_expected_separation_costs 700) :named evidence_total_expected_separation_costs))

(assert (! (= computed_expected_future_separation_costs (- total_expected_separation_costs incurred_separation_costs)) :named formula_expected_future_separation_costs))

(assert (! (<= (- computed_expected_future_separation_costs 700) 0.70000000000000007) :named claim_upper))
(assert (! (<= (- 700 computed_expected_future_separation_costs) 0.70000000000000007) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)