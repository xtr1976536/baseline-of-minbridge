(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_unadjusted_ebitda Real)
(declare-const depreciation_amortization Real)
(declare-const operating_income Real)

(assert (! (= depreciation_amortization 636) :named evidence_depreciation_amortization))
(assert (! (= operating_income 1196) :named evidence_operating_income))

(assert (! (= computed_unadjusted_ebitda (+ operating_income depreciation_amortization)) :named formula_unadjusted_ebitda))

(assert (! (<= (- computed_unadjusted_ebitda 1899) 1.899) :named claim_upper))
(assert (! (<= (- 1899 computed_unadjusted_ebitda) 1.899) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)