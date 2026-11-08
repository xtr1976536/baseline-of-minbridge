(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_cash_flow Real)
(declare-const operating_cash_flow Real)

(assert (! (= operating_cash_flow 381.60300000000001) :named evidence_operating_cash_flow))

(assert (! (= computed_operating_cash_flow operating_cash_flow) :named formula_operating_cash_flow))

(assert (! (<= (- computed_operating_cash_flow 381603) 381.60300000000001) :named claim_upper))
(assert (! (<= (- 381603 computed_operating_cash_flow) 381.60300000000001) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)