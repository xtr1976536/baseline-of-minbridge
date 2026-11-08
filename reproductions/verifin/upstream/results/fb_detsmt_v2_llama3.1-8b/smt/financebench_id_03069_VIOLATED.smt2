(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_depreciation_and_amortization_margin Real)
(declare-const depreciation_and_amortization Real)
(declare-const net_revenue Real)

(assert (! (= depreciation_and_amortization 167) :named evidence_depreciation_and_amortization))
(assert (! (= net_revenue 3991) :named evidence_net_revenue))

(assert (! (= computed_depreciation_and_amortization_margin (* (/ (+ 167 203) 3991) 100)) :named formula_depreciation_and_amortization_margin))

(assert (! (<= (- computed_depreciation_and_amortization_margin 4.1799999999999997) 0.050000000000000003) :named claim_upper))
(assert (! (<= (- 4.1799999999999997 computed_depreciation_and_amortization_margin) 0.050000000000000003) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)