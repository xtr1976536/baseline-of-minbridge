(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_income_loss_fy2025 Real)
(declare-const gross_profit_fy2025 Real)
(declare-const operating_expenses_fy2025 Real)

(assert (! (= gross_profit_fy2025 32255) :named evidence_gross_profit_fy2025))
(assert (! (= operating_expenses_fy2025 23924) :named evidence_operating_expenses_fy2025))

(assert (! (= computed_operating_income_loss_fy2025 (+ gross_profit_fy2025 (* (- 1) operating_expenses_fy2025))) :named formula_operating_income_loss_fy2025))

(assert (! (<= (- computed_operating_income_loss_fy2025 7205) 7.2050000000000001) :named claim_upper))
(assert (! (<= (- 7205 computed_operating_income_loss_fy2025) 7.2050000000000001) :named claim_lower))

; EDGAR-companyfacts fact bindings (no calculation-linkbase constraints).
(declare-const xbrl_fact_us_gaap_GrossProfit_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingExpenses_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= gross_profit_fy2025 xbrl_fact_us_gaap_GrossProfit_duration_2025_02_01_2026_01_31_unit_USD_dims_none) :named xbrl_bind_gross_profit_fy2025_edgar_2026_01_31_0001108524_26_000060))
(assert (! (= xbrl_fact_us_gaap_GrossProfit_duration_2025_02_01_2026_01_31_unit_USD_dims_none 32255) :named xbrl_instance_gross_profit_fy2025))
(assert (! (= operating_expenses_fy2025 xbrl_fact_us_gaap_OperatingExpenses_duration_2025_02_01_2026_01_31_unit_USD_dims_none) :named xbrl_bind_operating_expenses_fy2025_edgar_2026_01_31_0001108524_26_000060))
(assert (! (= xbrl_fact_us_gaap_OperatingExpenses_duration_2025_02_01_2026_01_31_unit_USD_dims_none 23924) :named xbrl_instance_operating_expenses_fy2025))

(check-sat)
(get-unsat-core)
(get-model)