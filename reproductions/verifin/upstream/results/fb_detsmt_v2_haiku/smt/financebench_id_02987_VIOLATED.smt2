(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_fixed_asset_turnover_ratio Real)
(declare-const ppe_end Real)
(declare-const ppe_start Real)
(declare-const revenue Real)

(assert (! (= ppe_end 253) :named evidence_ppe_end))
(assert (! (= ppe_start 282) :named evidence_ppe_start))
(assert (! (= revenue 6489) :named evidence_revenue))

(assert (! (= computed_fixed_asset_turnover_ratio (/ revenue (/ (+ ppe_start ppe_end) 2))) :named formula_fixed_asset_turnover_ratio))
(assert (! (or (> (/ (+ ppe_start ppe_end) 2) 0) (< (/ (+ ppe_start ppe_end) 2) 0)) :named domain_fixed_asset_turnover_ratio_0))

(assert (! (<= (- computed_fixed_asset_turnover_ratio 25.66) 0.0050000000000000001) :named claim_upper))
(assert (! (<= (- 25.66 computed_fixed_asset_turnover_ratio) 0.0050000000000000001) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)