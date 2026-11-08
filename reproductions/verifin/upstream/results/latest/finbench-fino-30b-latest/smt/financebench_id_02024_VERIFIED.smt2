(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_expected_retiree_benefit_payments Real)
(declare-const health_care_life_insurance Real)
(declare-const pension_benefits Real)

(assert (! (= health_care_life_insurance 862) :named evidence_health_care_life_insurance))
(assert (! (= pension_benefits 1097) :named evidence_pension_benefits))

(assert (! (= computed_expected_retiree_benefit_payments (+ pension_benefits health_care_life_insurance)) :named formula_expected_retiree_benefit_payments))

(assert (! (<= (- computed_expected_retiree_benefit_payments 1959) 1.9590000000000001) :named claim_upper))
(assert (! (<= (- 1959 computed_expected_retiree_benefit_payments) 1.9590000000000001) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)