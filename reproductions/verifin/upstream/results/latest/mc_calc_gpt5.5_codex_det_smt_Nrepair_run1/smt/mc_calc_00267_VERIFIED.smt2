(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_net_cash_provided_by_used_in_investing_activities_fy2026 Real)
(declare-const payments_to_acquire_available_for_sale_securities_debt_fy2026 Real)
(declare-const payments_to_acquire_businesses_net_of_cash_acquired_fy2026 Real)
(declare-const payments_to_acquire_longterm_investments_fy2026 Real)
(declare-const payments_to_acquire_property_plant_and_equipment_fy2026 Real)
(declare-const proceeds_from_maturities_prepayments_and_calls_of_available_for_sale_securities_fy2026 Real)
(declare-const proceeds_from_sale_of_available_for_sale_securities_debt_fy2026 Real)
(declare-const proceeds_from_sale_of_longterm_investments_fy2026 Real)

(assert (! (= payments_to_acquire_available_for_sale_securities_debt_fy2026 3763) :named evidence_payments_to_acquire_available_for_sale_securities_debt_fy2026))
(assert (! (= payments_to_acquire_businesses_net_of_cash_acquired_fy2026 9268) :named evidence_payments_to_acquire_businesses_net_of_cash_acquired_fy2026))
(assert (! (= payments_to_acquire_longterm_investments_fy2026 1958) :named evidence_payments_to_acquire_longterm_investments_fy2026))
(assert (! (= payments_to_acquire_property_plant_and_equipment_fy2026 594) :named evidence_payments_to_acquire_property_plant_and_equipment_fy2026))
(assert (! (= proceeds_from_maturities_prepayments_and_calls_of_available_for_sale_securities_fy2026 2395) :named evidence_proceeds_from_maturities_prepayments_and_calls_of_available_for_sale_securities_fy2026))
(assert (! (= proceeds_from_sale_of_available_for_sale_securities_debt_fy2026 4414) :named evidence_proceeds_from_sale_of_available_for_sale_securities_debt_fy2026))
(assert (! (= proceeds_from_sale_of_longterm_investments_fy2026 184) :named evidence_proceeds_from_sale_of_longterm_investments_fy2026))

(assert (! (= computed_net_cash_provided_by_used_in_investing_activities_fy2026 (+ (* (- 1) payments_to_acquire_businesses_net_of_cash_acquired_fy2026) (* (- 1) payments_to_acquire_longterm_investments_fy2026) proceeds_from_sale_of_longterm_investments_fy2026 (* (- 1) payments_to_acquire_available_for_sale_securities_debt_fy2026) proceeds_from_sale_of_available_for_sale_securities_debt_fy2026 proceeds_from_maturities_prepayments_and_calls_of_available_for_sale_securities_fy2026 (* (- 1) payments_to_acquire_property_plant_and_equipment_fy2026))) :named formula_net_cash_provided_by_used_in_investing_activities_fy2026))

(assert (! (<= (- computed_net_cash_provided_by_used_in_investing_activities_fy2026 -8590) 8.5899999999999999) :named claim_upper))
(assert (! (<= (- -8590 computed_net_cash_provided_by_used_in_investing_activities_fy2026) 8.5899999999999999) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)