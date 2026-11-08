(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_gross_profit_fy2022 Real)
(declare-const cost_of_goods_and_services_sold_fy2022 Real)
(declare-const revenue_from_contract_with_customer_excluding_assessed_tax_fy2022 Real)

(assert (! (= cost_of_goods_and_services_sold_fy2022 62650) :named evidence_cost_of_goods_and_services_sold_fy2022))
(assert (! (= revenue_from_contract_with_customer_excluding_assessed_tax_fy2022 198270) :named evidence_revenue_from_contract_with_customer_excluding_assessed_tax_fy2022))

(assert (! (= computed_gross_profit_fy2022 (+ revenue_from_contract_with_customer_excluding_assessed_tax_fy2022 (* (- 1) cost_of_goods_and_services_sold_fy2022))) :named formula_gross_profit_fy2022))

(assert (! (<= (- computed_gross_profit_fy2022 135620) 135.62) :named claim_upper))
(assert (! (<= (- 135620 computed_gross_profit_fy2022) 135.62) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2021_07_01_2022_06_30_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_GrossProfit_duration_2021_07_01_2022_06_30_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2021_07_01_2022_06_30_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_GrossProfit_duration_2021_07_01_2022_06_30_unit_USD_dims_none 135620) :named evidence_xbrl_fact_us_gaap_GrossProfit_duration_2021_07_01_2022_06_30_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= revenue_from_contract_with_customer_excluding_assessed_tax_fy2022 xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2021_07_01_2022_06_30_unit_USD_dims_none) :named xbrl_bind_revenue_from_contract_with_customer_excluding_assessed_tax_fy2022_edgar_2022_06_30_0001564590_22_026876))
(assert (! (= xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2021_07_01_2022_06_30_unit_USD_dims_none 198270) :named xbrl_instance_revenue_from_contract_with_customer_excluding_assessed_tax_fy2022))
(assert (! (= cost_of_goods_and_services_sold_fy2022 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2021_07_01_2022_06_30_unit_USD_dims_none) :named xbrl_bind_cost_of_goods_and_services_sold_fy2022_edgar_2022_06_30_0001564590_22_026876))
(assert (! (= xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2021_07_01_2022_06_30_unit_USD_dims_none 62650) :named xbrl_instance_cost_of_goods_and_services_sold_fy2022))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_GrossProfit_duration_2021_07_01_2022_06_30_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2021_07_01_2022_06_30_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2021_07_01_2022_06_30_unit_USD_dims_none))) 1.5) :named xbrl_calc_3_15971244_GrossProfit_C_0000789019_20210701_20220630_upper))
(assert (! (>= (- xbrl_fact_us_gaap_GrossProfit_duration_2021_07_01_2022_06_30_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2021_07_01_2022_06_30_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2021_07_01_2022_06_30_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_3_15971244_GrossProfit_C_0000789019_20210701_20220630_lower))

(check-sat)
(get-unsat-core)
(get-model)