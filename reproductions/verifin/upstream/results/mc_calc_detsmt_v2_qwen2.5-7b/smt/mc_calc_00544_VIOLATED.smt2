(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_gross_profit_fy2023 Real)
(declare-const cost_of_goods_and_services_sold_fy2023 Real)
(declare-const revenues_fy2023 Real)

(assert (! (= cost_of_goods_and_services_sold_fy2023 41881) :named evidence_cost_of_goods_and_services_sold_fy2023))
(assert (! (= revenues_fy2023 91471) :named evidence_revenues_fy2023))

(assert (! (= computed_gross_profit_fy2023 (+ revenues_fy2023 (* (- 1) cost_of_goods_and_services_sold_fy2023))) :named formula_gross_profit_fy2023))

(assert (! (<= (- computed_gross_profit_fy2023 45800) 45.800000000000004) :named claim_upper))
(assert (! (<= (- 45800 computed_gross_profit_fy2023) 45.800000000000004) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2023_01_01_2023_12_30_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_GrossProfit_duration_2023_01_01_2023_12_30_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_Revenues_duration_2023_01_01_2023_12_30_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_GrossProfit_duration_2023_01_01_2023_12_30_unit_USD_dims_none 49590) :named evidence_xbrl_fact_us_gaap_GrossProfit_duration_2023_01_01_2023_12_30_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= revenues_fy2023 xbrl_fact_us_gaap_Revenues_duration_2023_01_01_2023_12_30_unit_USD_dims_none) :named xbrl_bind_revenues_fy2023_edgar_2023_12_30_0000077476_24_000008))
(assert (! (= xbrl_fact_us_gaap_Revenues_duration_2023_01_01_2023_12_30_unit_USD_dims_none 91471) :named xbrl_instance_revenues_fy2023))
(assert (! (= cost_of_goods_and_services_sold_fy2023 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2023_01_01_2023_12_30_unit_USD_dims_none) :named xbrl_bind_cost_of_goods_and_services_sold_fy2023_edgar_2023_12_30_0000077476_24_000008))
(assert (! (= xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2023_01_01_2023_12_30_unit_USD_dims_none 41881) :named xbrl_instance_cost_of_goods_and_services_sold_fy2023))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_GrossProfit_duration_2023_01_01_2023_12_30_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2023_01_01_2023_12_30_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2023_01_01_2023_12_30_unit_USD_dims_none))) 1.5) :named xbrl_calc_1_177463439_GrossProfit_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_GrossProfit_duration_2023_01_01_2023_12_30_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2023_01_01_2023_12_30_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2023_01_01_2023_12_30_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_1_177463439_GrossProfit_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)