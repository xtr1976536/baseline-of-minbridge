(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_income_loss_fy2026 Real)
(declare-const gross_profit_fy2026 Real)
(declare-const operating_expenses_fy2026 Real)

(assert (! (= gross_profit_fy2026 32255) :named evidence_gross_profit_fy2026))
(assert (! (= operating_expenses_fy2026 23924) :named evidence_operating_expenses_fy2026))

(assert (! (= computed_operating_income_loss_fy2026 (+ gross_profit_fy2026 (* (- 1) operating_expenses_fy2026))) :named formula_operating_income_loss_fy2026))

(assert (! (<= (- computed_operating_income_loss_fy2026 -16) 0.5) :named claim_upper))
(assert (! (<= (- -16 computed_operating_income_loss_fy2026) 0.5) :named claim_lower))

; XBRL calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_GrossProfit_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingExpenses_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_01_2026_01_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2025_02_01_2026_01_31_unit_USD_dims_none 9270) :named evidence_xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2025_02_01_2026_01_31_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_OperatingExpenses_duration_2025_02_01_2026_01_31_unit_USD_dims_none 23924) :named evidence_xbrl_fact_us_gaap_OperatingExpenses_duration_2025_02_01_2026_01_31_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_02_01_2026_01_31_unit_USD_dims_none 8331) :named evidence_xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_02_01_2026_01_31_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_01_2026_01_31_unit_USD_dims_none 41525) :named evidence_xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_01_2026_01_31_unit_USD_dims_none))

; IR-to-XBRL bindings and independent instance-value witnesses.
(assert (! (= gross_profit_fy2026 xbrl_fact_us_gaap_GrossProfit_duration_2025_02_01_2026_01_31_unit_USD_dims_none) :named xbrl_bind_gross_profit_fy2026_c_1))
(assert (! (= xbrl_fact_us_gaap_GrossProfit_duration_2025_02_01_2026_01_31_unit_USD_dims_none 32255) :named xbrl_instance_gross_profit_fy2026))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_GrossProfit_duration_2025_02_01_2026_01_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_01_2026_01_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2025_02_01_2026_01_31_unit_USD_dims_none))) 1.5) :named xbrl_calc_8_204774902_GrossProfit_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_GrossProfit_duration_2025_02_01_2026_01_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_01_2026_01_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2025_02_01_2026_01_31_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_8_204774902_GrossProfit_c_1_lower))
(assert (! (<= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_02_01_2026_01_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_GrossProfit_duration_2025_02_01_2026_01_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_OperatingExpenses_duration_2025_02_01_2026_01_31_unit_USD_dims_none))) 1.5) :named xbrl_calc_9_204774902_OperatingIncomeLoss_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_02_01_2026_01_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_GrossProfit_duration_2025_02_01_2026_01_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_OperatingExpenses_duration_2025_02_01_2026_01_31_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_9_204774902_OperatingIncomeLoss_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)