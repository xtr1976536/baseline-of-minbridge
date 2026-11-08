(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_income_yoy_change_percent Real)
(declare-const operating_income_2015 Real)
(declare-const operating_income_2016 Real)

(assert (! (= operating_income_2015 903.09500000000003) :named evidence_operating_income_2015))
(assert (! (= operating_income_2016 1493.6020000000001) :named evidence_operating_income_2016))

(assert (! (= computed_operating_income_yoy_change_percent (* (/ (- operating_income_2016 operating_income_2015) operating_income_2015) 100)) :named formula_operating_income_yoy_change_percent))
(assert (! (or (> operating_income_2015 0) (< operating_income_2015 0)) :named domain_operating_income_yoy_change_percent_0))

(assert (! (<= (- computed_operating_income_yoy_change_percent 12.800000000000001) 0.050000000000000003) :named claim_upper))
(assert (! (<= (- 12.800000000000001 computed_operating_income_yoy_change_percent) 0.050000000000000003) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)