(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_net_cash_provided_by_operating_activities Real)
(declare-const net_cash_provided_by_operating_activities Real)

(assert (! (= net_cash_provided_by_operating_activities 381.60300000000001) :named evidence_net_cash_provided_by_operating_activities))

(assert (! (= computed_net_cash_provided_by_operating_activities net_cash_provided_by_operating_activities) :named formula_net_cash_provided_by_operating_activities))

(assert (! (<= (- computed_net_cash_provided_by_operating_activities 381.60300000000001) 0.38160300000000003) :named claim_upper))
(assert (! (<= (- 381.60300000000001 computed_net_cash_provided_by_operating_activities) 0.38160300000000003) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)