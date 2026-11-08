(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_income_margin_change Real)
(declare-const operating_income_end Real)
(declare-const operating_income_start Real)
(declare-const revenue_end Real)
(declare-const revenue_start Real)

(assert (! (= operating_income_end 21957) :named evidence_operating_income_end))
(assert (! (= operating_income_start 20437) :named evidence_operating_income_start))
(assert (! (= revenue_end 514405) :named evidence_revenue_end))
(assert (! (= revenue_start 500343) :named evidence_revenue_start))

(assert (! (= computed_operating_income_margin_change (- (* (/ operating_income_end revenue_end) 100) (* (/ operating_income_start revenue_start) 100))) :named formula_operating_income_margin_change))
(assert (! (or (> revenue_end 0) (< revenue_end 0)) :named domain_operating_income_margin_change_0))
(assert (! (or (> revenue_start 0) (< revenue_start 0)) :named domain_operating_income_margin_change_1))

(assert (! (<= (- computed_operating_income_margin_change 0.29999999999999999) 0.050000000000000003) :named claim_upper))
(assert (! (<= (- 0.29999999999999999 computed_operating_income_margin_change) 0.050000000000000003) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)