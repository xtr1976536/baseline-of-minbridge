(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_cash_dividends_paid Real)
(declare-const dividends_paid Real)

(assert (! (= dividends_paid 389) :named evidence_dividends_paid))

(assert (! (= computed_cash_dividends_paid (/ dividends_paid 1000)) :named formula_cash_dividends_paid))

(assert (! (<= (- computed_cash_dividends_paid 389000) 500) :named claim_upper))
(assert (! (<= (- 389000 computed_cash_dividends_paid) 500) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)