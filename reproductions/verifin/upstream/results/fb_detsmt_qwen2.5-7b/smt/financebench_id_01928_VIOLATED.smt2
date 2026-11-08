(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_adjusted_non_gaap_ebitda Real)
(declare-const depreciation_amortization Real)
(declare-const operating_income Real)

(assert (! (= depreciation_amortization 569) :named evidence_depreciation_amortization))
(assert (! (= operating_income 1250) :named evidence_operating_income))

(assert (! (= computed_adjusted_non_gaap_ebitda (+ operating_income depreciation_amortization)) :named formula_adjusted_non_gaap_ebitda))

(assert (! (<= (- computed_adjusted_non_gaap_ebitda 2018) 2.0180000000000002) :named claim_upper))
(assert (! (<= (- 2018 computed_adjusted_non_gaap_ebitda) 2.0180000000000002) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)