(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_depreciation_and_amortization_margin Real)
(declare-const depreciation_and_amortization Real)
(declare-const revenue Real)

(assert (! (= depreciation_and_amortization 167) :named evidence_depreciation_and_amortization))
(assert (! (= revenue 3991) :named evidence_revenue))

(assert (! (= computed_depreciation_and_amortization_margin (* (/ depreciation_and_amortization revenue) 100)) :named formula_depreciation_and_amortization_margin))
(assert (! (or (> revenue 0) (< revenue 0)) :named domain_depreciation_and_amortization_margin_0))

(assert (! (<= (- computed_depreciation_and_amortization_margin 4.1799999999999997) 0.0050000000000000001) :named claim_upper))
(assert (! (<= (- 4.1799999999999997 computed_depreciation_and_amortization_margin) 0.0050000000000000001) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)