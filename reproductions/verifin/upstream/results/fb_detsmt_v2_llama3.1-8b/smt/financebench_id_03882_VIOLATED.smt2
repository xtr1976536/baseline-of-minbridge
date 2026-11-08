(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_net_accounts_receivable Real)
(declare-const receivables Real)

(assert (! (= receivables 1615.9000000000001) :named evidence_receivables))

(assert (! (= computed_net_accounts_receivable receivables) :named formula_net_accounts_receivable))

(assert (! (<= (- computed_net_accounts_receivable 3973.5999999999999) 3.9735999999999998) :named claim_upper))
(assert (! (<= (- 3973.5999999999999 computed_net_accounts_receivable) 3.9735999999999998) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)