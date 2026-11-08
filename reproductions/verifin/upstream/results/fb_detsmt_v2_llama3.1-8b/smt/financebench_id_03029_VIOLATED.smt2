(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_capital_expenditure Real)
(declare-const capex Real)

(assert (! (= capex -1577) :named evidence_capex))

(assert (! (= computed_capital_expenditure capex) :named formula_capital_expenditure))

(assert (! (<= (- computed_capital_expenditure 1577) 1.577) :named claim_upper))
(assert (! (<= (- 1577 computed_capital_expenditure) 1.577) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)