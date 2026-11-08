(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_unadjusted_ebitda_margin_percent Real)
(declare-const depreciation_amortization Real)
(declare-const dvd_content_amortization Real)
(declare-const operating_income Real)
(declare-const revenue Real)
(declare-const streaming_content_amortization Real)

(assert (! (= depreciation_amortization 62.283000000000001) :named evidence_depreciation_amortization))
(assert (! (= dvd_content_amortization 79.379999999999995) :named evidence_dvd_content_amortization))
(assert (! (= operating_income 305.82600000000002) :named evidence_operating_income))
(assert (! (= revenue 6779.5110000000004) :named evidence_revenue))
(assert (! (= streaming_content_amortization 3.4053820000000004) :named evidence_streaming_content_amortization))

(assert (! (= computed_unadjusted_ebitda_margin_percent (* (/ (+ operating_income depreciation_amortization dvd_content_amortization streaming_content_amortization) revenue) 100)) :named formula_unadjusted_ebitda_margin_percent))
(assert (! (or (> revenue 0) (< revenue 0)) :named domain_unadjusted_ebitda_margin_percent_0))

(assert (! (<= (- computed_unadjusted_ebitda_margin_percent 4.5099999999999998) 0.0050000000000000001) :named claim_upper))
(assert (! (<= (- 4.5099999999999998 computed_unadjusted_ebitda_margin_percent) 0.0050000000000000001) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)