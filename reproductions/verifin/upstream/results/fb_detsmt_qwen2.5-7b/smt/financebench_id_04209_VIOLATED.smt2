(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_total_assets Real)
(declare-const assets Real)

(assert (! (= assets 29505) :named evidence_assets))

(assert (! (= computed_total_assets assets) :named formula_total_assets))

(assert (! (<= (- computed_total_assets 59268) 59.268000000000001) :named claim_upper))
(assert (! (<= (- 59268 computed_total_assets) 59.268000000000001) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)