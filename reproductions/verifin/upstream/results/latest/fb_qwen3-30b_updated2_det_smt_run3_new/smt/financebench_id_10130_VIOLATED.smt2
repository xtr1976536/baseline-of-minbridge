(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_days_payable_outstanding Real)
(declare-const accounts_payable_2019 Real)
(declare-const accounts_payable_2020 Real)
(declare-const cost_of_revenue_2020 Real)
(declare-const inventory_2019 Real)
(declare-const inventory_2020 Real)

(assert (! (= accounts_payable_2019 1587) :named evidence_accounts_payable_2019))
(assert (! (= accounts_payable_2020 1174) :named evidence_accounts_payable_2020))
(assert (! (= cost_of_revenue_2020 7772) :named evidence_cost_of_revenue_2020))
(assert (! (= inventory_2019 2320) :named evidence_inventory_2019))
(assert (! (= inventory_2020 2438) :named evidence_inventory_2020))

(assert (! (= computed_days_payable_outstanding (/ (* 365 (/ (+ accounts_payable_2019 accounts_payable_2020) 2)) (+ cost_of_revenue_2020 (- inventory_2020 inventory_2019)))) :named formula_days_payable_outstanding))
(assert (! (or (> (+ cost_of_revenue_2020 (- inventory_2020 inventory_2019)) 0) (< (+ cost_of_revenue_2020 (- inventory_2020 inventory_2019)) 0)) :named domain_days_payable_outstanding_0))

(assert (! (<= (- computed_days_payable_outstanding 45.670000000000002) 0.0050000000000000001) :named claim_upper))
(assert (! (<= (- 45.670000000000002 computed_days_payable_outstanding) 0.0050000000000000001) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)