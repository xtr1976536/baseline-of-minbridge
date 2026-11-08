(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_days_payable_outstanding Real)
(declare-const accounts_payable_fy2016 Real)
(declare-const accounts_payable_fy2017 Real)
(declare-const cost_of_revenue_fy2017 Real)
(declare-const inventory_fy2016 Real)
(declare-const inventory_fy2017 Real)

(assert (! (= accounts_payable_fy2016 25309) :named evidence_accounts_payable_fy2016))
(assert (! (= accounts_payable_fy2017 34616) :named evidence_accounts_payable_fy2017))
(assert (! (= cost_of_revenue_fy2017 111934) :named evidence_cost_of_revenue_fy2017))
(assert (! (= inventory_fy2016 11461) :named evidence_inventory_fy2016))
(assert (! (= inventory_fy2017 16047) :named evidence_inventory_fy2017))

(assert (! (= computed_days_payable_outstanding (/ (* 365 (/ (+ accounts_payable_fy2016 accounts_payable_fy2017) 2)) (+ cost_of_revenue_fy2017 (- inventory_fy2017 inventory_fy2016)))) :named formula_days_payable_outstanding))
(assert (! (or (> (+ cost_of_revenue_fy2017 (- inventory_fy2017 inventory_fy2016)) 0) (< (+ cost_of_revenue_fy2017 (- inventory_fy2017 inventory_fy2016)) 0)) :named domain_days_payable_outstanding_0))

(assert (! (<= (- computed_days_payable_outstanding 93.890000000000001) 0.0050000000000000001) :named claim_upper))
(assert (! (<= (- 93.890000000000001 computed_days_payable_outstanding) 0.0050000000000000001) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)