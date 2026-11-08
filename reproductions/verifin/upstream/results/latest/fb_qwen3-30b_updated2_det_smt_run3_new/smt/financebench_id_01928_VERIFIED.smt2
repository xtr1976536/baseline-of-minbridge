(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_adjusted_non_gaap_ebitda Real)
(declare-const adjusted_ebitda Real)

(assert (! (= adjusted_ebitda 2018) :named evidence_adjusted_ebitda))

(assert (! (= computed_adjusted_non_gaap_ebitda adjusted_ebitda) :named formula_adjusted_non_gaap_ebitda))

(assert (! (<= (- computed_adjusted_non_gaap_ebitda 2018) 2.0180000000000002) :named claim_upper))
(assert (! (<= (- 2018 computed_adjusted_non_gaap_ebitda) 2.0180000000000002) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)