(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_accounts_payable Real)
(declare-const accounts_payable Real)

(assert (! (= accounts_payable 302.57800000000003) :named evidence_accounts_payable))

(assert (! (= computed_accounts_payable accounts_payable) :named formula_accounts_payable))

(assert (! (<= (- computed_accounts_payable 302.57799999999997) 0.30257799999999996) :named claim_upper))
(assert (! (<= (- 302.57799999999997 computed_accounts_payable) 0.30257799999999996) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)