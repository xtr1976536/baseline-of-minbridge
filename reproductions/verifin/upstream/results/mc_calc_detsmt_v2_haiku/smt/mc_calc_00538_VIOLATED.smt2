(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_income_loss_fy2023 Real)
(declare-const cost_of_goods_and_services_sold_fy2023 Real)
(declare-const revenues_fy2023 Real)
(declare-const selling_general_and_administrative_expense_fy2023 Real)

(assert (! (= cost_of_goods_and_services_sold_fy2023 42760) :named evidence_cost_of_goods_and_services_sold_fy2023))
(assert (! (= revenues_fy2023 82006) :named evidence_revenues_fy2023))
(assert (! (= selling_general_and_administrative_expense_fy2023 21112) :named evidence_selling_general_and_administrative_expense_fy2023))

(assert (! (= computed_operating_income_loss_fy2023 (+ revenues_fy2023 (* (- 1) cost_of_goods_and_services_sold_fy2023) (* (- 1) selling_general_and_administrative_expense_fy2023))) :named formula_operating_income_loss_fy2023))

(assert (! (<= (- computed_operating_income_loss_fy2023 17134) 17.134) :named claim_upper))
(assert (! (<= (- 17134 computed_operating_income_loss_fy2023) 17.134) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2022_07_01_2023_06_30_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2022_07_01_2023_06_30_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_Revenues_duration_2022_07_01_2023_06_30_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2022_07_01_2023_06_30_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2022_07_01_2023_06_30_unit_USD_dims_none 18134) :named evidence_xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2022_07_01_2023_06_30_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= revenues_fy2023 xbrl_fact_us_gaap_Revenues_duration_2022_07_01_2023_06_30_unit_USD_dims_none) :named xbrl_bind_revenues_fy2023_edgar_2023_06_30_0000080424_23_000073))
(assert (! (= xbrl_fact_us_gaap_Revenues_duration_2022_07_01_2023_06_30_unit_USD_dims_none 82006) :named xbrl_instance_revenues_fy2023))
(assert (! (= cost_of_goods_and_services_sold_fy2023 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2022_07_01_2023_06_30_unit_USD_dims_none) :named xbrl_bind_cost_of_goods_and_services_sold_fy2023_edgar_2023_06_30_0000080424_23_000073))
(assert (! (= xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2022_07_01_2023_06_30_unit_USD_dims_none 42760) :named xbrl_instance_cost_of_goods_and_services_sold_fy2023))
(assert (! (= selling_general_and_administrative_expense_fy2023 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2022_07_01_2023_06_30_unit_USD_dims_none) :named xbrl_bind_selling_general_and_administrative_expense_fy2023_edgar_2023_06_30_0000080424_23_000073))
(assert (! (= xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2022_07_01_2023_06_30_unit_USD_dims_none 21112) :named xbrl_instance_selling_general_and_administrative_expense_fy2023))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2022_07_01_2023_06_30_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2022_07_01_2023_06_30_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2022_07_01_2023_06_30_unit_USD_dims_none) (* -1 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2022_07_01_2023_06_30_unit_USD_dims_none))) 2) :named xbrl_calc_2_55266277_OperatingIncomeLoss_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2022_07_01_2023_06_30_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2022_07_01_2023_06_30_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2022_07_01_2023_06_30_unit_USD_dims_none) (* -1 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2022_07_01_2023_06_30_unit_USD_dims_none))) (- 2)) :named xbrl_calc_2_55266277_OperatingIncomeLoss_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)