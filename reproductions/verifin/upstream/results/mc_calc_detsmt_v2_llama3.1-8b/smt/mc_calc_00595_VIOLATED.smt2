(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_net_cash_provided_by_used_in_financing_activities_fy2025 Real)
(declare-const finance_lease_principal_payments_fy2025 Real)
(declare-const payments_for_repurchase_of_common_stock_fy2025 Real)
(declare-const payments_of_dividends_fy2025 Real)
(declare-const proceeds_from_stock_plans_fy2025 Real)
(declare-const repayments_of_long_term_lines_of_credit_fy2025 Real)

(assert (! (= finance_lease_principal_payments_fy2025 584) :named evidence_finance_lease_principal_payments_fy2025))
(assert (! (= payments_for_repurchase_of_common_stock_fy2025 12596) :named evidence_payments_for_repurchase_of_common_stock_fy2025))
(assert (! (= payments_of_dividends_fy2025 1587) :named evidence_payments_of_dividends_fy2025))
(assert (! (= proceeds_from_stock_plans_fy2025 1039) :named evidence_proceeds_from_stock_plans_fy2025))
(assert (! (= repayments_of_long_term_lines_of_credit_fy2025 0) :named evidence_repayments_of_long_term_lines_of_credit_fy2025))

(assert (! (= computed_net_cash_provided_by_used_in_financing_activities_fy2025 (+ (* (- 1) repayments_of_long_term_lines_of_credit_fy2025) (* (- 1) finance_lease_principal_payments_fy2025) (* (- 1) payments_for_repurchase_of_common_stock_fy2025) proceeds_from_stock_plans_fy2025 (* (- 1) payments_of_dividends_fy2025))) :named formula_net_cash_provided_by_used_in_financing_activities_fy2025))

(assert (! (<= (- computed_net_cash_provided_by_used_in_financing_activities_fy2025 -7477) 7.4770000000000003) :named claim_upper))
(assert (! (<= (- -7477 computed_net_cash_provided_by_used_in_financing_activities_fy2025) 7.4770000000000003) :named claim_lower))

; EDGAR-companyfacts fact bindings (no calculation-linkbase constraints).
(declare-const xbrl_fact_us_gaap_FinanceLeasePrincipalPayments_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_PaymentsForRepurchaseOfCommonStock_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_PaymentsOfDividends_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_ProceedsFromStockPlans_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RepaymentsOfLongTermLinesOfCredit_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= repayments_of_long_term_lines_of_credit_fy2025 xbrl_fact_us_gaap_RepaymentsOfLongTermLinesOfCredit_duration_2025_02_01_2026_01_31_unit_USD_dims_none) :named xbrl_bind_repayments_of_long_term_lines_of_credit_fy2025_edgar_2026_01_31_0001108524_26_000060))
(assert (! (= xbrl_fact_us_gaap_RepaymentsOfLongTermLinesOfCredit_duration_2025_02_01_2026_01_31_unit_USD_dims_none 0) :named xbrl_instance_repayments_of_long_term_lines_of_credit_fy2025))
(assert (! (= finance_lease_principal_payments_fy2025 xbrl_fact_us_gaap_FinanceLeasePrincipalPayments_duration_2025_02_01_2026_01_31_unit_USD_dims_none) :named xbrl_bind_finance_lease_principal_payments_fy2025_edgar_2026_01_31_0001108524_26_000060))
(assert (! (= xbrl_fact_us_gaap_FinanceLeasePrincipalPayments_duration_2025_02_01_2026_01_31_unit_USD_dims_none 584) :named xbrl_instance_finance_lease_principal_payments_fy2025))
(assert (! (= payments_for_repurchase_of_common_stock_fy2025 xbrl_fact_us_gaap_PaymentsForRepurchaseOfCommonStock_duration_2025_02_01_2026_01_31_unit_USD_dims_none) :named xbrl_bind_payments_for_repurchase_of_common_stock_fy2025_edgar_2026_01_31_0001108524_26_000060))
(assert (! (= xbrl_fact_us_gaap_PaymentsForRepurchaseOfCommonStock_duration_2025_02_01_2026_01_31_unit_USD_dims_none 12596) :named xbrl_instance_payments_for_repurchase_of_common_stock_fy2025))
(assert (! (= proceeds_from_stock_plans_fy2025 xbrl_fact_us_gaap_ProceedsFromStockPlans_duration_2025_02_01_2026_01_31_unit_USD_dims_none) :named xbrl_bind_proceeds_from_stock_plans_fy2025_edgar_2026_01_31_0001108524_26_000060))
(assert (! (= xbrl_fact_us_gaap_ProceedsFromStockPlans_duration_2025_02_01_2026_01_31_unit_USD_dims_none 1039) :named xbrl_instance_proceeds_from_stock_plans_fy2025))
(assert (! (= payments_of_dividends_fy2025 xbrl_fact_us_gaap_PaymentsOfDividends_duration_2025_02_01_2026_01_31_unit_USD_dims_none) :named xbrl_bind_payments_of_dividends_fy2025_edgar_2026_01_31_0001108524_26_000060))
(assert (! (= xbrl_fact_us_gaap_PaymentsOfDividends_duration_2025_02_01_2026_01_31_unit_USD_dims_none 1587) :named xbrl_instance_payments_of_dividends_fy2025))

(check-sat)
(get-unsat-core)
(get-model)