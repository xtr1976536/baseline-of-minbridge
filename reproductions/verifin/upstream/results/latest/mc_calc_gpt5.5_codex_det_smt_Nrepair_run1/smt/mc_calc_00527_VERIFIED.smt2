(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_gross_profit_fy2022 Real)
(declare-const cost_of_revenue_fy2022 Real)
(declare-const revenues_fy2022 Real)

(assert (! (= cost_of_revenue_fy2022 27842) :named evidence_cost_of_revenue_fy2022))
(assert (! (= revenues_fy2022 60530) :named evidence_revenues_fy2022))

(assert (! (= computed_gross_profit_fy2022 (+ revenues_fy2022 (* (- 1) cost_of_revenue_fy2022))) :named formula_gross_profit_fy2022))

(assert (! (<= (- computed_gross_profit_fy2022 32688) 32.688000000000002) :named claim_upper))
(assert (! (<= (- 32688 computed_gross_profit_fy2022) 32.688000000000002) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostOfRevenue_duration_2022_01_01_2022_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_GrossProfit_duration_2022_01_01_2022_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_Revenues_duration_2022_01_01_2022_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_GrossProfit_duration_2022_01_01_2022_12_31_unit_USD_dims_none 32687) :named evidence_xbrl_fact_us_gaap_GrossProfit_duration_2022_01_01_2022_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= revenues_fy2022 xbrl_fact_us_gaap_Revenues_duration_2022_01_01_2022_12_31_unit_USD_dims_none) :named xbrl_bind_revenues_fy2022_edgar_2022_12_31_0001558370_23_002376))
(assert (! (= xbrl_fact_us_gaap_Revenues_duration_2022_01_01_2022_12_31_unit_USD_dims_none 60530) :named xbrl_instance_revenues_fy2022))
(assert (! (= cost_of_revenue_fy2022 xbrl_fact_us_gaap_CostOfRevenue_duration_2022_01_01_2022_12_31_unit_USD_dims_none) :named xbrl_bind_cost_of_revenue_fy2022_edgar_2022_12_31_0001558370_23_002376))
(assert (! (= xbrl_fact_us_gaap_CostOfRevenue_duration_2022_01_01_2022_12_31_unit_USD_dims_none 27842) :named xbrl_instance_cost_of_revenue_fy2022))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_GrossProfit_duration_2022_01_01_2022_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2022_01_01_2022_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfRevenue_duration_2022_01_01_2022_12_31_unit_USD_dims_none))) 1.5) :named xbrl_calc_5_336347089_GrossProfit_Duration_1_1_2022_To_12_31_2022_M62iYm1530e69wSMRRzSSg_upper))
(assert (! (>= (- xbrl_fact_us_gaap_GrossProfit_duration_2022_01_01_2022_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2022_01_01_2022_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfRevenue_duration_2022_01_01_2022_12_31_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_5_336347089_GrossProfit_Duration_1_1_2022_To_12_31_2022_M62iYm1530e69wSMRRzSSg_lower))

(check-sat)
(get-unsat-core)
(get-model)