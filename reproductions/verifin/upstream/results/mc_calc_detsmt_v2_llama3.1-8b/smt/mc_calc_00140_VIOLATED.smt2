(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_income_loss_fy2025 Real)
(declare-const costs_and_expenses_fy2025 Real)
(declare-const revenue_from_contract_with_customer_excluding_assessed_tax_fy2025 Real)

(assert (! (= costs_and_expenses_fy2025 36810) :named evidence_costs_and_expenses_fy2025))
(assert (! (= revenue_from_contract_with_customer_excluding_assessed_tax_fy2025 44556) :named evidence_revenue_from_contract_with_customer_excluding_assessed_tax_fy2025))

(assert (! (= computed_operating_income_loss_fy2025 (+ revenue_from_contract_with_customer_excluding_assessed_tax_fy2025 (* (- 1) costs_and_expenses_fy2025))) :named formula_operating_income_loss_fy2025))

(assert (! (<= (- computed_operating_income_loss_fy2025 -8) 0.5) :named claim_upper))
(assert (! (<= (- -8 computed_operating_income_loss_fy2025) 0.5) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostsAndExpenses_duration_2025_01_01_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_01_01_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_01_01_2025_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_01_01_2025_12_31_unit_USD_dims_none 7746) :named evidence_xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_01_01_2025_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= revenue_from_contract_with_customer_excluding_assessed_tax_fy2025 xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_01_01_2025_12_31_unit_USD_dims_none) :named xbrl_bind_revenue_from_contract_with_customer_excluding_assessed_tax_fy2025_edgar_2025_12_31_0000097745_26_000018))
(assert (! (= xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_01_01_2025_12_31_unit_USD_dims_none 44556) :named xbrl_instance_revenue_from_contract_with_customer_excluding_assessed_tax_fy2025))
(assert (! (= costs_and_expenses_fy2025 xbrl_fact_us_gaap_CostsAndExpenses_duration_2025_01_01_2025_12_31_unit_USD_dims_none) :named xbrl_bind_costs_and_expenses_fy2025_edgar_2025_12_31_0000097745_26_000018))
(assert (! (= xbrl_fact_us_gaap_CostsAndExpenses_duration_2025_01_01_2025_12_31_unit_USD_dims_none 36810) :named xbrl_instance_costs_and_expenses_fy2025))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_01_01_2025_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_01_01_2025_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostsAndExpenses_duration_2025_01_01_2025_12_31_unit_USD_dims_none))) 1.5) :named xbrl_calc_10_188114205_OperatingIncomeLoss_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_01_01_2025_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_01_01_2025_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostsAndExpenses_duration_2025_01_01_2025_12_31_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_10_188114205_OperatingIncomeLoss_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)