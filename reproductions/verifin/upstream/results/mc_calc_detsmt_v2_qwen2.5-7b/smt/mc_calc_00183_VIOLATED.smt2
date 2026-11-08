(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_gross_profit_fy2026 Real)
(declare-const cost_of_goods_and_services_sold_fy2026 Real)
(declare-const revenue_from_contract_with_customer_excluding_assessed_tax_fy2026 Real)

(assert (! (= cost_of_goods_and_services_sold_fy2026 9270) :named evidence_cost_of_goods_and_services_sold_fy2026))
(assert (! (= revenue_from_contract_with_customer_excluding_assessed_tax_fy2026 41525) :named evidence_revenue_from_contract_with_customer_excluding_assessed_tax_fy2026))

(assert (! (= computed_gross_profit_fy2026 (+ revenue_from_contract_with_customer_excluding_assessed_tax_fy2026 (* (- 1) cost_of_goods_and_services_sold_fy2026))) :named formula_gross_profit_fy2026))

(assert (! (<= (- computed_gross_profit_fy2026 32355) 32.355000000000004) :named claim_upper))
(assert (! (<= (- 32355 computed_gross_profit_fy2026) 32.355000000000004) :named claim_lower))

; XBRL calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_GrossProfit_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_GrossProfit_duration_2025_02_01_2026_01_31_unit_USD_dims_none 32255) :named evidence_xbrl_fact_us_gaap_GrossProfit_duration_2025_02_01_2026_01_31_unit_USD_dims_none))

; IR-to-XBRL bindings and independent instance-value witnesses.
(assert (! (= revenue_from_contract_with_customer_excluding_assessed_tax_fy2026 xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_01_2026_01_31_unit_USD_dims_none) :named xbrl_bind_revenue_from_contract_with_customer_excluding_assessed_tax_fy2026_c_1))
(assert (! (= xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_01_2026_01_31_unit_USD_dims_none 41525) :named xbrl_instance_revenue_from_contract_with_customer_excluding_assessed_tax_fy2026))
(assert (! (= cost_of_goods_and_services_sold_fy2026 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2025_02_01_2026_01_31_unit_USD_dims_none) :named xbrl_bind_cost_of_goods_and_services_sold_fy2026_c_1))
(assert (! (= xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2025_02_01_2026_01_31_unit_USD_dims_none 9270) :named xbrl_instance_cost_of_goods_and_services_sold_fy2026))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_GrossProfit_duration_2025_02_01_2026_01_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_01_2026_01_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2025_02_01_2026_01_31_unit_USD_dims_none))) 1.5) :named xbrl_calc_8_204774902_GrossProfit_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_GrossProfit_duration_2025_02_01_2026_01_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_01_2026_01_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2025_02_01_2026_01_31_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_8_204774902_GrossProfit_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)