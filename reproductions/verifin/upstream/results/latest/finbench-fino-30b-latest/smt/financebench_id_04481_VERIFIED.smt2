(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_unadjusted_ebitda_margin_percent Real)
(declare-const depreciation_amortization Real)
(declare-const operating_income Real)
(declare-const revenue Real)

(assert (! (= depreciation_amortization 2763) :named evidence_depreciation_amortization))
(assert (! (= operating_income 11512) :named evidence_operating_income))
(assert (! (= revenue 86392) :named evidence_revenue))

(assert (! (= computed_unadjusted_ebitda_margin_percent (* (/ (+ operating_income depreciation_amortization) revenue) 100)) :named formula_unadjusted_ebitda_margin_percent))
(assert (! (or (> revenue 0) (< revenue 0)) :named domain_unadjusted_ebitda_margin_percent_0))

(assert (! (<= (- computed_unadjusted_ebitda_margin_percent 16.52) 0.01652) :named claim_upper))
(assert (! (<= (- 16.52 computed_unadjusted_ebitda_margin_percent) 0.01652) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)