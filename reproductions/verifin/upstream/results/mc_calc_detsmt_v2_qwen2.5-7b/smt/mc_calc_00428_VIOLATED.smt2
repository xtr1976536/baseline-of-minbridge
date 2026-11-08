(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_gross_profit_fy2023 Real)
(declare-const cost_of_goods_and_services_sold_fy2023 Real)
(declare-const revenue_from_contract_with_customer_excluding_assessed_tax_fy2023 Real)

(assert (! (= cost_of_goods_and_services_sold_fy2023 26553) :named evidence_cost_of_goods_and_services_sold_fy2023))
(assert (! (= revenue_from_contract_with_customer_excluding_assessed_tax_fy2023 85159) :named evidence_revenue_from_contract_with_customer_excluding_assessed_tax_fy2023))

(assert (! (= computed_gross_profit_fy2023 (+ revenue_from_contract_with_customer_excluding_assessed_tax_fy2023 (* (- 1) cost_of_goods_and_services_sold_fy2023))) :named formula_gross_profit_fy2023))

(assert (! (<= (- computed_gross_profit_fy2023 58701) 58.701000000000001) :named claim_upper))
(assert (! (<= (- 58701 computed_gross_profit_fy2023) 58.701000000000001) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2023_01_02_2023_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_GrossProfit_duration_2023_01_02_2023_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2023_01_02_2023_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_GrossProfit_duration_2023_01_02_2023_12_31_unit_USD_dims_none 58606) :named evidence_xbrl_fact_us_gaap_GrossProfit_duration_2023_01_02_2023_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= revenue_from_contract_with_customer_excluding_assessed_tax_fy2023 xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2023_01_02_2023_12_31_unit_USD_dims_none) :named xbrl_bind_revenue_from_contract_with_customer_excluding_assessed_tax_fy2023_edgar_2023_12_31_0000200406_24_000013))
(assert (! (= xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2023_01_02_2023_12_31_unit_USD_dims_none 85159) :named xbrl_instance_revenue_from_contract_with_customer_excluding_assessed_tax_fy2023))
(assert (! (= cost_of_goods_and_services_sold_fy2023 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2023_01_02_2023_12_31_unit_USD_dims_none) :named xbrl_bind_cost_of_goods_and_services_sold_fy2023_edgar_2023_12_31_0000200406_24_000013))
(assert (! (= xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2023_01_02_2023_12_31_unit_USD_dims_none 26553) :named xbrl_instance_cost_of_goods_and_services_sold_fy2023))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_GrossProfit_duration_2023_01_02_2023_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2023_01_02_2023_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2023_01_02_2023_12_31_unit_USD_dims_none))) 1.5) :named xbrl_calc_11_77374093_GrossProfit_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_GrossProfit_duration_2023_01_02_2023_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2023_01_02_2023_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2023_01_02_2023_12_31_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_11_77374093_GrossProfit_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)