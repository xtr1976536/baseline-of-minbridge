(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_gross_profit_fy2024 Real)
(declare-const cost_of_goods_and_services_sold_fy2024 Real)
(declare-const revenue_from_contract_with_customer_excluding_assessed_tax_fy2024 Real)

(assert (! (= cost_of_goods_and_services_sold_fy2024 35756) :named evidence_cost_of_goods_and_services_sold_fy2024))
(assert (! (= revenue_from_contract_with_customer_excluding_assessed_tax_fy2024 53101) :named evidence_revenue_from_contract_with_customer_excluding_assessed_tax_fy2024))

(assert (! (= computed_gross_profit_fy2024 (+ revenue_from_contract_with_customer_excluding_assessed_tax_fy2024 (* (- 1) cost_of_goods_and_services_sold_fy2024))) :named formula_gross_profit_fy2024))

(assert (! (<= (- computed_gross_profit_fy2024 17345) 17.344999999999999) :named claim_upper))
(assert (! (<= (- 17345 computed_gross_profit_fy2024) 17.344999999999999) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2023_12_31_2024_12_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_GrossProfit_duration_2023_12_31_2024_12_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2023_12_31_2024_12_28_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_GrossProfit_duration_2023_12_31_2024_12_28_unit_USD_dims_none 17345) :named evidence_xbrl_fact_us_gaap_GrossProfit_duration_2023_12_31_2024_12_28_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= revenue_from_contract_with_customer_excluding_assessed_tax_fy2024 xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2023_12_31_2024_12_28_unit_USD_dims_none) :named xbrl_bind_revenue_from_contract_with_customer_excluding_assessed_tax_fy2024_edgar_2024_12_28_0000050863_25_000009))
(assert (! (= xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2023_12_31_2024_12_28_unit_USD_dims_none 53101) :named xbrl_instance_revenue_from_contract_with_customer_excluding_assessed_tax_fy2024))
(assert (! (= cost_of_goods_and_services_sold_fy2024 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2023_12_31_2024_12_28_unit_USD_dims_none) :named xbrl_bind_cost_of_goods_and_services_sold_fy2024_edgar_2024_12_28_0000050863_25_000009))
(assert (! (= xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2023_12_31_2024_12_28_unit_USD_dims_none 35756) :named xbrl_instance_cost_of_goods_and_services_sold_fy2024))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_GrossProfit_duration_2023_12_31_2024_12_28_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2023_12_31_2024_12_28_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2023_12_31_2024_12_28_unit_USD_dims_none))) 1.5) :named xbrl_calc_2_433660659_GrossProfit_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_GrossProfit_duration_2023_12_31_2024_12_28_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2023_12_31_2024_12_28_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2023_12_31_2024_12_28_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_2_433660659_GrossProfit_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)