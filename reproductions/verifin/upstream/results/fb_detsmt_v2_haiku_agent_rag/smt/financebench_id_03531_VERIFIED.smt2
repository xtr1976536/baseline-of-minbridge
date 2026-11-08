(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_total_current_assets Real)
(declare-const current_assets Real)

(assert (! (= current_assets 16525) :named evidence_current_assets))

(assert (! (= computed_total_current_assets current_assets) :named formula_total_current_assets))

(assert (! (<= (- computed_total_current_assets 16525) 16.524999999999999) :named claim_upper))
(assert (! (<= (- 16525 computed_total_current_assets) 16.524999999999999) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)