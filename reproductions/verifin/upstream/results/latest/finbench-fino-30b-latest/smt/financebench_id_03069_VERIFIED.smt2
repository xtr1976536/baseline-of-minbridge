(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_depreciation_and_amortization_margin Real)
(declare-const depreciation_and_amortization Real)
(declare-const net_revenue Real)

(assert (! (= depreciation_and_amortization 167) :named evidence_depreciation_and_amortization))
(assert (! (= net_revenue 3991) :named evidence_net_revenue))

(assert (! (= computed_depreciation_and_amortization_margin (* (/ depreciation_and_amortization net_revenue) 100)) :named formula_depreciation_and_amortization_margin))
(assert (! (or (> net_revenue 0) (< net_revenue 0)) :named domain_depreciation_and_amortization_margin_0))

(assert (! (<= (- computed_depreciation_and_amortization_margin 4.1840000000000002) 0.0041840000000000002) :named claim_upper))
(assert (! (<= (- 4.1840000000000002 computed_depreciation_and_amortization_margin) 0.0041840000000000002) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)