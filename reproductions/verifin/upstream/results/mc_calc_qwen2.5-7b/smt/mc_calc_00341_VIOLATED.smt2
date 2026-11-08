(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_income_loss_fy2025 Real)
(declare-const gross_profit_fy2025 Real)
(declare-const operating_expenses_fy2025 Real)

(assert (! (= gross_profit_fy2025 97858.0) :named evidence_gross_profit_fy2025))
(assert (! (= operating_expenses_fy2025 16405.0) :named evidence_operating_expenses_fy2025))

(assert (! (= computed_operating_income_loss_fy2025 (+ gross_profit_fy2025 (* -1 operating_expenses_fy2025))) :named formula_operating_income_loss_fy2025))

(assert (! (or (> operating_expenses_fy2025 0) (< operating_expenses_fy2025 0)) :named denom_nonzero))

(assert (! (<= (- computed_operating_income_loss_fy2025 -31400.0) 0.01) :named claim_upper))
(assert (! (<= (- -31400.0 computed_operating_income_loss_fy2025) 0.01) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_nvda_BusinessCombinationAdvancedConsiderationWrittenOff_duration_2024_01_29_2025_01_26_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_CostOfRevenue_duration_2024_01_29_2025_01_26_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_GrossProfit_duration_2024_01_29_2025_01_26_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingExpenses_duration_2024_01_29_2025_01_26_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_01_29_2025_01_26_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2024_01_29_2025_01_26_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_Revenues_duration_2024_01_29_2025_01_26_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2024_01_29_2025_01_26_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_nvda_BusinessCombinationAdvancedConsiderationWrittenOff_duration_2024_01_29_2025_01_26_unit_USD_dims_none 0) :named evidence_xbrl_fact_nvda_BusinessCombinationAdvancedConsiderationWrittenOff_duration_2024_01_29_2025_01_26_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_CostOfRevenue_duration_2024_01_29_2025_01_26_unit_USD_dims_none 32639) :named evidence_xbrl_fact_us_gaap_CostOfRevenue_duration_2024_01_29_2025_01_26_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_01_29_2025_01_26_unit_USD_dims_none 81453) :named evidence_xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_01_29_2025_01_26_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2024_01_29_2025_01_26_unit_USD_dims_none 12914) :named evidence_xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2024_01_29_2025_01_26_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_Revenues_duration_2024_01_29_2025_01_26_unit_USD_dims_none 130497) :named evidence_xbrl_fact_us_gaap_Revenues_duration_2024_01_29_2025_01_26_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2024_01_29_2025_01_26_unit_USD_dims_none 3491) :named evidence_xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2024_01_29_2025_01_26_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= gross_profit_fy2025 xbrl_fact_us_gaap_GrossProfit_duration_2024_01_29_2025_01_26_unit_USD_dims_none) :named xbrl_bind_gross_profit_fy2025_edgar_2025_01_26_0001045810_25_000023))
(assert (! (= xbrl_fact_us_gaap_GrossProfit_duration_2024_01_29_2025_01_26_unit_USD_dims_none 97858) :named xbrl_instance_gross_profit_fy2025))
(assert (! (= operating_expenses_fy2025 xbrl_fact_us_gaap_OperatingExpenses_duration_2024_01_29_2025_01_26_unit_USD_dims_none) :named xbrl_bind_operating_expenses_fy2025_edgar_2025_01_26_0001045810_25_000023))
(assert (! (= xbrl_fact_us_gaap_OperatingExpenses_duration_2024_01_29_2025_01_26_unit_USD_dims_none 16405) :named xbrl_instance_operating_expenses_fy2025))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_GrossProfit_duration_2024_01_29_2025_01_26_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2024_01_29_2025_01_26_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfRevenue_duration_2024_01_29_2025_01_26_unit_USD_dims_none))) 1.5) :named xbrl_calc_0_576763843_GrossProfit_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_GrossProfit_duration_2024_01_29_2025_01_26_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2024_01_29_2025_01_26_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfRevenue_duration_2024_01_29_2025_01_26_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_0_576763843_GrossProfit_c_1_lower))
(assert (! (<= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_01_29_2025_01_26_unit_USD_dims_none (+ xbrl_fact_us_gaap_GrossProfit_duration_2024_01_29_2025_01_26_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_OperatingExpenses_duration_2024_01_29_2025_01_26_unit_USD_dims_none))) 1.5) :named xbrl_calc_1_576763843_OperatingIncomeLoss_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_01_29_2025_01_26_unit_USD_dims_none (+ xbrl_fact_us_gaap_GrossProfit_duration_2024_01_29_2025_01_26_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_OperatingExpenses_duration_2024_01_29_2025_01_26_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_1_576763843_OperatingIncomeLoss_c_1_lower))
(assert (! (<= (- xbrl_fact_us_gaap_OperatingExpenses_duration_2024_01_29_2025_01_26_unit_USD_dims_none (+ xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2024_01_29_2025_01_26_unit_USD_dims_none xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2024_01_29_2025_01_26_unit_USD_dims_none xbrl_fact_nvda_BusinessCombinationAdvancedConsiderationWrittenOff_duration_2024_01_29_2025_01_26_unit_USD_dims_none)) 2) :named xbrl_calc_3_576763843_OperatingExpenses_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_OperatingExpenses_duration_2024_01_29_2025_01_26_unit_USD_dims_none (+ xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2024_01_29_2025_01_26_unit_USD_dims_none xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2024_01_29_2025_01_26_unit_USD_dims_none xbrl_fact_nvda_BusinessCombinationAdvancedConsiderationWrittenOff_duration_2024_01_29_2025_01_26_unit_USD_dims_none)) (- 2)) :named xbrl_calc_3_576763843_OperatingExpenses_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)