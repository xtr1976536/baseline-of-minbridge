(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_fixed_asset_turnover_ratio Real)
(declare-const average_ppe Real)
(declare-const revenue Real)

(assert (! (= average_ppe 253) :named evidence_average_ppe))
(assert (! (= revenue 6490) :named evidence_revenue))

(assert (! (= computed_fixed_asset_turnover_ratio (* (/ revenue average_ppe) 100)) :named formula_fixed_asset_turnover_ratio))
(assert (! (or (> average_ppe 0) (< average_ppe 0)) :named domain_fixed_asset_turnover_ratio_0))

(assert (! (<= (- computed_fixed_asset_turnover_ratio 3.2400000000000002) 0.0050000000000000001) :named claim_upper))
(assert (! (<= (- 3.2400000000000002 computed_fixed_asset_turnover_ratio) 0.0050000000000000001) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)