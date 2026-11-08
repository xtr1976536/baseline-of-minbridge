(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_days_payable_outstanding Real)
(declare-const accounts_payable_end Real)
(declare-const accounts_payable_start Real)
(declare-const cost_of_revenue Real)
(declare-const inventory_end Real)
(declare-const inventory_start Real)

(assert (! (= accounts_payable_end 34616) :named evidence_accounts_payable_end))
(assert (! (= accounts_payable_start 25309) :named evidence_accounts_payable_start))
(assert (! (= cost_of_revenue 111934) :named evidence_cost_of_revenue))
(assert (! (= inventory_end 16047) :named evidence_inventory_end))
(assert (! (= inventory_start 11461) :named evidence_inventory_start))

(assert (! (= computed_days_payable_outstanding (/ (* 365 (/ (+ accounts_payable_start accounts_payable_end) 2)) (+ cost_of_revenue (- inventory_end inventory_start)))) :named formula_days_payable_outstanding))
(assert (! (or (> (+ cost_of_revenue (- inventory_end inventory_start)) 0) (< (+ cost_of_revenue (- inventory_end inventory_start)) 0)) :named domain_days_payable_outstanding_0))

(assert (! (<= (- computed_days_payable_outstanding 64.319999999999993) 0.0050000000000000001) :named claim_upper))
(assert (! (<= (- 64.319999999999993 computed_days_payable_outstanding) 0.0050000000000000001) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)