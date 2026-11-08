(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_expected_retiree_benefit_payments Real)
(declare-const health_care_life_insurance Real)
(declare-const pension_benefits Real)

(assert (! (= health_care_life_insurance 862) :named evidence_health_care_life_insurance))
(assert (! (= pension_benefits 1097) :named evidence_pension_benefits))

(assert (! (= computed_expected_retiree_benefit_payments (+ pension_benefits health_care_life_insurance)) :named formula_expected_retiree_benefit_payments))

(assert (! (<= (- computed_expected_retiree_benefit_payments 862) 0.86199999999999999) :named claim_upper))
(assert (! (<= (- 862 computed_expected_retiree_benefit_payments) 0.86199999999999999) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)