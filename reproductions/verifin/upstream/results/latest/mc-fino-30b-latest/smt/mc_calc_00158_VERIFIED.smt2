(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_expenses_fy2026 Real)
(declare-const depreciation_and_amortization_fy2026 Real)
(declare-const selling_general_and_administrative_expense_fy2026 Real)

(assert (! (= depreciation_and_amortization_fy2026 3273) :named evidence_depreciation_and_amortization_fy2026))
(assert (! (= selling_general_and_administrative_expense_fy2026 30702) :named evidence_selling_general_and_administrative_expense_fy2026))

(assert (! (= computed_operating_expenses_fy2026 (+ selling_general_and_administrative_expense_fy2026 depreciation_and_amortization_fy2026)) :named formula_operating_expenses_fy2026))

(assert (! (<= (- computed_operating_expenses_fy2026 33975) 33.975000000000001) :named claim_upper))
(assert (! (<= (- 33975 computed_operating_expenses_fy2026) 33.975000000000001) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)