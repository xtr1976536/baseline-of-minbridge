(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_net_cash_provided_by_used_in_financing_activities_fy2026 Real)
(declare-const payments_for_repurchase_of_common_stock_fy2026 Real)
(declare-const payments_of_dividends_common_stock_fy2026 Real)
(declare-const proceeds_from_issuance_of_common_stock_fy2026 Real)
(declare-const proceeds_from_issuance_of_long_term_debt_and_capital_securities_net_fy2026 Real)
(declare-const proceeds_from_payments_for_other_financing_activities_fy2026 Real)
(declare-const proceeds_from_repayments_of_commercial_paper_fy2026 Real)
(declare-const repayments_of_long_term_debt_and_capital_securities_fy2026 Real)

(assert (! (= payments_for_repurchase_of_common_stock_fy2026 0) :named evidence_payments_for_repurchase_of_common_stock_fy2026))
(assert (! (= payments_of_dividends_common_stock_fy2026 9152) :named evidence_payments_of_dividends_common_stock_fy2026))
(assert (! (= proceeds_from_issuance_of_common_stock_fy2026 314) :named evidence_proceeds_from_issuance_of_common_stock_fy2026))
(assert (! (= proceeds_from_issuance_of_long_term_debt_and_capital_securities_net_fy2026 2161) :named evidence_proceeds_from_issuance_of_long_term_debt_and_capital_securities_net_fy2026))
(assert (! (= proceeds_from_payments_for_other_financing_activities_fy2026 -145) :named evidence_proceeds_from_payments_for_other_financing_activities_fy2026))
(assert (! (= proceeds_from_repayments_of_commercial_paper_fy2026 4148) :named evidence_proceeds_from_repayments_of_commercial_paper_fy2026))
(assert (! (= repayments_of_long_term_debt_and_capital_securities_fy2026 5040) :named evidence_repayments_of_long_term_debt_and_capital_securities_fy2026))

(assert (! (= computed_net_cash_provided_by_used_in_financing_activities_fy2026 (+ proceeds_from_repayments_of_commercial_paper_fy2026 proceeds_from_issuance_of_long_term_debt_and_capital_securities_net_fy2026 (* (- 1) repayments_of_long_term_debt_and_capital_securities_fy2026) (* (- 1) payments_for_repurchase_of_common_stock_fy2026) proceeds_from_issuance_of_common_stock_fy2026 (* (- 1) payments_of_dividends_common_stock_fy2026) proceeds_from_payments_for_other_financing_activities_fy2026)) :named formula_net_cash_provided_by_used_in_financing_activities_fy2026))

(assert (! (<= (- computed_net_cash_provided_by_used_in_financing_activities_fy2026 -7714) 7.7140000000000004) :named claim_upper))
(assert (! (<= (- -7714 computed_net_cash_provided_by_used_in_financing_activities_fy2026) 7.7140000000000004) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)