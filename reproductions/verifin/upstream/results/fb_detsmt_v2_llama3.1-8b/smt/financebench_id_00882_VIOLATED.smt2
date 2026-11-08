(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_unsecured_five_year_revolving_credit_agreement_increase Real)
(declare-const new_credit_agreement_amount Real)
(declare-const prior_credit_agreement_amount Real)

(assert (! (= new_credit_agreement_amount 4200000000) :named evidence_new_credit_agreement_amount))
(assert (! (= prior_credit_agreement_amount 3800000000) :named evidence_prior_credit_agreement_amount))

(assert (! (= computed_unsecured_five_year_revolving_credit_agreement_increase (- new_credit_agreement_amount prior_credit_agreement_amount)) :named formula_unsecured_five_year_revolving_credit_agreement_increase))

(assert (! (<= (- computed_unsecured_five_year_revolving_credit_agreement_increase 4950000000000) 4950000000) :named claim_upper))
(assert (! (<= (- 4950000000000 computed_unsecured_five_year_revolving_credit_agreement_increase) 4950000000) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)