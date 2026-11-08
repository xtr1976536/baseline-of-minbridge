(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_net_accounts_receivable Real)
(declare-const receivables Real)

(assert (! (= receivables 1615.9000000000001) :named evidence_receivables))

(assert (! (= computed_net_accounts_receivable receivables) :named formula_net_accounts_receivable))

(assert (! (<= (- computed_net_accounts_receivable 4625.8999999999996) 4.6258999999999997) :named claim_upper))
(assert (! (<= (- 4625.8999999999996 computed_net_accounts_receivable) 4.6258999999999997) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)