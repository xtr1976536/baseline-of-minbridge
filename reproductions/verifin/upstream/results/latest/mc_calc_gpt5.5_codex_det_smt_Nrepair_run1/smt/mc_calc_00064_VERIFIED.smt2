(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_gross_profit_fy2025 Real)
(declare-const cost_of_goods_and_services_sold_fy2025 Real)
(declare-const revenue_from_contract_with_customer_excluding_assessed_tax_fy2025 Real)

(assert (! (= cost_of_goods_and_services_sold_fy2025 30256) :named evidence_cost_of_goods_and_services_sold_fy2025))
(assert (! (= revenue_from_contract_with_customer_excluding_assessed_tax_fy2025 94193) :named evidence_revenue_from_contract_with_customer_excluding_assessed_tax_fy2025))

(assert (! (= computed_gross_profit_fy2025 (+ revenue_from_contract_with_customer_excluding_assessed_tax_fy2025 (* (- 1) cost_of_goods_and_services_sold_fy2025))) :named formula_gross_profit_fy2025))

(assert (! (<= (- computed_gross_profit_fy2025 63937) 63.937000000000005) :named claim_upper))
(assert (! (<= (- 63937 computed_gross_profit_fy2025) 63.937000000000005) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_12_30_2025_12_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_GrossProfit_duration_2024_12_30_2025_12_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2024_12_30_2025_12_28_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_GrossProfit_duration_2024_12_30_2025_12_28_unit_USD_dims_none 63937) :named evidence_xbrl_fact_us_gaap_GrossProfit_duration_2024_12_30_2025_12_28_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= revenue_from_contract_with_customer_excluding_assessed_tax_fy2025 xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2024_12_30_2025_12_28_unit_USD_dims_none) :named xbrl_bind_revenue_from_contract_with_customer_excluding_assessed_tax_fy2025_edgar_2025_12_28_0000200406_26_000016))
(assert (! (= xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2024_12_30_2025_12_28_unit_USD_dims_none 94193) :named xbrl_instance_revenue_from_contract_with_customer_excluding_assessed_tax_fy2025))
(assert (! (= cost_of_goods_and_services_sold_fy2025 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_12_30_2025_12_28_unit_USD_dims_none) :named xbrl_bind_cost_of_goods_and_services_sold_fy2025_edgar_2025_12_28_0000200406_26_000016))
(assert (! (= xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_12_30_2025_12_28_unit_USD_dims_none 30256) :named xbrl_instance_cost_of_goods_and_services_sold_fy2025))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_GrossProfit_duration_2024_12_30_2025_12_28_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2024_12_30_2025_12_28_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_12_30_2025_12_28_unit_USD_dims_none))) 1.5) :named xbrl_calc_9_77374093_GrossProfit_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_GrossProfit_duration_2024_12_30_2025_12_28_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2024_12_30_2025_12_28_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_12_30_2025_12_28_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_9_77374093_GrossProfit_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)