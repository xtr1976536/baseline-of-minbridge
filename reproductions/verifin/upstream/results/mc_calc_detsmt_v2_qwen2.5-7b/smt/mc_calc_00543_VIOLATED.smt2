(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_expenses_fy2025 Real)
(declare-const general_and_administrative_expense_fy2025 Real)
(declare-const research_and_development_expense_fy2025 Real)
(declare-const restructuring_charges_fy2025 Real)
(declare-const selling_and_marketing_expense_fy2025 Real)

(assert (! (= general_and_administrative_expense_fy2025 3000) :named evidence_general_and_administrative_expense_fy2025))
(assert (! (= research_and_development_expense_fy2025 5993) :named evidence_research_and_development_expense_fy2025))
(assert (! (= restructuring_charges_fy2025 586) :named evidence_restructuring_charges_fy2025))
(assert (! (= selling_and_marketing_expense_fy2025 14345) :named evidence_selling_and_marketing_expense_fy2025))

(assert (! (= computed_operating_expenses_fy2025 (+ selling_and_marketing_expense_fy2025 general_and_administrative_expense_fy2025 research_and_development_expense_fy2025 restructuring_charges_fy2025)) :named formula_operating_expenses_fy2025))

(assert (! (<= (- computed_operating_expenses_fy2025 21729) 21.728999999999999) :named claim_upper))
(assert (! (<= (- 21729 computed_operating_expenses_fy2025) 21.728999999999999) :named claim_lower))

; EDGAR-companyfacts fact bindings (no calculation-linkbase constraints).
(declare-const xbrl_fact_us_gaap_GeneralAndAdministrativeExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RestructuringCharges_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_SellingAndMarketingExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= selling_and_marketing_expense_fy2025 xbrl_fact_us_gaap_SellingAndMarketingExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none) :named xbrl_bind_selling_and_marketing_expense_fy2025_edgar_2026_01_31_0001108524_26_000060))
(assert (! (= xbrl_fact_us_gaap_SellingAndMarketingExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none 14345) :named xbrl_instance_selling_and_marketing_expense_fy2025))
(assert (! (= general_and_administrative_expense_fy2025 xbrl_fact_us_gaap_GeneralAndAdministrativeExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none) :named xbrl_bind_general_and_administrative_expense_fy2025_edgar_2026_01_31_0001108524_26_000060))
(assert (! (= xbrl_fact_us_gaap_GeneralAndAdministrativeExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none 3000) :named xbrl_instance_general_and_administrative_expense_fy2025))
(assert (! (= research_and_development_expense_fy2025 xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none) :named xbrl_bind_research_and_development_expense_fy2025_edgar_2026_01_31_0001108524_26_000060))
(assert (! (= xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2025_02_01_2026_01_31_unit_USD_dims_none 5993) :named xbrl_instance_research_and_development_expense_fy2025))
(assert (! (= restructuring_charges_fy2025 xbrl_fact_us_gaap_RestructuringCharges_duration_2025_02_01_2026_01_31_unit_USD_dims_none) :named xbrl_bind_restructuring_charges_fy2025_edgar_2026_01_31_0001108524_26_000060))
(assert (! (= xbrl_fact_us_gaap_RestructuringCharges_duration_2025_02_01_2026_01_31_unit_USD_dims_none 586) :named xbrl_instance_restructuring_charges_fy2025))

(check-sat)
(get-unsat-core)
(get-model)