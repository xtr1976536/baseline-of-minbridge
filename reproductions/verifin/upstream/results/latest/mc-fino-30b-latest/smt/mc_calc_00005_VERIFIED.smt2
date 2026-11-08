(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_income_loss_fy2026 Real)
(declare-const gross_profit_fy2026 Real)
(declare-const operating_expenses_fy2026 Real)

(assert (! (= gross_profit_fy2026 153463) :named evidence_gross_profit_fy2026))
(assert (! (= operating_expenses_fy2026 23076) :named evidence_operating_expenses_fy2026))

(assert (! (= computed_operating_income_loss_fy2026 (+ gross_profit_fy2026 (* (- 1) operating_expenses_fy2026))) :named formula_operating_income_loss_fy2026))

(assert (! (<= (- computed_operating_income_loss_fy2026 130387) 130.387) :named claim_upper))
(assert (! (<= (- 130387 computed_operating_income_loss_fy2026) 130.387) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostOfRevenue_duration_2025_01_27_2026_01_25_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_GrossProfit_duration_2025_01_27_2026_01_25_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingExpenses_duration_2025_01_27_2026_01_25_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_01_27_2026_01_25_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2025_01_27_2026_01_25_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_Revenues_duration_2025_01_27_2026_01_25_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_01_27_2026_01_25_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_CostOfRevenue_duration_2025_01_27_2026_01_25_unit_USD_dims_none 62475) :named evidence_xbrl_fact_us_gaap_CostOfRevenue_duration_2025_01_27_2026_01_25_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_01_27_2026_01_25_unit_USD_dims_none 130387) :named evidence_xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_01_27_2026_01_25_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2025_01_27_2026_01_25_unit_USD_dims_none 18497) :named evidence_xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2025_01_27_2026_01_25_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_Revenues_duration_2025_01_27_2026_01_25_unit_USD_dims_none 215938) :named evidence_xbrl_fact_us_gaap_Revenues_duration_2025_01_27_2026_01_25_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_01_27_2026_01_25_unit_USD_dims_none 4579) :named evidence_xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_01_27_2026_01_25_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= gross_profit_fy2026 xbrl_fact_us_gaap_GrossProfit_duration_2025_01_27_2026_01_25_unit_USD_dims_none) :named xbrl_bind_gross_profit_fy2026_edgar_2026_01_25_0001045810_26_000021))
(assert (! (= xbrl_fact_us_gaap_GrossProfit_duration_2025_01_27_2026_01_25_unit_USD_dims_none 153463) :named xbrl_instance_gross_profit_fy2026))
(assert (! (= operating_expenses_fy2026 xbrl_fact_us_gaap_OperatingExpenses_duration_2025_01_27_2026_01_25_unit_USD_dims_none) :named xbrl_bind_operating_expenses_fy2026_edgar_2026_01_25_0001045810_26_000021))
(assert (! (= xbrl_fact_us_gaap_OperatingExpenses_duration_2025_01_27_2026_01_25_unit_USD_dims_none 23076) :named xbrl_instance_operating_expenses_fy2026))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_01_27_2026_01_25_unit_USD_dims_none (+ xbrl_fact_us_gaap_GrossProfit_duration_2025_01_27_2026_01_25_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_OperatingExpenses_duration_2025_01_27_2026_01_25_unit_USD_dims_none))) 1.5) :named xbrl_calc_0_576763843_OperatingIncomeLoss_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_01_27_2026_01_25_unit_USD_dims_none (+ xbrl_fact_us_gaap_GrossProfit_duration_2025_01_27_2026_01_25_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_OperatingExpenses_duration_2025_01_27_2026_01_25_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_0_576763843_OperatingIncomeLoss_c_1_lower))
(assert (! (<= (- xbrl_fact_us_gaap_OperatingExpenses_duration_2025_01_27_2026_01_25_unit_USD_dims_none (+ xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2025_01_27_2026_01_25_unit_USD_dims_none xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_01_27_2026_01_25_unit_USD_dims_none)) 1.5) :named xbrl_calc_1_576763843_OperatingExpenses_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_OperatingExpenses_duration_2025_01_27_2026_01_25_unit_USD_dims_none (+ xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2025_01_27_2026_01_25_unit_USD_dims_none xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_01_27_2026_01_25_unit_USD_dims_none)) (- 1.5)) :named xbrl_calc_1_576763843_OperatingExpenses_c_1_lower))
(assert (! (<= (- xbrl_fact_us_gaap_GrossProfit_duration_2025_01_27_2026_01_25_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2025_01_27_2026_01_25_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfRevenue_duration_2025_01_27_2026_01_25_unit_USD_dims_none))) 1.5) :named xbrl_calc_2_576763843_GrossProfit_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_GrossProfit_duration_2025_01_27_2026_01_25_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2025_01_27_2026_01_25_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfRevenue_duration_2025_01_27_2026_01_25_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_2_576763843_GrossProfit_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)