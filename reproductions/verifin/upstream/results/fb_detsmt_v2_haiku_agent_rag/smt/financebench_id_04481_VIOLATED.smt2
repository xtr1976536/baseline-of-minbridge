(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_unadjusted_ebitda_margin_percent Real)
(declare-const depreciation_amortization Real)
(declare-const net_revenue Real)
(declare-const operating_income Real)

(assert (! (= depreciation_amortization 2763) :named evidence_depreciation_amortization))
(assert (! (= net_revenue 86392) :named evidence_net_revenue))
(assert (! (= operating_income 11512) :named evidence_operating_income))

(assert (! (= computed_unadjusted_ebitda_margin_percent (* (/ (+ operating_income depreciation_amortization) net_revenue) 100)) :named formula_unadjusted_ebitda_margin_percent))
(assert (! (or (> net_revenue 0) (< net_revenue 0)) :named domain_unadjusted_ebitda_margin_percent_0))

(assert (! (<= (- computed_unadjusted_ebitda_margin_percent 16.800000000000001) 0.050000000000000003) :named claim_upper))
(assert (! (<= (- 16.800000000000001 computed_unadjusted_ebitda_margin_percent) 0.050000000000000003) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)