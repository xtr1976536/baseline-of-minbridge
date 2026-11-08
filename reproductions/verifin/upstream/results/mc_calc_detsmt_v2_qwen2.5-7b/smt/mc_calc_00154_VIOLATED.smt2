(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_gross_profit_fy2025 Real)
(declare-const cost_of_revenue_fy2025 Real)
(declare-const revenues_fy2025 Real)

(assert (! (= cost_of_revenue_fy2025 2551) :named evidence_cost_of_revenue_fy2025))
(assert (! (= revenues_fy2025 23769) :named evidence_revenues_fy2025))

(assert (! (= computed_gross_profit_fy2025 (+ revenues_fy2025 (* (- 1) cost_of_revenue_fy2025))) :named formula_gross_profit_fy2025))

(assert (! (<= (- computed_gross_profit_fy2025 19147) 19.147000000000002) :named claim_upper))
(assert (! (<= (- 19147 computed_gross_profit_fy2025) 19.147000000000002) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostOfRevenue_duration_2024_11_30_2025_11_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_GrossProfit_duration_2024_11_30_2025_11_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_Revenues_duration_2024_11_30_2025_11_28_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_GrossProfit_duration_2024_11_30_2025_11_28_unit_USD_dims_none 21218) :named evidence_xbrl_fact_us_gaap_GrossProfit_duration_2024_11_30_2025_11_28_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= revenues_fy2025 xbrl_fact_us_gaap_Revenues_duration_2024_11_30_2025_11_28_unit_USD_dims_none) :named xbrl_bind_revenues_fy2025_edgar_2025_11_28_0000796343_26_000003))
(assert (! (= xbrl_fact_us_gaap_Revenues_duration_2024_11_30_2025_11_28_unit_USD_dims_none 23769) :named xbrl_instance_revenues_fy2025))
(assert (! (= cost_of_revenue_fy2025 xbrl_fact_us_gaap_CostOfRevenue_duration_2024_11_30_2025_11_28_unit_USD_dims_none) :named xbrl_bind_cost_of_revenue_fy2025_edgar_2025_11_28_0000796343_26_000003))
(assert (! (= xbrl_fact_us_gaap_CostOfRevenue_duration_2024_11_30_2025_11_28_unit_USD_dims_none 2551) :named xbrl_instance_cost_of_revenue_fy2025))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_GrossProfit_duration_2024_11_30_2025_11_28_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2024_11_30_2025_11_28_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfRevenue_duration_2024_11_30_2025_11_28_unit_USD_dims_none))) 1.5) :named xbrl_calc_8_976020706_GrossProfit_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_GrossProfit_duration_2024_11_30_2025_11_28_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2024_11_30_2025_11_28_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfRevenue_duration_2024_11_30_2025_11_28_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_8_976020706_GrossProfit_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)