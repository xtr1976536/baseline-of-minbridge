(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_net_working_capital Real)
(declare-const current_assets Real)
(declare-const current_liabilities Real)

(assert (! (= current_assets 19815) :named evidence_current_assets))
(assert (! (= current_liabilities 13997) :named evidence_current_liabilities))

(assert (! (= computed_net_working_capital (- current_assets current_liabilities)) :named formula_net_working_capital))

(assert (! (<= (- computed_net_working_capital 5818) 5.8180000000000005) :named claim_upper))
(assert (! (<= (- 5818 computed_net_working_capital) 5.8180000000000005) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)