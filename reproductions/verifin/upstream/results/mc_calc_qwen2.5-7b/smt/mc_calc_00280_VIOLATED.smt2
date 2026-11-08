(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_income_loss_fy2024 Real)
(declare-const costs_and_expenses_fy2024 Real)
(declare-const revenue_from_contract_with_customer_excluding_assessed_tax_fy2024 Real)

(assert (! (= costs_and_expenses_fy2024 35542.0) :named evidence_costs_and_expenses_fy2024))
(assert (! (= revenue_from_contract_with_customer_excluding_assessed_tax_fy2024 42879.0) :named evidence_revenue_from_contract_with_customer_excluding_assessed_tax_fy2024))

(assert (! (= computed_operating_income_loss_fy2024 (+ revenue_from_contract_with_customer_excluding_assessed_tax_fy2024 (- costs_and_expenses_fy2024))) :named formula_operating_income_loss_fy2024))

(assert (! (or (> costs_and_expenses_fy2024 0) (< costs_and_expenses_fy2024 0)) :named denom_nonzero))

(assert (! (<= (- computed_operating_income_loss_fy2024 -6657.0) 66.57000000000001) :named claim_upper))
(assert (! (<= (- -6657.0 computed_operating_income_loss_fy2024) 66.57000000000001) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostsAndExpenses_duration_2024_01_01_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_01_01_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2024_01_01_2024_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_01_01_2024_12_31_unit_USD_dims_none 7337) :named evidence_xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_01_01_2024_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= costs_and_expenses_fy2024 xbrl_fact_us_gaap_CostsAndExpenses_duration_2024_01_01_2024_12_31_unit_USD_dims_none) :named xbrl_bind_costs_and_expenses_fy2024_edgar_2024_12_31_0000097745_25_000010))
(assert (! (= xbrl_fact_us_gaap_CostsAndExpenses_duration_2024_01_01_2024_12_31_unit_USD_dims_none 35542) :named xbrl_instance_costs_and_expenses_fy2024))
(assert (! (= revenue_from_contract_with_customer_excluding_assessed_tax_fy2024 xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2024_01_01_2024_12_31_unit_USD_dims_none) :named xbrl_bind_revenue_from_contract_with_customer_excluding_assessed_tax_fy2024_edgar_2024_12_31_0000097745_25_000010))
(assert (! (= xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2024_01_01_2024_12_31_unit_USD_dims_none 42879) :named xbrl_instance_revenue_from_contract_with_customer_excluding_assessed_tax_fy2024))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_01_01_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2024_01_01_2024_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostsAndExpenses_duration_2024_01_01_2024_12_31_unit_USD_dims_none))) 1.5) :named xbrl_calc_6_188114205_OperatingIncomeLoss_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_01_01_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2024_01_01_2024_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostsAndExpenses_duration_2024_01_01_2024_12_31_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_6_188114205_OperatingIncomeLoss_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)