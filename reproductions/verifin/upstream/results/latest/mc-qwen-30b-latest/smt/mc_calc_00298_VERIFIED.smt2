(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_net_cash_provided_by_used_in_investing_activities_fy2026 Real)
(declare-const payments_for_proceeds_from_other_investing_activities_fy2026 Real)
(declare-const payments_to_acquire_businesses_net_of_cash_acquired_fy2026 Real)
(declare-const payments_to_acquire_productive_assets_fy2026 Real)

(assert (! (= payments_for_proceeds_from_other_investing_activities_fy2026 -109) :named evidence_payments_for_proceeds_from_other_investing_activities_fy2026))
(assert (! (= payments_to_acquire_businesses_net_of_cash_acquired_fy2026 5410) :named evidence_payments_to_acquire_businesses_net_of_cash_acquired_fy2026))
(assert (! (= payments_to_acquire_productive_assets_fy2026 3679) :named evidence_payments_to_acquire_productive_assets_fy2026))

(assert (! (= computed_net_cash_provided_by_used_in_investing_activities_fy2026 (+ (* (- 1) payments_to_acquire_productive_assets_fy2026) (* (- 1) payments_to_acquire_businesses_net_of_cash_acquired_fy2026) (* (- 1) payments_for_proceeds_from_other_investing_activities_fy2026))) :named formula_net_cash_provided_by_used_in_investing_activities_fy2026))

(assert (! (<= (- computed_net_cash_provided_by_used_in_investing_activities_fy2026 -8980) 8.9800000000000004) :named claim_upper))
(assert (! (<= (- -8980 computed_net_cash_provided_by_used_in_investing_activities_fy2026) 8.9800000000000004) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)