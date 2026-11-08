(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_inventory_turnover_ratio Real)
(declare-const cost_of_revenue Real)
(declare-const inventory_end Real)
(declare-const inventory_start Real)

(assert (! (= cost_of_revenue 24576) :named evidence_cost_of_revenue))
(assert (! (= inventory_end 6854) :named evidence_inventory_end))
(assert (! (= inventory_start 7367) :named evidence_inventory_start))

(assert (! (= computed_inventory_turnover_ratio (/ cost_of_revenue (/ (+ inventory_start inventory_end) 2))) :named formula_inventory_turnover_ratio))
(assert (! (or (> (/ (+ inventory_start inventory_end) 2) 0) (< (/ (+ inventory_start inventory_end) 2) 0)) :named domain_inventory_turnover_ratio_0))

(assert (! (<= (- computed_inventory_turnover_ratio 3.5) 0.0050000000000000001) :named claim_upper))
(assert (! (<= (- 3.5 computed_inventory_turnover_ratio) 0.0050000000000000001) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)