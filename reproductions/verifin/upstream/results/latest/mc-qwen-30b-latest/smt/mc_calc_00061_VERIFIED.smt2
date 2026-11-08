(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_gross_profit_fy2026 Real)
(declare-const cost_of_revenue_fy2026 Real)
(declare-const revenues_fy2026 Real)

(assert (! (= cost_of_revenue_fy2026 62475) :named evidence_cost_of_revenue_fy2026))
(assert (! (= revenues_fy2026 215938) :named evidence_revenues_fy2026))

(assert (! (= computed_gross_profit_fy2026 (+ revenues_fy2026 (* (- 1) cost_of_revenue_fy2026))) :named formula_gross_profit_fy2026))

(assert (! (<= (- computed_gross_profit_fy2026 153463) 153.46299999999999) :named claim_upper))
(assert (! (<= (- 153463 computed_gross_profit_fy2026) 153.46299999999999) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostOfRevenue_duration_2025_01_27_2026_01_25_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_GrossProfit_duration_2025_01_27_2026_01_25_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_Revenues_duration_2025_01_27_2026_01_25_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_GrossProfit_duration_2025_01_27_2026_01_25_unit_USD_dims_none 153463) :named evidence_xbrl_fact_us_gaap_GrossProfit_duration_2025_01_27_2026_01_25_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= revenues_fy2026 xbrl_fact_us_gaap_Revenues_duration_2025_01_27_2026_01_25_unit_USD_dims_none) :named xbrl_bind_revenues_fy2026_edgar_2026_01_25_0001045810_26_000021))
(assert (! (= xbrl_fact_us_gaap_Revenues_duration_2025_01_27_2026_01_25_unit_USD_dims_none 215938) :named xbrl_instance_revenues_fy2026))
(assert (! (= cost_of_revenue_fy2026 xbrl_fact_us_gaap_CostOfRevenue_duration_2025_01_27_2026_01_25_unit_USD_dims_none) :named xbrl_bind_cost_of_revenue_fy2026_edgar_2026_01_25_0001045810_26_000021))
(assert (! (= xbrl_fact_us_gaap_CostOfRevenue_duration_2025_01_27_2026_01_25_unit_USD_dims_none 62475) :named xbrl_instance_cost_of_revenue_fy2026))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_GrossProfit_duration_2025_01_27_2026_01_25_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2025_01_27_2026_01_25_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfRevenue_duration_2025_01_27_2026_01_25_unit_USD_dims_none))) 1.5) :named xbrl_calc_2_576763843_GrossProfit_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_GrossProfit_duration_2025_01_27_2026_01_25_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2025_01_27_2026_01_25_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfRevenue_duration_2025_01_27_2026_01_25_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_2_576763843_GrossProfit_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)