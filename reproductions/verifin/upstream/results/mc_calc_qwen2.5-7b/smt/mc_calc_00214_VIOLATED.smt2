(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_income_loss_fy2026 Real)
(declare-const gross_profit_fy2026 Real)
(declare-const operating_expenses_fy2026 Real)

(assert (! (= gross_profit_fy2026 54865.0) :named evidence_gross_profit_fy2026))
(assert (! (= operating_expenses_fy2026 33975.0) :named evidence_operating_expenses_fy2026))

(assert (! (= computed_operating_income_loss_fy2026 (+ gross_profit_fy2026 (- operating_expenses_fy2026))) :named formula_operating_income_loss_fy2026))

(assert (! (or (> operating_expenses_fy2026 0) (< operating_expenses_fy2026 0)) :named denom_nonzero))

(assert (! (<= (- computed_operating_income_loss_fy2026 -3311.0) 33.11) :named claim_upper))
(assert (! (<= (- -3311.0 computed_operating_income_loss_fy2026) 33.11) :named claim_lower))

; XBRL calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostOfRevenue_duration_2025_02_03_2026_02_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_DepreciationAndAmortization_duration_2025_02_03_2026_02_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_GrossProfit_duration_2025_02_03_2026_02_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingExpenses_duration_2025_02_03_2026_02_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_02_03_2026_02_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_03_2026_02_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_02_03_2026_02_01_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_CostOfRevenue_duration_2025_02_03_2026_02_01_unit_USD_dims_none 109818) :named evidence_xbrl_fact_us_gaap_CostOfRevenue_duration_2025_02_03_2026_02_01_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_DepreciationAndAmortization_duration_2025_02_03_2026_02_01_unit_USD_dims_none 3273) :named evidence_xbrl_fact_us_gaap_DepreciationAndAmortization_duration_2025_02_03_2026_02_01_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_02_03_2026_02_01_unit_USD_dims_none 20890) :named evidence_xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_02_03_2026_02_01_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_03_2026_02_01_unit_USD_dims_none 164683) :named evidence_xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_03_2026_02_01_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_02_03_2026_02_01_unit_USD_dims_none 30702) :named evidence_xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_02_03_2026_02_01_unit_USD_dims_none))

; IR-to-XBRL bindings and independent instance-value witnesses.
(assert (! (= gross_profit_fy2026 xbrl_fact_us_gaap_GrossProfit_duration_2025_02_03_2026_02_01_unit_USD_dims_none) :named xbrl_bind_gross_profit_fy2026_c_1))
(assert (! (= xbrl_fact_us_gaap_GrossProfit_duration_2025_02_03_2026_02_01_unit_USD_dims_none 54865) :named xbrl_instance_gross_profit_fy2026))
(assert (! (= operating_expenses_fy2026 xbrl_fact_us_gaap_OperatingExpenses_duration_2025_02_03_2026_02_01_unit_USD_dims_none) :named xbrl_bind_operating_expenses_fy2026_c_1))
(assert (! (= xbrl_fact_us_gaap_OperatingExpenses_duration_2025_02_03_2026_02_01_unit_USD_dims_none 33975) :named xbrl_instance_operating_expenses_fy2026))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_OperatingExpenses_duration_2025_02_03_2026_02_01_unit_USD_dims_none (+ xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_02_03_2026_02_01_unit_USD_dims_none xbrl_fact_us_gaap_DepreciationAndAmortization_duration_2025_02_03_2026_02_01_unit_USD_dims_none)) 1.5) :named xbrl_calc_8_939849317_OperatingExpenses_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_OperatingExpenses_duration_2025_02_03_2026_02_01_unit_USD_dims_none (+ xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_02_03_2026_02_01_unit_USD_dims_none xbrl_fact_us_gaap_DepreciationAndAmortization_duration_2025_02_03_2026_02_01_unit_USD_dims_none)) (- 1.5)) :named xbrl_calc_8_939849317_OperatingExpenses_c_1_lower))
(assert (! (<= (- xbrl_fact_us_gaap_GrossProfit_duration_2025_02_03_2026_02_01_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_03_2026_02_01_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfRevenue_duration_2025_02_03_2026_02_01_unit_USD_dims_none))) 1.5) :named xbrl_calc_10_939849317_GrossProfit_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_GrossProfit_duration_2025_02_03_2026_02_01_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_03_2026_02_01_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfRevenue_duration_2025_02_03_2026_02_01_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_10_939849317_GrossProfit_c_1_lower))
(assert (! (<= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_02_03_2026_02_01_unit_USD_dims_none (+ xbrl_fact_us_gaap_GrossProfit_duration_2025_02_03_2026_02_01_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_OperatingExpenses_duration_2025_02_03_2026_02_01_unit_USD_dims_none))) 1.5) :named xbrl_calc_11_939849317_OperatingIncomeLoss_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_02_03_2026_02_01_unit_USD_dims_none (+ xbrl_fact_us_gaap_GrossProfit_duration_2025_02_03_2026_02_01_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_OperatingExpenses_duration_2025_02_03_2026_02_01_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_11_939849317_OperatingIncomeLoss_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)