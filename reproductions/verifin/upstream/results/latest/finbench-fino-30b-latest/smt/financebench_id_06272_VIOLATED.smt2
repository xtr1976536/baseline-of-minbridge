(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_dividend_payout_ratio Real)
(declare-const dividends_paid Real)
(declare-const net_income Real)

(assert (! (= dividends_paid 7616) :named evidence_dividends_paid))
(assert (! (= net_income 9542) :named evidence_net_income))

(assert (! (= computed_dividend_payout_ratio (/ dividends_paid net_income)) :named formula_dividend_payout_ratio))
(assert (! (or (> net_income 0) (< net_income 0)) :named domain_dividend_payout_ratio_0))

(assert (! (<= (- computed_dividend_payout_ratio 79.819999999999993) 0.079819999999999988) :named claim_upper))
(assert (! (<= (- 79.819999999999993 computed_dividend_payout_ratio) 0.079819999999999988) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)