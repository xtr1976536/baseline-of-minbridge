(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_gross_profit_fy2025 Real)
(declare-const cost_of_goods_and_services_sold_fy2025 Real)
(declare-const revenues_fy2025 Real)

(assert (! (= cost_of_goods_and_services_sold_fy2025 43066) :named evidence_cost_of_goods_and_services_sold_fy2025))
(assert (! (= revenues_fy2025 93925) :named evidence_revenues_fy2025))

(assert (! (= computed_gross_profit_fy2025 (+ revenues_fy2025 (* (- 1) cost_of_goods_and_services_sold_fy2025))) :named formula_gross_profit_fy2025))

(assert (! (<= (- computed_gross_profit_fy2025 50110) 50.109999999999999) :named claim_upper))
(assert (! (<= (- 50110 computed_gross_profit_fy2025) 50.109999999999999) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_12_29_2025_12_27_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_GrossProfit_duration_2024_12_29_2025_12_27_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_Revenues_duration_2024_12_29_2025_12_27_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_GrossProfit_duration_2024_12_29_2025_12_27_unit_USD_dims_none 50859) :named evidence_xbrl_fact_us_gaap_GrossProfit_duration_2024_12_29_2025_12_27_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= revenues_fy2025 xbrl_fact_us_gaap_Revenues_duration_2024_12_29_2025_12_27_unit_USD_dims_none) :named xbrl_bind_revenues_fy2025_edgar_2025_12_27_0000077476_26_000007))
(assert (! (= xbrl_fact_us_gaap_Revenues_duration_2024_12_29_2025_12_27_unit_USD_dims_none 93925) :named xbrl_instance_revenues_fy2025))
(assert (! (= cost_of_goods_and_services_sold_fy2025 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_12_29_2025_12_27_unit_USD_dims_none) :named xbrl_bind_cost_of_goods_and_services_sold_fy2025_edgar_2025_12_27_0000077476_26_000007))
(assert (! (= xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_12_29_2025_12_27_unit_USD_dims_none 43066) :named xbrl_instance_cost_of_goods_and_services_sold_fy2025))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_GrossProfit_duration_2024_12_29_2025_12_27_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2024_12_29_2025_12_27_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_12_29_2025_12_27_unit_USD_dims_none))) 1.5) :named xbrl_calc_4_177463439_GrossProfit_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_GrossProfit_duration_2024_12_29_2025_12_27_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2024_12_29_2025_12_27_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_12_29_2025_12_27_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_4_177463439_GrossProfit_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)