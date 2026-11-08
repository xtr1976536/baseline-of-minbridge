(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_gross_profit_fy2025 Real)
(declare-const cost_of_goods_and_services_sold_fy2025 Real)
(declare-const revenue_from_contract_with_customer_excluding_assessed_tax_fy2025 Real)

(assert (! (= cost_of_goods_and_services_sold_fy2025 34478) :named evidence_cost_of_goods_and_services_sold_fy2025))
(assert (! (= revenue_from_contract_with_customer_excluding_assessed_tax_fy2025 52853) :named evidence_revenue_from_contract_with_customer_excluding_assessed_tax_fy2025))

(assert (! (= computed_gross_profit_fy2025 (+ revenue_from_contract_with_customer_excluding_assessed_tax_fy2025 (* (- 1) cost_of_goods_and_services_sold_fy2025))) :named formula_gross_profit_fy2025))

(assert (! (<= (- computed_gross_profit_fy2025 18375) 18.375) :named claim_upper))
(assert (! (<= (- 18375 computed_gross_profit_fy2025) 18.375) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_12_29_2025_12_27_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_CostsAndExpenses_duration_2024_12_29_2025_12_27_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_GrossProfit_duration_2024_12_29_2025_12_27_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_12_29_2025_12_27_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2024_12_29_2025_12_27_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_CostsAndExpenses_duration_2024_12_29_2025_12_27_unit_USD_dims_none 55067) :named evidence_xbrl_fact_us_gaap_CostsAndExpenses_duration_2024_12_29_2025_12_27_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_GrossProfit_duration_2024_12_29_2025_12_27_unit_USD_dims_none 18375) :named evidence_xbrl_fact_us_gaap_GrossProfit_duration_2024_12_29_2025_12_27_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_12_29_2025_12_27_unit_USD_dims_none -2214) :named evidence_xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_12_29_2025_12_27_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= revenue_from_contract_with_customer_excluding_assessed_tax_fy2025 xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2024_12_29_2025_12_27_unit_USD_dims_none) :named xbrl_bind_revenue_from_contract_with_customer_excluding_assessed_tax_fy2025_edgar_2025_12_27_0000050863_26_000011))
(assert (! (= xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2024_12_29_2025_12_27_unit_USD_dims_none 52853) :named xbrl_instance_revenue_from_contract_with_customer_excluding_assessed_tax_fy2025))
(assert (! (= cost_of_goods_and_services_sold_fy2025 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_12_29_2025_12_27_unit_USD_dims_none) :named xbrl_bind_cost_of_goods_and_services_sold_fy2025_edgar_2025_12_27_0000050863_26_000011))
(assert (! (= xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_12_29_2025_12_27_unit_USD_dims_none 34478) :named xbrl_instance_cost_of_goods_and_services_sold_fy2025))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_GrossProfit_duration_2024_12_29_2025_12_27_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2024_12_29_2025_12_27_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_12_29_2025_12_27_unit_USD_dims_none))) 1.5) :named xbrl_calc_0_433660659_GrossProfit_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_GrossProfit_duration_2024_12_29_2025_12_27_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2024_12_29_2025_12_27_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_12_29_2025_12_27_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_0_433660659_GrossProfit_c_1_lower))
(assert (! (<= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_12_29_2025_12_27_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2024_12_29_2025_12_27_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostsAndExpenses_duration_2024_12_29_2025_12_27_unit_USD_dims_none))) 1.5) :named xbrl_calc_20_469884860_OperatingIncomeLoss_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_12_29_2025_12_27_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2024_12_29_2025_12_27_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostsAndExpenses_duration_2024_12_29_2025_12_27_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_20_469884860_OperatingIncomeLoss_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)