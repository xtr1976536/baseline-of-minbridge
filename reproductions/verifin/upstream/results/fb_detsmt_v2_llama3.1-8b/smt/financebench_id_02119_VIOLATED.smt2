(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_market_capitalization Real)
(declare-const shares_outstanding Real)

(assert (! (= shares_outstanding 804000000000000) :named evidence_shares_outstanding))

(assert (! (= computed_market_capitalization (* 206 shares_outstanding)) :named formula_market_capitalization))

(assert (! (<= (- computed_market_capitalization 66560) 66.560000000000002) :named claim_upper))
(assert (! (<= (- 66560 computed_market_capitalization) 66.560000000000002) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)