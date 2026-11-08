(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_gross_profit_fy2024 Real)
(declare-const cost_of_revenue_fy2024 Real)
(declare-const revenues_fy2024 Real)

(assert (! (= cost_of_revenue_fy2024 2358) :named evidence_cost_of_revenue_fy2024))
(assert (! (= revenues_fy2024 21505) :named evidence_revenues_fy2024))

(assert (! (= computed_gross_profit_fy2024 (+ revenues_fy2024 (* (- 1) cost_of_revenue_fy2024))) :named formula_gross_profit_fy2024))

(assert (! (<= (- computed_gross_profit_fy2024 19147) 19.147000000000002) :named claim_upper))
(assert (! (<= (- 19147 computed_gross_profit_fy2024) 19.147000000000002) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostOfRevenue_duration_2023_12_02_2024_11_29_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_GrossProfit_duration_2023_12_02_2024_11_29_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_Revenues_duration_2023_12_02_2024_11_29_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_GrossProfit_duration_2023_12_02_2024_11_29_unit_USD_dims_none 19147) :named evidence_xbrl_fact_us_gaap_GrossProfit_duration_2023_12_02_2024_11_29_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= revenues_fy2024 xbrl_fact_us_gaap_Revenues_duration_2023_12_02_2024_11_29_unit_USD_dims_none) :named xbrl_bind_revenues_fy2024_edgar_2024_11_29_0000796343_25_000004))
(assert (! (= xbrl_fact_us_gaap_Revenues_duration_2023_12_02_2024_11_29_unit_USD_dims_none 21505) :named xbrl_instance_revenues_fy2024))
(assert (! (= cost_of_revenue_fy2024 xbrl_fact_us_gaap_CostOfRevenue_duration_2023_12_02_2024_11_29_unit_USD_dims_none) :named xbrl_bind_cost_of_revenue_fy2024_edgar_2024_11_29_0000796343_25_000004))
(assert (! (= xbrl_fact_us_gaap_CostOfRevenue_duration_2023_12_02_2024_11_29_unit_USD_dims_none 2358) :named xbrl_instance_cost_of_revenue_fy2024))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_GrossProfit_duration_2023_12_02_2024_11_29_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2023_12_02_2024_11_29_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfRevenue_duration_2023_12_02_2024_11_29_unit_USD_dims_none))) 1.5) :named xbrl_calc_11_976020706_GrossProfit_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_GrossProfit_duration_2023_12_02_2024_11_29_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2023_12_02_2024_11_29_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfRevenue_duration_2023_12_02_2024_11_29_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_11_976020706_GrossProfit_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)