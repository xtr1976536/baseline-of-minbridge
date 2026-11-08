(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_dividend_payout_ratio Real)
(declare-const dividends_paid Real)
(declare-const net_income_attributable_to_shareholders Real)

(assert (! (= dividends_paid -7616) :named evidence_dividends_paid))
(assert (! (= net_income_attributable_to_shareholders 9542) :named evidence_net_income_attributable_to_shareholders))

(assert (! (= computed_dividend_payout_ratio (* (/ dividends_paid net_income_attributable_to_shareholders) 100)) :named formula_dividend_payout_ratio))
(assert (! (or (> net_income_attributable_to_shareholders 0) (< net_income_attributable_to_shareholders 0)) :named domain_dividend_payout_ratio_0))

(assert (! (<= (- computed_dividend_payout_ratio 20.219999999999999) 0.020219999999999998) :named claim_upper))
(assert (! (<= (- 20.219999999999999 computed_dividend_payout_ratio) 0.020219999999999998) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)