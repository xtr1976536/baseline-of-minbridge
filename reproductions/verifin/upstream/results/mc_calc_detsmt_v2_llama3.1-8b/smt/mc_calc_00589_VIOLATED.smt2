(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_income_loss_fy2023 Real)
(declare-const gross_profit_fy2023 Real)
(declare-const other_cost_and_expense_operating_fy2023 Real)
(declare-const selling_general_and_administrative_expense_fy2023 Real)

(assert (! (= gross_profit_fy2023 27234) :named evidence_gross_profit_fy2023))
(assert (! (= other_cost_and_expense_operating_fy2023 1951) :named evidence_other_cost_and_expense_operating_fy2023))
(assert (! (= selling_general_and_administrative_expense_fy2023 13972) :named evidence_selling_general_and_administrative_expense_fy2023))

(assert (! (= computed_operating_income_loss_fy2023 (+ gross_profit_fy2023 (* (- 1) selling_general_and_administrative_expense_fy2023) (* (- 1) other_cost_and_expense_operating_fy2023))) :named formula_operating_income_loss_fy2023))

(assert (! (<= (- computed_operating_income_loss_fy2023 12952) 12.952) :named claim_upper))
(assert (! (<= (- 12952 computed_operating_income_loss_fy2023) 12.952) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2023_01_01_2023_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_GrossProfit_duration_2023_01_01_2023_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2023_01_01_2023_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherCostAndExpenseOperating_duration_2023_01_01_2023_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_Revenues_duration_2023_01_01_2023_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2023_01_01_2023_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2023_01_01_2023_12_31_unit_USD_dims_none 18520) :named evidence_xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2023_01_01_2023_12_31_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2023_01_01_2023_12_31_unit_USD_dims_none 11311) :named evidence_xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2023_01_01_2023_12_31_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_Revenues_duration_2023_01_01_2023_12_31_unit_USD_dims_none 45754) :named evidence_xbrl_fact_us_gaap_Revenues_duration_2023_01_01_2023_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= gross_profit_fy2023 xbrl_fact_us_gaap_GrossProfit_duration_2023_01_01_2023_12_31_unit_USD_dims_none) :named xbrl_bind_gross_profit_fy2023_edgar_2023_12_31_0000021344_24_000009))
(assert (! (= xbrl_fact_us_gaap_GrossProfit_duration_2023_01_01_2023_12_31_unit_USD_dims_none 27234) :named xbrl_instance_gross_profit_fy2023))
(assert (! (= selling_general_and_administrative_expense_fy2023 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2023_01_01_2023_12_31_unit_USD_dims_none) :named xbrl_bind_selling_general_and_administrative_expense_fy2023_edgar_2023_12_31_0000021344_24_000009))
(assert (! (= xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2023_01_01_2023_12_31_unit_USD_dims_none 13972) :named xbrl_instance_selling_general_and_administrative_expense_fy2023))
(assert (! (= other_cost_and_expense_operating_fy2023 xbrl_fact_us_gaap_OtherCostAndExpenseOperating_duration_2023_01_01_2023_12_31_unit_USD_dims_none) :named xbrl_bind_other_cost_and_expense_operating_fy2023_edgar_2023_12_31_0000021344_24_000009))
(assert (! (= xbrl_fact_us_gaap_OtherCostAndExpenseOperating_duration_2023_01_01_2023_12_31_unit_USD_dims_none 1951) :named xbrl_instance_other_cost_and_expense_operating_fy2023))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_GrossProfit_duration_2023_01_01_2023_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2023_01_01_2023_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2023_01_01_2023_12_31_unit_USD_dims_none))) 1.5) :named xbrl_calc_0_611970461_GrossProfit_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_GrossProfit_duration_2023_01_01_2023_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2023_01_01_2023_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2023_01_01_2023_12_31_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_0_611970461_GrossProfit_c_1_lower))
(assert (! (<= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2023_01_01_2023_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_GrossProfit_duration_2023_01_01_2023_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2023_01_01_2023_12_31_unit_USD_dims_none) (* -1 xbrl_fact_us_gaap_OtherCostAndExpenseOperating_duration_2023_01_01_2023_12_31_unit_USD_dims_none))) 2) :named xbrl_calc_2_611970461_OperatingIncomeLoss_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2023_01_01_2023_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_GrossProfit_duration_2023_01_01_2023_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2023_01_01_2023_12_31_unit_USD_dims_none) (* -1 xbrl_fact_us_gaap_OtherCostAndExpenseOperating_duration_2023_01_01_2023_12_31_unit_USD_dims_none))) (- 2)) :named xbrl_calc_2_611970461_OperatingIncomeLoss_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)