(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_expenses_fy2024 Real)
(declare-const research_and_development_expense_fy2024 Real)
(declare-const selling_general_and_administrative_expense_fy2024 Real)

(assert (! (= research_and_development_expense_fy2024 31370) :named evidence_research_and_development_expense_fy2024))
(assert (! (= selling_general_and_administrative_expense_fy2024 26097) :named evidence_selling_general_and_administrative_expense_fy2024))

(assert (! (= computed_operating_expenses_fy2024 (+ research_and_development_expense_fy2024 selling_general_and_administrative_expense_fy2024)) :named formula_operating_expenses_fy2024))

(assert (! (<= (- computed_operating_expenses_fy2024 57467) 57.466999999999999) :named claim_upper))
(assert (! (<= (- 57467 computed_operating_expenses_fy2024) 57.466999999999999) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_OperatingExpenses_duration_2023_10_01_2024_09_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2023_10_01_2024_09_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2023_10_01_2024_09_28_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_OperatingExpenses_duration_2023_10_01_2024_09_28_unit_USD_dims_none 57467) :named evidence_xbrl_fact_us_gaap_OperatingExpenses_duration_2023_10_01_2024_09_28_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= research_and_development_expense_fy2024 xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2023_10_01_2024_09_28_unit_USD_dims_none) :named xbrl_bind_research_and_development_expense_fy2024_edgar_2024_09_28_0000320193_24_000123))
(assert (! (= xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2023_10_01_2024_09_28_unit_USD_dims_none 31370) :named xbrl_instance_research_and_development_expense_fy2024))
(assert (! (= selling_general_and_administrative_expense_fy2024 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2023_10_01_2024_09_28_unit_USD_dims_none) :named xbrl_bind_selling_general_and_administrative_expense_fy2024_edgar_2024_09_28_0000320193_24_000123))
(assert (! (= xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2023_10_01_2024_09_28_unit_USD_dims_none 26097) :named xbrl_instance_selling_general_and_administrative_expense_fy2024))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_OperatingExpenses_duration_2023_10_01_2024_09_28_unit_USD_dims_none (+ xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2023_10_01_2024_09_28_unit_USD_dims_none xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2023_10_01_2024_09_28_unit_USD_dims_none)) 1.5) :named xbrl_calc_0_928818934_OperatingExpenses_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_OperatingExpenses_duration_2023_10_01_2024_09_28_unit_USD_dims_none (+ xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2023_10_01_2024_09_28_unit_USD_dims_none xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2023_10_01_2024_09_28_unit_USD_dims_none)) (- 1.5)) :named xbrl_calc_0_928818934_OperatingExpenses_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)