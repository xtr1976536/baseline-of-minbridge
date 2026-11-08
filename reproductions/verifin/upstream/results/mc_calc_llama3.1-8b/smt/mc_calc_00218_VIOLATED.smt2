(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_income_before_income_taxes Real)
(declare-const Income_Loss_from_Continuing_Operations_before_Income_Tax Real)

(assert (! (= Income_Loss_from_Continuing_Operations_before_Income_Tax -4948.0) :named evidence_Income_Loss_from_Continuing_Operations_before_Income_Tax))

(assert (! (= computed_income_before_income_taxes (/ Income_Loss_from_Continuing_Operations_before_Income_Tax 1000000)) :named formula_income_before_income_taxes))

(assert (! (or (> 1000000 0) (< 1000000 0)) :named denom_nonzero))

(assert (! (<= (- computed_income_before_income_taxes 26015.0) 260.15) :named claim_upper))
(assert (! (<= (- 26015.0 computed_income_before_income_taxes) 260.15) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)