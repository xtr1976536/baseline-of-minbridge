(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_unadjusted_ebitda_less_capex Real)
(declare-const capex Real)
(declare-const depreciation_amortization Real)
(declare-const operating_income Real)

(assert (! (= capex -5207) :named evidence_capex))
(assert (! (= depreciation_amortization 2763) :named evidence_depreciation_amortization))
(assert (! (= operating_income 11512) :named evidence_operating_income))

(assert (! (= computed_unadjusted_ebitda_less_capex (- (+ operating_income depreciation_amortization) capex)) :named formula_unadjusted_ebitda_less_capex))

(assert (! (<= (- computed_unadjusted_ebitda_less_capex 9068) 9.0679999999999996) :named claim_upper))
(assert (! (<= (- 9068 computed_unadjusted_ebitda_less_capex) 9.0679999999999996) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)