(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_income_loss_fy2025 Real)
(declare-const cost_of_revenue_fy2025 Real)
(declare-const revenues_fy2025 Real)
(declare-const selling_general_and_administrative_expense_fy2025 Real)

(assert (! (= cost_of_revenue_fy2025 511753) :named evidence_cost_of_revenue_fy2025))
(assert (! (= revenues_fy2025 680985) :named evidence_revenues_fy2025))
(assert (! (= selling_general_and_administrative_expense_fy2025 139884) :named evidence_selling_general_and_administrative_expense_fy2025))

(assert (! (= computed_operating_income_loss_fy2025 (+ revenues_fy2025 (* (- 1) cost_of_revenue_fy2025) (* (- 1) selling_general_and_administrative_expense_fy2025))) :named formula_operating_income_loss_fy2025))

(assert (! (<= (- computed_operating_income_loss_fy2025 29348) 29.347999999999999) :named claim_upper))
(assert (! (<= (- 29348 computed_operating_income_loss_fy2025) 29.347999999999999) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostOfRevenue_duration_2024_02_01_2025_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_02_01_2025_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherIncome_duration_2024_02_01_2025_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2024_02_01_2025_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_Revenues_duration_2024_02_01_2025_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2024_02_01_2025_01_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_02_01_2025_01_31_unit_USD_dims_none 29348) :named evidence_xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_02_01_2025_01_31_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_OtherIncome_duration_2024_02_01_2025_01_31_unit_USD_dims_none 6447) :named evidence_xbrl_fact_us_gaap_OtherIncome_duration_2024_02_01_2025_01_31_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2024_02_01_2025_01_31_unit_USD_dims_none 674538) :named evidence_xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2024_02_01_2025_01_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= revenues_fy2025 xbrl_fact_us_gaap_Revenues_duration_2024_02_01_2025_01_31_unit_USD_dims_none) :named xbrl_bind_revenues_fy2025_edgar_2025_01_31_0000104169_25_000021))
(assert (! (= xbrl_fact_us_gaap_Revenues_duration_2024_02_01_2025_01_31_unit_USD_dims_none 680985) :named xbrl_instance_revenues_fy2025))
(assert (! (= cost_of_revenue_fy2025 xbrl_fact_us_gaap_CostOfRevenue_duration_2024_02_01_2025_01_31_unit_USD_dims_none) :named xbrl_bind_cost_of_revenue_fy2025_edgar_2025_01_31_0000104169_25_000021))
(assert (! (= xbrl_fact_us_gaap_CostOfRevenue_duration_2024_02_01_2025_01_31_unit_USD_dims_none 511753) :named xbrl_instance_cost_of_revenue_fy2025))
(assert (! (= selling_general_and_administrative_expense_fy2025 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2024_02_01_2025_01_31_unit_USD_dims_none) :named xbrl_bind_selling_general_and_administrative_expense_fy2025_edgar_2025_01_31_0000104169_25_000021))
(assert (! (= xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2024_02_01_2025_01_31_unit_USD_dims_none 139884) :named xbrl_instance_selling_general_and_administrative_expense_fy2025))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_02_01_2025_01_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2024_02_01_2025_01_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfRevenue_duration_2024_02_01_2025_01_31_unit_USD_dims_none) (* -1 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2024_02_01_2025_01_31_unit_USD_dims_none))) 2) :named xbrl_calc_2_638033365_OperatingIncomeLoss_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_02_01_2025_01_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2024_02_01_2025_01_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfRevenue_duration_2024_02_01_2025_01_31_unit_USD_dims_none) (* -1 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2024_02_01_2025_01_31_unit_USD_dims_none))) (- 2)) :named xbrl_calc_2_638033365_OperatingIncomeLoss_c_1_lower))
(assert (! (<= (- xbrl_fact_us_gaap_Revenues_duration_2024_02_01_2025_01_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2024_02_01_2025_01_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherIncome_duration_2024_02_01_2025_01_31_unit_USD_dims_none)) 1.5) :named xbrl_calc_4_638033365_Revenues_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_Revenues_duration_2024_02_01_2025_01_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2024_02_01_2025_01_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherIncome_duration_2024_02_01_2025_01_31_unit_USD_dims_none)) (- 1.5)) :named xbrl_calc_4_638033365_Revenues_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)