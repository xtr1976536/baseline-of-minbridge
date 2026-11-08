(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_net_income_attributable_to_shareholders Real)
(declare-const net_income Real)

(assert (! (= net_income 11588) :named evidence_net_income))

(assert (! (= computed_net_income_attributable_to_shareholders net_income) :named formula_net_income_attributable_to_shareholders))

(assert (! (<= (- computed_net_income_attributable_to_shareholders 11588) 11.588000000000001) :named claim_upper))
(assert (! (<= (- 11588 computed_net_income_attributable_to_shareholders) 11.588000000000001) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)