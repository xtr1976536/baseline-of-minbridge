(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_expenses_fy2026 Real)
(declare-const research_and_development_expense_fy2026 Real)
(declare-const selling_general_and_administrative_expense_fy2026 Real)

(assert (! (= research_and_development_expense_fy2026 18497) :named evidence_research_and_development_expense_fy2026))
(assert (! (= selling_general_and_administrative_expense_fy2026 4579) :named evidence_selling_general_and_administrative_expense_fy2026))

(assert (! (= computed_operating_expenses_fy2026 (+ research_and_development_expense_fy2026 selling_general_and_administrative_expense_fy2026)) :named formula_operating_expenses_fy2026))

(assert (! (<= (- computed_operating_expenses_fy2026 23076) 23.076000000000001) :named claim_upper))
(assert (! (<= (- 23076 computed_operating_expenses_fy2026) 23.076000000000001) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_OperatingExpenses_duration_2025_01_27_2026_01_25_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2025_01_27_2026_01_25_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_01_27_2026_01_25_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_OperatingExpenses_duration_2025_01_27_2026_01_25_unit_USD_dims_none 23076) :named evidence_xbrl_fact_us_gaap_OperatingExpenses_duration_2025_01_27_2026_01_25_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= research_and_development_expense_fy2026 xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2025_01_27_2026_01_25_unit_USD_dims_none) :named xbrl_bind_research_and_development_expense_fy2026_edgar_2026_01_25_0001045810_26_000021))
(assert (! (= xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2025_01_27_2026_01_25_unit_USD_dims_none 18497) :named xbrl_instance_research_and_development_expense_fy2026))
(assert (! (= selling_general_and_administrative_expense_fy2026 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_01_27_2026_01_25_unit_USD_dims_none) :named xbrl_bind_selling_general_and_administrative_expense_fy2026_edgar_2026_01_25_0001045810_26_000021))
(assert (! (= xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_01_27_2026_01_25_unit_USD_dims_none 4579) :named xbrl_instance_selling_general_and_administrative_expense_fy2026))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_OperatingExpenses_duration_2025_01_27_2026_01_25_unit_USD_dims_none (+ xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2025_01_27_2026_01_25_unit_USD_dims_none xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_01_27_2026_01_25_unit_USD_dims_none)) 1.5) :named xbrl_calc_1_576763843_OperatingExpenses_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_OperatingExpenses_duration_2025_01_27_2026_01_25_unit_USD_dims_none (+ xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2025_01_27_2026_01_25_unit_USD_dims_none xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_01_27_2026_01_25_unit_USD_dims_none)) (- 1.5)) :named xbrl_calc_1_576763843_OperatingExpenses_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)