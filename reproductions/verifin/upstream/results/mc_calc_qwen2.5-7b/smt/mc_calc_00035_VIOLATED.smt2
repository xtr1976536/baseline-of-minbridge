(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_income_loss_fy2026 Real)
(declare-const cost_of_revenue_fy2026 Real)
(declare-const revenues_fy2026 Real)
(declare-const selling_general_and_administrative_expense_fy2026 Real)

(assert (! (= cost_of_revenue_fy2026 535395.0) :named evidence_cost_of_revenue_fy2026))
(assert (! (= revenues_fy2026 713163.0) :named evidence_revenues_fy2026))
(assert (! (= selling_general_and_administrative_expense_fy2026 147943.0) :named evidence_selling_general_and_administrative_expense_fy2026))

(assert (! (= computed_operating_income_loss_fy2026 (+ revenues_fy2026 (- cost_of_revenue_fy2026) (- selling_general_and_administrative_expense_fy2026))) :named formula_operating_income_loss_fy2026))

(assert (! (or (> cost_of_revenue_fy2026 0) (< cost_of_revenue_fy2026 0)) :named denom_nonzero_cost_of_revenue))
(assert (! (or (> revenues_fy2026 0) (< revenues_fy2026 0)) :named denom_nonzero_revenues))
(assert (! (or (> selling_general_and_administrative_expense_fy2026 0) (< selling_general_and_administrative_expense_fy2026 0)) :named denom_nonzero_selling_general_and_administrative_expense))

(assert (! (<= (- computed_operating_income_loss_fy2026 -107.0) 0.01) :named claim_upper))
(assert (! (<= (- -107.0 computed_operating_income_loss_fy2026) 0.01) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostOfRevenue_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherIncome_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_Revenues_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_02_01_2026_01_31_unit_USD_dims_none 29825) :named evidence_xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_02_01_2026_01_31_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_OtherIncome_duration_2025_02_01_2026_01_31_unit_USD_dims_none 6750) :named evidence_xbrl_fact_us_gaap_OtherIncome_duration_2025_02_01_2026_01_31_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_01_2026_01_31_unit_USD_dims_none 706413) :named evidence_xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_01_2026_01_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= revenues_fy2026 xbrl_fact_us_gaap_Revenues_duration_2025_02_01_2026_01_31_unit_USD_dims_none) :named xbrl_bind_revenues_fy2026_edgar_2026_01_31_0000104169_26_000055))
(assert (! (= xbrl_fact_us_gaap_Revenues_duration_2025_02_01_2026_01_31_unit_USD_dims_none 713163) :named xbrl_instance_revenues_fy2026))
(assert (! (= cost_of_revenue_fy2026 xbrl_fact_us_gaap_CostOfRevenue_duration_2025_02_01_2026_01_31_unit_USD_dims_none) :named xbrl_bind_cost_of_revenue_fy2026_edgar_2026_01_31_0000104169_26_000055))
(assert (! (= xbrl_fact_us_gaap_CostOfRevenue_duration_2025_02_01_2026_01_31_unit_USD_dims_none 535395) :named xbrl_instance_cost_of_revenue_fy2026))
(assert (! (= selling_general_and_administrative_expense_fy2026 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none) :named xbrl_bind_selling_general_and_administrative_expense_fy2026_edgar_2026_01_31_0000104169_26_000055))
(assert (! (= xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none 147943) :named xbrl_instance_selling_general_and_administrative_expense_fy2026))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_Revenues_duration_2025_02_01_2026_01_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_01_2026_01_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherIncome_duration_2025_02_01_2026_01_31_unit_USD_dims_none)) 1.5) :named xbrl_calc_0_638033365_Revenues_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_Revenues_duration_2025_02_01_2026_01_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_01_2026_01_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherIncome_duration_2025_02_01_2026_01_31_unit_USD_dims_none)) (- 1.5)) :named xbrl_calc_0_638033365_Revenues_c_1_lower))
(assert (! (<= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_02_01_2026_01_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2025_02_01_2026_01_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfRevenue_duration_2025_02_01_2026_01_31_unit_USD_dims_none) (* -1 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none))) 2) :named xbrl_calc_3_638033365_OperatingIncomeLoss_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_02_01_2026_01_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2025_02_01_2026_01_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfRevenue_duration_2025_02_01_2026_01_31_unit_USD_dims_none) (* -1 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none))) (- 2)) :named xbrl_calc_3_638033365_OperatingIncomeLoss_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)