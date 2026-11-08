(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_net_accounts_receivable Real)
(declare-const receivables Real)

(assert (! (= receivables 1615.9000000000001) :named evidence_receivables))

(assert (! (= computed_net_accounts_receivable receivables) :named formula_net_accounts_receivable))

(assert (! (<= (- computed_net_accounts_receivable 1615.9000000000001) 1.6159000000000001) :named claim_upper))
(assert (! (<= (- 1615.9000000000001 computed_net_accounts_receivable) 1.6159000000000001) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)