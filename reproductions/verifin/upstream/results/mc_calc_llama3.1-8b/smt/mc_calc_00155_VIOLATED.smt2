(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_expenses_fy2026 Real)
(declare-const general_and_administrative_expense_fy2026 Real)
(declare-const research_and_development_expense_fy2026 Real)
(declare-const restructuring_charges_fy2026 Real)
(declare-const selling_and_marketing_expense_fy2026 Real)

(assert (! (= general_and_administrative_expense_fy2026 3000.0) :named evidence_general_and_administrative_expense_fy2026))
(assert (! (= research_and_development_expense_fy2026 5993.0) :named evidence_research_and_development_expense_fy2026))
(assert (! (= restructuring_charges_fy2026 586.0) :named evidence_restructuring_charges_fy2026))
(assert (! (= selling_and_marketing_expense_fy2026 14345.0) :named evidence_selling_and_marketing_expense_fy2026))

(assert (! (= computed_operating_expenses_fy2026 (+ (+ selling_and_marketing_expense_fy2026 general_and_administrative_expense_fy2026) research_and_development_expense_fy2026 restructuring_charges_fy2026)) :named formula_operating_expenses_fy2026))

(assert (! (or (> selling_and_marketing_expense_fy2026 0) (< selling_and_marketing_expense_fy2026 0)) :named denom_nonzero))
(assert (! (or (> general_and_administrative_expense_fy2026 0) (< general_and_administrative_expense_fy2026 0)) :named denom_nonzero_1))
(assert (! (or (> research_and_development_expense_fy2026 0) (< research_and_development_expense_fy2026 0)) :named denom_nonzero_2))
(assert (! (or (> restructuring_charges_fy2026 0) (< restructuring_charges_fy2026 0)) :named denom_nonzero_3))

(assert (! (<= (- computed_operating_expenses_fy2026 22047.0) 220.47) :named claim_upper))
(assert (! (<= (- 22047.0 computed_operating_expenses_fy2026) 220.47) :named claim_lower))

; XBRL calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_GeneralAndAdministrativeExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingExpenses_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RestructuringCharges_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_SellingAndMarketingExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_OperatingExpenses_duration_2025_02_01_2026_01_31_unit_USD_dims_none 23924) :named evidence_xbrl_fact_us_gaap_OperatingExpenses_duration_2025_02_01_2026_01_31_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_SellingAndMarketingExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none 14345) :named evidence_xbrl_fact_us_gaap_SellingAndMarketingExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none))

; IR-to-XBRL bindings and independent instance-value witnesses.
(assert (! (= general_and_administrative_expense_fy2026 xbrl_fact_us_gaap_GeneralAndAdministrativeExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none) :named xbrl_bind_general_and_administrative_expense_fy2026_c_1))
(assert (! (= xbrl_fact_us_gaap_GeneralAndAdministrativeExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none 3000) :named xbrl_instance_general_and_administrative_expense_fy2026))
(assert (! (= research_and_development_expense_fy2026 xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none) :named xbrl_bind_research_and_development_expense_fy2026_c_1))
(assert (! (= xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none 5993) :named xbrl_instance_research_and_development_expense_fy2026))
(assert (! (= restructuring_charges_fy2026 xbrl_fact_us_gaap_RestructuringCharges_duration_2025_02_01_2026_01_31_unit_USD_dims_none) :named xbrl_bind_restructuring_charges_fy2026_c_1))
(assert (! (= xbrl_fact_us_gaap_RestructuringCharges_duration_2025_02_01_2026_01_31_unit_USD_dims_none 586) :named xbrl_instance_restructuring_charges_fy2026))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_OperatingExpenses_duration_2025_02_01_2026_01_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_SellingAndMarketingExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none xbrl_fact_us_gaap_GeneralAndAdministrativeExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none xbrl_fact_us_gaap_RestructuringCharges_duration_2025_02_01_2026_01_31_unit_USD_dims_none)) 2.5) :named xbrl_calc_7_204774902_OperatingExpenses_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_OperatingExpenses_duration_2025_02_01_2026_01_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_SellingAndMarketingExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none xbrl_fact_us_gaap_GeneralAndAdministrativeExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none xbrl_fact_us_gaap_RestructuringCharges_duration_2025_02_01_2026_01_31_unit_USD_dims_none)) (- 2.5)) :named xbrl_calc_7_204774902_OperatingExpenses_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)