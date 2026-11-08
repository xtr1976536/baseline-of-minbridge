(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_gross_profit_fy2023 Real)
(declare-const cost_of_goods_and_services_sold_fy2023 Real)
(declare-const revenue_from_contract_with_customer_excluding_assessed_tax_fy2023 Real)

(assert (! (= cost_of_goods_and_services_sold_fy2023 65863) :named evidence_cost_of_goods_and_services_sold_fy2023))
(assert (! (= revenue_from_contract_with_customer_excluding_assessed_tax_fy2023 211915) :named evidence_revenue_from_contract_with_customer_excluding_assessed_tax_fy2023))

(assert (! (= computed_gross_profit_fy2023 (+ revenue_from_contract_with_customer_excluding_assessed_tax_fy2023 (* (- 1) cost_of_goods_and_services_sold_fy2023))) :named formula_gross_profit_fy2023))

(assert (! (<= (- computed_gross_profit_fy2023 146052) 146.05199999999999) :named claim_upper))
(assert (! (<= (- 146052 computed_gross_profit_fy2023) 146.05199999999999) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2022_07_01_2023_06_30_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_GrossProfit_duration_2022_07_01_2023_06_30_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2022_07_01_2023_06_30_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_GrossProfit_duration_2022_07_01_2023_06_30_unit_USD_dims_none 146052) :named evidence_xbrl_fact_us_gaap_GrossProfit_duration_2022_07_01_2023_06_30_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= revenue_from_contract_with_customer_excluding_assessed_tax_fy2023 xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2022_07_01_2023_06_30_unit_USD_dims_none) :named xbrl_bind_revenue_from_contract_with_customer_excluding_assessed_tax_fy2023_edgar_2023_06_30_0000950170_23_035122))
(assert (! (= xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2022_07_01_2023_06_30_unit_USD_dims_none 211915) :named xbrl_instance_revenue_from_contract_with_customer_excluding_assessed_tax_fy2023))
(assert (! (= cost_of_goods_and_services_sold_fy2023 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2022_07_01_2023_06_30_unit_USD_dims_none) :named xbrl_bind_cost_of_goods_and_services_sold_fy2023_edgar_2023_06_30_0000950170_23_035122))
(assert (! (= xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2022_07_01_2023_06_30_unit_USD_dims_none 65863) :named xbrl_instance_cost_of_goods_and_services_sold_fy2023))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_GrossProfit_duration_2022_07_01_2023_06_30_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2022_07_01_2023_06_30_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2022_07_01_2023_06_30_unit_USD_dims_none))) 1.5) :named xbrl_calc_2_976854837_GrossProfit_C_da7a1266_ce2b_41b7_83ff_bb6e03dc1fa5_upper))
(assert (! (>= (- xbrl_fact_us_gaap_GrossProfit_duration_2022_07_01_2023_06_30_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2022_07_01_2023_06_30_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2022_07_01_2023_06_30_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_2_976854837_GrossProfit_C_da7a1266_ce2b_41b7_83ff_bb6e03dc1fa5_lower))

(check-sat)
(get-unsat-core)
(get-model)