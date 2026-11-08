(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_gross_profit_fy2025 Real)
(declare-const cost_of_revenue_fy2025 Real)
(declare-const revenues_fy2025 Real)

(assert (! (= cost_of_revenue_fy2025 28239) :named evidence_cost_of_revenue_fy2025))
(assert (! (= revenues_fy2025 67535) :named evidence_revenues_fy2025))

(assert (! (= computed_gross_profit_fy2025 (+ revenues_fy2025 (* (- 1) cost_of_revenue_fy2025))) :named formula_gross_profit_fy2025))

(assert (! (<= (- computed_gross_profit_fy2025 39296) 39.295999999999999) :named claim_upper))
(assert (! (<= (- 39296 computed_gross_profit_fy2025) 39.295999999999999) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostOfRevenue_duration_2025_01_01_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_GrossProfit_duration_2025_01_01_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_Revenues_duration_2025_01_01_2025_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_GrossProfit_duration_2025_01_01_2025_12_31_unit_USD_dims_none 39297) :named evidence_xbrl_fact_us_gaap_GrossProfit_duration_2025_01_01_2025_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= revenues_fy2025 xbrl_fact_us_gaap_Revenues_duration_2025_01_01_2025_12_31_unit_USD_dims_none) :named xbrl_bind_revenues_fy2025_edgar_2025_12_31_0000051143_26_000010))
(assert (! (= xbrl_fact_us_gaap_Revenues_duration_2025_01_01_2025_12_31_unit_USD_dims_none 67535) :named xbrl_instance_revenues_fy2025))
(assert (! (= cost_of_revenue_fy2025 xbrl_fact_us_gaap_CostOfRevenue_duration_2025_01_01_2025_12_31_unit_USD_dims_none) :named xbrl_bind_cost_of_revenue_fy2025_edgar_2025_12_31_0000051143_26_000010))
(assert (! (= xbrl_fact_us_gaap_CostOfRevenue_duration_2025_01_01_2025_12_31_unit_USD_dims_none 28239) :named xbrl_instance_cost_of_revenue_fy2025))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_GrossProfit_duration_2025_01_01_2025_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2025_01_01_2025_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfRevenue_duration_2025_01_01_2025_12_31_unit_USD_dims_none))) 1.5) :named xbrl_calc_4_783931725_GrossProfit_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_GrossProfit_duration_2025_01_01_2025_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2025_01_01_2025_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfRevenue_duration_2025_01_01_2025_12_31_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_4_783931725_GrossProfit_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)