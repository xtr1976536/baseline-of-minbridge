(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_income_loss_fy2025 Real)
(declare-const gross_profit_fy2025 Real)
(declare-const other_selling_general_and_administrative_expense_fy2025 Real)
(declare-const selling_general_and_administrative_expense_fy2025 Real)

(assert (! (= gross_profit_fy2025 29544) :named evidence_gross_profit_fy2025))
(assert (! (= other_selling_general_and_administrative_expense_fy2025 1261) :named evidence_other_selling_general_and_administrative_expense_fy2025))
(assert (! (= selling_general_and_administrative_expense_fy2025 14521) :named evidence_selling_general_and_administrative_expense_fy2025))

(assert (! (= computed_operating_income_loss_fy2025 (+ gross_profit_fy2025 (* (- 1) selling_general_and_administrative_expense_fy2025) (* (- 1) other_selling_general_and_administrative_expense_fy2025))) :named formula_operating_income_loss_fy2025))

(assert (! (<= (- computed_operating_income_loss_fy2025 15023) 15.023) :named claim_upper))
(assert (! (<= (- 15023 computed_operating_income_loss_fy2025) 15.023) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2025_01_01_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_GrossProfit_duration_2025_01_01_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_01_01_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherSellingGeneralAndAdministrativeExpense_duration_2025_01_01_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_Revenues_duration_2025_01_01_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_01_01_2025_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2025_01_01_2025_12_31_unit_USD_dims_none 18397) :named evidence_xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2025_01_01_2025_12_31_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_01_01_2025_12_31_unit_USD_dims_none 13762) :named evidence_xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_01_01_2025_12_31_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_Revenues_duration_2025_01_01_2025_12_31_unit_USD_dims_none 47941) :named evidence_xbrl_fact_us_gaap_Revenues_duration_2025_01_01_2025_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= gross_profit_fy2025 xbrl_fact_us_gaap_GrossProfit_duration_2025_01_01_2025_12_31_unit_USD_dims_none) :named xbrl_bind_gross_profit_fy2025_edgar_2025_12_31_0001628280_26_010047))
(assert (! (= xbrl_fact_us_gaap_GrossProfit_duration_2025_01_01_2025_12_31_unit_USD_dims_none 29544) :named xbrl_instance_gross_profit_fy2025))
(assert (! (= selling_general_and_administrative_expense_fy2025 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_01_01_2025_12_31_unit_USD_dims_none) :named xbrl_bind_selling_general_and_administrative_expense_fy2025_edgar_2025_12_31_0001628280_26_010047))
(assert (! (= xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_01_01_2025_12_31_unit_USD_dims_none 14521) :named xbrl_instance_selling_general_and_administrative_expense_fy2025))
(assert (! (= other_selling_general_and_administrative_expense_fy2025 xbrl_fact_us_gaap_OtherSellingGeneralAndAdministrativeExpense_duration_2025_01_01_2025_12_31_unit_USD_dims_none) :named xbrl_bind_other_selling_general_and_administrative_expense_fy2025_edgar_2025_12_31_0001628280_26_010047))
(assert (! (= xbrl_fact_us_gaap_OtherSellingGeneralAndAdministrativeExpense_duration_2025_01_01_2025_12_31_unit_USD_dims_none 1261) :named xbrl_instance_other_selling_general_and_administrative_expense_fy2025))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_01_01_2025_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_GrossProfit_duration_2025_01_01_2025_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_01_01_2025_12_31_unit_USD_dims_none) (* -1 xbrl_fact_us_gaap_OtherSellingGeneralAndAdministrativeExpense_duration_2025_01_01_2025_12_31_unit_USD_dims_none))) 2) :named xbrl_calc_3_611970461_OperatingIncomeLoss_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_01_01_2025_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_GrossProfit_duration_2025_01_01_2025_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_01_01_2025_12_31_unit_USD_dims_none) (* -1 xbrl_fact_us_gaap_OtherSellingGeneralAndAdministrativeExpense_duration_2025_01_01_2025_12_31_unit_USD_dims_none))) (- 2)) :named xbrl_calc_3_611970461_OperatingIncomeLoss_c_1_lower))
(assert (! (<= (- xbrl_fact_us_gaap_GrossProfit_duration_2025_01_01_2025_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2025_01_01_2025_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2025_01_01_2025_12_31_unit_USD_dims_none))) 1.5) :named xbrl_calc_5_611970461_GrossProfit_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_GrossProfit_duration_2025_01_01_2025_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2025_01_01_2025_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2025_01_01_2025_12_31_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_5_611970461_GrossProfit_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)