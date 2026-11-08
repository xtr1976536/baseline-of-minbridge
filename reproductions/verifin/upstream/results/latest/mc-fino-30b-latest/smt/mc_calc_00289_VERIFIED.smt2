(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_income_loss_fy2024 Real)
(declare-const gross_profit_fy2024 Real)
(declare-const other_selling_general_and_administrative_expense_fy2024 Real)
(declare-const selling_general_and_administrative_expense_fy2024 Real)

(assert (! (= gross_profit_fy2024 28737) :named evidence_gross_profit_fy2024))
(assert (! (= other_selling_general_and_administrative_expense_fy2024 4163) :named evidence_other_selling_general_and_administrative_expense_fy2024))
(assert (! (= selling_general_and_administrative_expense_fy2024 14582) :named evidence_selling_general_and_administrative_expense_fy2024))

(assert (! (= computed_operating_income_loss_fy2024 (+ gross_profit_fy2024 (* (- 1) selling_general_and_administrative_expense_fy2024) (* (- 1) other_selling_general_and_administrative_expense_fy2024))) :named formula_operating_income_loss_fy2024))

(assert (! (<= (- computed_operating_income_loss_fy2024 10000) 10) :named claim_upper))
(assert (! (<= (- 10000 computed_operating_income_loss_fy2024) 10) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_01_01_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_GrossProfit_duration_2024_01_01_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_01_01_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherSellingGeneralAndAdministrativeExpense_duration_2024_01_01_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_Revenues_duration_2024_01_01_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2024_01_01_2024_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_01_01_2024_12_31_unit_USD_dims_none 18324) :named evidence_xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_01_01_2024_12_31_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_01_01_2024_12_31_unit_USD_dims_none 9992) :named evidence_xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_01_01_2024_12_31_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_Revenues_duration_2024_01_01_2024_12_31_unit_USD_dims_none 47061) :named evidence_xbrl_fact_us_gaap_Revenues_duration_2024_01_01_2024_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= gross_profit_fy2024 xbrl_fact_us_gaap_GrossProfit_duration_2024_01_01_2024_12_31_unit_USD_dims_none) :named xbrl_bind_gross_profit_fy2024_edgar_2024_12_31_0000021344_25_000011))
(assert (! (= xbrl_fact_us_gaap_GrossProfit_duration_2024_01_01_2024_12_31_unit_USD_dims_none 28737) :named xbrl_instance_gross_profit_fy2024))
(assert (! (= selling_general_and_administrative_expense_fy2024 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2024_01_01_2024_12_31_unit_USD_dims_none) :named xbrl_bind_selling_general_and_administrative_expense_fy2024_edgar_2024_12_31_0000021344_25_000011))
(assert (! (= xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2024_01_01_2024_12_31_unit_USD_dims_none 14582) :named xbrl_instance_selling_general_and_administrative_expense_fy2024))
(assert (! (= other_selling_general_and_administrative_expense_fy2024 xbrl_fact_us_gaap_OtherSellingGeneralAndAdministrativeExpense_duration_2024_01_01_2024_12_31_unit_USD_dims_none) :named xbrl_bind_other_selling_general_and_administrative_expense_fy2024_edgar_2024_12_31_0000021344_25_000011))
(assert (! (= xbrl_fact_us_gaap_OtherSellingGeneralAndAdministrativeExpense_duration_2024_01_01_2024_12_31_unit_USD_dims_none 4163) :named xbrl_instance_other_selling_general_and_administrative_expense_fy2024))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_01_01_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_GrossProfit_duration_2024_01_01_2024_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2024_01_01_2024_12_31_unit_USD_dims_none) (* -1 xbrl_fact_us_gaap_OtherSellingGeneralAndAdministrativeExpense_duration_2024_01_01_2024_12_31_unit_USD_dims_none))) 2) :named xbrl_calc_1_611970461_OperatingIncomeLoss_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_01_01_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_GrossProfit_duration_2024_01_01_2024_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2024_01_01_2024_12_31_unit_USD_dims_none) (* -1 xbrl_fact_us_gaap_OtherSellingGeneralAndAdministrativeExpense_duration_2024_01_01_2024_12_31_unit_USD_dims_none))) (- 2)) :named xbrl_calc_1_611970461_OperatingIncomeLoss_c_1_lower))
(assert (! (<= (- xbrl_fact_us_gaap_GrossProfit_duration_2024_01_01_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2024_01_01_2024_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_01_01_2024_12_31_unit_USD_dims_none))) 1.5) :named xbrl_calc_5_611970461_GrossProfit_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_GrossProfit_duration_2024_01_01_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2024_01_01_2024_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_01_01_2024_12_31_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_5_611970461_GrossProfit_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)