(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_cash_flow_ratio Real)
(declare-const current_liabilities Real)
(declare-const operating_cash_flow Real)

(assert (! (= current_liabilities 3527.4569999999999) :named evidence_current_liabilities))
(assert (! (= operating_cash_flow 2912.8530000000001) :named evidence_operating_cash_flow))

(assert (! (= computed_operating_cash_flow_ratio (/ operating_cash_flow current_liabilities)) :named formula_operating_cash_flow_ratio))
(assert (! (or (> current_liabilities 0) (< current_liabilities 0)) :named domain_operating_cash_flow_ratio_0))

(assert (! (<= (- computed_operating_cash_flow_ratio 0.81000000000000005) 0.0050000000000000001) :named claim_upper))
(assert (! (<= (- 0.81000000000000005 computed_operating_cash_flow_ratio) 0.0050000000000000001) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)