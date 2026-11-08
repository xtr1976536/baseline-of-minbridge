(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_income_loss_fy2024 Real)
(declare-const cost_of_revenue_fy2024 Real)
(declare-const revenues_fy2024 Real)
(declare-const selling_general_and_administrative_expense_fy2024 Real)

(assert (! (= cost_of_revenue_fy2024 490142.0) :named evidence_cost_of_revenue_fy2024))
(assert (! (= revenues_fy2024 648125.0) :named evidence_revenues_fy2024))
(assert (! (= selling_general_and_administrative_expense_fy2024 130971.0) :named evidence_selling_general_and_administrative_expense_fy2024))

(assert (! (= computed_operating_income_loss_fy2024 (+ revenues_fy2024 (- cost_of_revenue_fy2024) (- selling_general_and_administrative_expense_fy2024))) :named formula_operating_income_loss_fy2024))

(assert (! (or (> cost_of_revenue_fy2024 0) (< cost_of_revenue_fy2024 0)) :named denom_nonzero_cost_of_revenue))
(assert (! (or (> revenues_fy2024 0) (< revenues_fy2024 0)) :named denom_nonzero_revenues))
(assert (! (or (> selling_general_and_administrative_expense_fy2024 0) (< selling_general_and_administrative_expense_fy2024 0)) :named denom_nonzero_selling_general_and_administrative_expense))

(assert (! (<= (- computed_operating_income_loss_fy2024 30427.0) 304.27) :named claim_upper))
(assert (! (<= (- 30427.0 computed_operating_income_loss_fy2024) 304.27) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostOfRevenue_duration_2023_02_01_2024_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2023_02_01_2024_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherIncome_duration_2023_02_01_2024_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2023_02_01_2024_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_Revenues_duration_2023_02_01_2024_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2023_02_01_2024_01_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2023_02_01_2024_01_31_unit_USD_dims_none 27012) :named evidence_xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2023_02_01_2024_01_31_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_OtherIncome_duration_2023_02_01_2024_01_31_unit_USD_dims_none 5488) :named evidence_xbrl_fact_us_gaap_OtherIncome_duration_2023_02_01_2024_01_31_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2023_02_01_2024_01_31_unit_USD_dims_none 642637) :named evidence_xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2023_02_01_2024_01_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= cost_of_revenue_fy2024 xbrl_fact_us_gaap_CostOfRevenue_duration_2023_02_01_2024_01_31_unit_USD_dims_none) :named xbrl_bind_cost_of_revenue_fy2024_edgar_2024_01_31_0000104169_24_000056))
(assert (! (= xbrl_fact_us_gaap_CostOfRevenue_duration_2023_02_01_2024_01_31_unit_USD_dims_none 490142) :named xbrl_instance_cost_of_revenue_fy2024))
(assert (! (= revenues_fy2024 xbrl_fact_us_gaap_Revenues_duration_2023_02_01_2024_01_31_unit_USD_dims_none) :named xbrl_bind_revenues_fy2024_edgar_2024_01_31_0000104169_24_000056))
(assert (! (= xbrl_fact_us_gaap_Revenues_duration_2023_02_01_2024_01_31_unit_USD_dims_none 648125) :named xbrl_instance_revenues_fy2024))
(assert (! (= selling_general_and_administrative_expense_fy2024 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2023_02_01_2024_01_31_unit_USD_dims_none) :named xbrl_bind_selling_general_and_administrative_expense_fy2024_edgar_2024_01_31_0000104169_24_000056))
(assert (! (= xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2023_02_01_2024_01_31_unit_USD_dims_none 130971) :named xbrl_instance_selling_general_and_administrative_expense_fy2024))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2023_02_01_2024_01_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2023_02_01_2024_01_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfRevenue_duration_2023_02_01_2024_01_31_unit_USD_dims_none) (* -1 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2023_02_01_2024_01_31_unit_USD_dims_none))) 2) :named xbrl_calc_0_638033365_OperatingIncomeLoss_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2023_02_01_2024_01_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2023_02_01_2024_01_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfRevenue_duration_2023_02_01_2024_01_31_unit_USD_dims_none) (* -1 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2023_02_01_2024_01_31_unit_USD_dims_none))) (- 2)) :named xbrl_calc_0_638033365_OperatingIncomeLoss_c_1_lower))
(assert (! (<= (- xbrl_fact_us_gaap_Revenues_duration_2023_02_01_2024_01_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2023_02_01_2024_01_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherIncome_duration_2023_02_01_2024_01_31_unit_USD_dims_none)) 1.5) :named xbrl_calc_3_638033365_Revenues_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_Revenues_duration_2023_02_01_2024_01_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2023_02_01_2024_01_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherIncome_duration_2023_02_01_2024_01_31_unit_USD_dims_none)) (- 1.5)) :named xbrl_calc_3_638033365_Revenues_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)