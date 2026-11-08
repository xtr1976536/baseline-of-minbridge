(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_expenses_fy2025 Real)
(declare-const depreciation_and_amortization_fy2025 Real)
(declare-const selling_general_and_administrative_expense_fy2025 Real)

(assert (! (= depreciation_and_amortization_fy2025 3273) :named evidence_depreciation_and_amortization_fy2025))
(assert (! (= selling_general_and_administrative_expense_fy2025 30702) :named evidence_selling_general_and_administrative_expense_fy2025))

(assert (! (= computed_operating_expenses_fy2025 (+ selling_general_and_administrative_expense_fy2025 depreciation_and_amortization_fy2025)) :named formula_operating_expenses_fy2025))

(assert (! (<= (- computed_operating_expenses_fy2025 31782) 31.782) :named claim_upper))
(assert (! (<= (- 31782 computed_operating_expenses_fy2025) 31.782) :named claim_lower))

; EDGAR-companyfacts fact bindings (no calculation-linkbase constraints).
(declare-const xbrl_fact_us_gaap_DepreciationAndAmortization_duration_2025_02_03_2026_02_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_02_03_2026_02_01_unit_USD_dims_none Real)

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= selling_general_and_administrative_expense_fy2025 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_02_03_2026_02_01_unit_USD_dims_none) :named xbrl_bind_selling_general_and_administrative_expense_fy2025_edgar_2026_02_01_0001628280_26_019436))
(assert (! (= xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_02_03_2026_02_01_unit_USD_dims_none 30702) :named xbrl_instance_selling_general_and_administrative_expense_fy2025))
(assert (! (= depreciation_and_amortization_fy2025 xbrl_fact_us_gaap_DepreciationAndAmortization_duration_2025_02_03_2026_02_01_unit_USD_dims_none) :named xbrl_bind_depreciation_and_amortization_fy2025_edgar_2026_02_01_0001628280_26_019436))
(assert (! (= xbrl_fact_us_gaap_DepreciationAndAmortization_duration_2025_02_03_2026_02_01_unit_USD_dims_none 3273) :named xbrl_instance_depreciation_and_amortization_fy2025))

(check-sat)
(get-unsat-core)
(get-model)