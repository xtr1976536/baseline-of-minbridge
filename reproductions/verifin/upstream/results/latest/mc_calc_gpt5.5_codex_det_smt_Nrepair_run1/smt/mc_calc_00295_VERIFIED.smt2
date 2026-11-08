(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_net_cash_provided_by_used_in_financing_activities_fy2026 Real)
(declare-const finance_lease_principal_payments_fy2026 Real)
(declare-const payments_for_repurchase_of_common_stock_fy2026 Real)
(declare-const payments_of_dividends_fy2026 Real)
(declare-const payments_related_to_tax_withholding_for_share_based_compensation_fy2026 Real)
(declare-const proceeds_from_issuance_of_medium_term_notes_fy2026 Real)
(declare-const proceeds_from_stock_plans_fy2026 Real)
(declare-const repayments_of_long_term_lines_of_credit_fy2026 Real)

(assert (! (= finance_lease_principal_payments_fy2026 584) :named evidence_finance_lease_principal_payments_fy2026))
(assert (! (= payments_for_repurchase_of_common_stock_fy2026 12596) :named evidence_payments_for_repurchase_of_common_stock_fy2026))
(assert (! (= payments_of_dividends_fy2026 1587) :named evidence_payments_of_dividends_fy2026))
(assert (! (= payments_related_to_tax_withholding_for_share_based_compensation_fy2026 351) :named evidence_payments_related_to_tax_withholding_for_share_based_compensation_fy2026))
(assert (! (= proceeds_from_issuance_of_medium_term_notes_fy2026 6000) :named evidence_proceeds_from_issuance_of_medium_term_notes_fy2026))
(assert (! (= proceeds_from_stock_plans_fy2026 1039) :named evidence_proceeds_from_stock_plans_fy2026))
(assert (! (= repayments_of_long_term_lines_of_credit_fy2026 0) :named evidence_repayments_of_long_term_lines_of_credit_fy2026))

(assert (! (= computed_net_cash_provided_by_used_in_financing_activities_fy2026 (+ proceeds_from_issuance_of_medium_term_notes_fy2026 (* (- 1) payments_for_repurchase_of_common_stock_fy2026) (* (- 1) payments_related_to_tax_withholding_for_share_based_compensation_fy2026) proceeds_from_stock_plans_fy2026 (* (- 1) finance_lease_principal_payments_fy2026) (* (- 1) repayments_of_long_term_lines_of_credit_fy2026) (* (- 1) payments_of_dividends_fy2026))) :named formula_net_cash_provided_by_used_in_financing_activities_fy2026))

(assert (! (<= (- computed_net_cash_provided_by_used_in_financing_activities_fy2026 -8079) 8.0790000000000006) :named claim_upper))
(assert (! (<= (- -8079 computed_net_cash_provided_by_used_in_financing_activities_fy2026) 8.0790000000000006) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)