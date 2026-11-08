(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_free_cash_flow Real)
(declare-const capex Real)
(declare-const operating_cash_flow Real)

(assert (! (= capex -460.80000000000001) :named evidence_capex))
(assert (! (= operating_cash_flow 3676.1999999999998) :named evidence_operating_cash_flow))

(assert (! (= computed_free_cash_flow (- operating_cash_flow capex)) :named formula_free_cash_flow))

(assert (! (<= (- computed_free_cash_flow 3215.4000000000001) 3.2154000000000003) :named claim_upper))
(assert (! (<= (- 3215.4000000000001 computed_free_cash_flow) 3.2154000000000003) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)