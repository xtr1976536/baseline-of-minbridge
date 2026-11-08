(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_gross_profit_fy2024 Real)
(declare-const cost_of_goods_and_services_sold_fy2024 Real)
(declare-const revenues_fy2024 Real)

(assert (! (= cost_of_goods_and_services_sold_fy2024 18324) :named evidence_cost_of_goods_and_services_sold_fy2024))
(assert (! (= revenues_fy2024 47061) :named evidence_revenues_fy2024))

(assert (! (= computed_gross_profit_fy2024 (+ revenues_fy2024 (* (- 1) cost_of_goods_and_services_sold_fy2024))) :named formula_gross_profit_fy2024))

(assert (! (<= (- computed_gross_profit_fy2024 28737) 28.737000000000002) :named claim_upper))
(assert (! (<= (- 28737 computed_gross_profit_fy2024) 28.737000000000002) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_01_01_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_GrossProfit_duration_2024_01_01_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_Revenues_duration_2024_01_01_2024_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_GrossProfit_duration_2024_01_01_2024_12_31_unit_USD_dims_none 28737) :named evidence_xbrl_fact_us_gaap_GrossProfit_duration_2024_01_01_2024_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= revenues_fy2024 xbrl_fact_us_gaap_Revenues_duration_2024_01_01_2024_12_31_unit_USD_dims_none) :named xbrl_bind_revenues_fy2024_edgar_2024_12_31_0000021344_25_000011))
(assert (! (= xbrl_fact_us_gaap_Revenues_duration_2024_01_01_2024_12_31_unit_USD_dims_none 47061) :named xbrl_instance_revenues_fy2024))
(assert (! (= cost_of_goods_and_services_sold_fy2024 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_01_01_2024_12_31_unit_USD_dims_none) :named xbrl_bind_cost_of_goods_and_services_sold_fy2024_edgar_2024_12_31_0000021344_25_000011))
(assert (! (= xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_01_01_2024_12_31_unit_USD_dims_none 18324) :named xbrl_instance_cost_of_goods_and_services_sold_fy2024))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_GrossProfit_duration_2024_01_01_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2024_01_01_2024_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_01_01_2024_12_31_unit_USD_dims_none))) 1.5) :named xbrl_calc_5_611970461_GrossProfit_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_GrossProfit_duration_2024_01_01_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2024_01_01_2024_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_01_01_2024_12_31_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_5_611970461_GrossProfit_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)