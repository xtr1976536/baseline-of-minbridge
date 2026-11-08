(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_income_yoy_change_percent Real)
(declare-const operating_income_end Real)
(declare-const operating_income_start Real)

(assert (! (= operating_income_end 1493.6020000000001) :named evidence_operating_income_end))
(assert (! (= operating_income_start 903.09500000000003) :named evidence_operating_income_start))

(assert (! (= computed_operating_income_yoy_change_percent (* (/ (- operating_income_end operating_income_start) operating_income_start) 100)) :named formula_operating_income_yoy_change_percent))
(assert (! (or (> operating_income_start 0) (< operating_income_start 0)) :named domain_operating_income_yoy_change_percent_0))

(assert (! (<= (- computed_operating_income_yoy_change_percent 65.400000000000006) 0.050000000000000003) :named claim_upper))
(assert (! (<= (- 65.400000000000006 computed_operating_income_yoy_change_percent) 0.050000000000000003) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)