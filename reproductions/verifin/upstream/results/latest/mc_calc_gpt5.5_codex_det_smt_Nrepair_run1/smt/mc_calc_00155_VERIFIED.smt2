(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_expenses_fy2026 Real)
(declare-const general_and_administrative_expense_fy2026 Real)
(declare-const research_and_development_expense_fy2026 Real)
(declare-const restructuring_charges_fy2026 Real)
(declare-const selling_and_marketing_expense_fy2026 Real)

(assert (! (= general_and_administrative_expense_fy2026 3000) :named evidence_general_and_administrative_expense_fy2026))
(assert (! (= research_and_development_expense_fy2026 5993) :named evidence_research_and_development_expense_fy2026))
(assert (! (= restructuring_charges_fy2026 586) :named evidence_restructuring_charges_fy2026))
(assert (! (= selling_and_marketing_expense_fy2026 14345) :named evidence_selling_and_marketing_expense_fy2026))

(assert (! (= computed_operating_expenses_fy2026 (+ selling_and_marketing_expense_fy2026 general_and_administrative_expense_fy2026 research_and_development_expense_fy2026 restructuring_charges_fy2026)) :named formula_operating_expenses_fy2026))

(assert (! (<= (- computed_operating_expenses_fy2026 23924) 23.923999999999999) :named claim_upper))
(assert (! (<= (- 23924 computed_operating_expenses_fy2026) 23.923999999999999) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)