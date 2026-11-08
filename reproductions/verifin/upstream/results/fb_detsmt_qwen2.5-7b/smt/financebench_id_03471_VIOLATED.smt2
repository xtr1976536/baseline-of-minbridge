(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_working_capital_ratio Real)
(declare-const current_assets Real)
(declare-const current_liabilities Real)

(assert (! (= current_assets 5121.3000000000002) :named evidence_current_assets))
(assert (! (= current_liabilities 7491.5) :named evidence_current_liabilities))

(assert (! (= computed_working_capital_ratio (* (/ current_assets current_liabilities) 100)) :named formula_working_capital_ratio))
(assert (! (or (> current_liabilities 0) (< current_liabilities 0)) :named domain_working_capital_ratio_0))

(assert (! (<= (- computed_working_capital_ratio 0.68000000000000005) 0.0050000000000000001) :named claim_upper))
(assert (! (<= (- 0.68000000000000005 computed_working_capital_ratio) 0.0050000000000000001) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)