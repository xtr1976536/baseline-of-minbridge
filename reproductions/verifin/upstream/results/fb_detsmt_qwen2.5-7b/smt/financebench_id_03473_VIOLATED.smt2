(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_return_on_assets Real)
(declare-const assets Real)
(declare-const net_income Real)

(assert (! (= assets 87896) :named evidence_assets))
(assert (! (= net_income 1248) :named evidence_net_income))

(assert (! (= computed_return_on_assets (/ net_income assets)) :named formula_return_on_assets))
(assert (! (or (> assets 0) (< assets 0)) :named domain_return_on_assets_0))

(assert (! (<= (- computed_return_on_assets 1.4099999999999999) 0.0050000000000000001) :named claim_upper))
(assert (! (<= (- 1.4099999999999999 computed_return_on_assets) 0.0050000000000000001) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)