(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_retention_ratio Real)
(declare-const dividends_paid Real)
(declare-const net_income Real)

(assert (! (= dividends_paid 1244.5) :named evidence_dividends_paid))
(assert (! (= net_income 2707.3000000000002) :named evidence_net_income))

(assert (! (= computed_retention_ratio (* (/ (- net_income dividends_paid) net_income) 100)) :named formula_retention_ratio))
(assert (! (or (> net_income 0) (< net_income 0)) :named domain_retention_ratio_0))

(assert (! (<= (- computed_retention_ratio 86) 0.01) :named claim_upper))
(assert (! (<= (- 86 computed_retention_ratio) 0.01) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)