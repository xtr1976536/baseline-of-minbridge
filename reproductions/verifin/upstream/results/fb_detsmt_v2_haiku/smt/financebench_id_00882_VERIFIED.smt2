(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_total_unsecured_revolving_credit_capacity Real)
(declare-const credit_agreement_364day Real)
(declare-const credit_agreement_5year Real)

(assert (! (= credit_agreement_364day 4200) :named evidence_credit_agreement_364day))
(assert (! (= credit_agreement_5year 4200) :named evidence_credit_agreement_5year))

(assert (! (= computed_total_unsecured_revolving_credit_capacity (+ credit_agreement_364day credit_agreement_5year)) :named formula_total_unsecured_revolving_credit_capacity))

(assert (! (<= (- computed_total_unsecured_revolving_credit_capacity 8400) 0.01) :named claim_upper))
(assert (! (<= (- 8400 computed_total_unsecured_revolving_credit_capacity) 0.01) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)