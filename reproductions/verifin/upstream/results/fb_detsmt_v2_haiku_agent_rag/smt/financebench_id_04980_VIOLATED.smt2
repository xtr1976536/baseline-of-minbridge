(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_capital_expenditure Real)
(declare-const capex Real)

(assert (! (= capex 4625) :named evidence_capex))

(assert (! (= computed_capital_expenditure (/ capex 1000)) :named formula_capital_expenditure))

(assert (! (<= (- computed_capital_expenditure 4625) 4.625) :named claim_upper))
(assert (! (<= (- 4625 computed_capital_expenditure) 4.625) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)