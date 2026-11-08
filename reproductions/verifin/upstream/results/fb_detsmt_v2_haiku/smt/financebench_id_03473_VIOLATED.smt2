(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_return_on_assets Real)
(declare-const assets_end Real)
(declare-const assets_start Real)
(declare-const net_income Real)

(assert (! (= assets_end 87896) :named evidence_assets_end))
(assert (! (= assets_start 87270) :named evidence_assets_start))
(assert (! (= net_income 1248) :named evidence_net_income))

(assert (! (= computed_return_on_assets (/ net_income (/ (+ assets_start assets_end) 2))) :named formula_return_on_assets))
(assert (! (or (> (/ (+ assets_start assets_end) 2) 0) (< (/ (+ assets_start assets_end) 2) 0)) :named domain_return_on_assets_0))

(assert (! (<= (- computed_return_on_assets 1.4299999999999999) 0.0050000000000000001) :named claim_upper))
(assert (! (<= (- 1.4299999999999999 computed_return_on_assets) 0.0050000000000000001) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)