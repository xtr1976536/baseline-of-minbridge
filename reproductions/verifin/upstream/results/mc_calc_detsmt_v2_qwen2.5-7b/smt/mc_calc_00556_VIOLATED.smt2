(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_income_loss_fy2022 Real)
(declare-const costs_and_expenses_fy2022 Real)
(declare-const revenue_from_contract_with_customer_excluding_assessed_tax_fy2022 Real)

(assert (! (= costs_and_expenses_fy2022 36522) :named evidence_costs_and_expenses_fy2022))
(assert (! (= revenue_from_contract_with_customer_excluding_assessed_tax_fy2022 44915) :named evidence_revenue_from_contract_with_customer_excluding_assessed_tax_fy2022))

(assert (! (= computed_operating_income_loss_fy2022 (+ revenue_from_contract_with_customer_excluding_assessed_tax_fy2022 (* (- 1) costs_and_expenses_fy2022))) :named formula_operating_income_loss_fy2022))

(assert (! (<= (- computed_operating_income_loss_fy2022 -2193) 2.1930000000000001) :named claim_upper))
(assert (! (<= (- -2193 computed_operating_income_loss_fy2022) 2.1930000000000001) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostsAndExpenses_duration_2022_01_01_2022_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2022_01_01_2022_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2022_01_01_2022_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2022_01_01_2022_12_31_unit_USD_dims_none 8393) :named evidence_xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2022_01_01_2022_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= revenue_from_contract_with_customer_excluding_assessed_tax_fy2022 xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2022_01_01_2022_12_31_unit_USD_dims_none) :named xbrl_bind_revenue_from_contract_with_customer_excluding_assessed_tax_fy2022_edgar_2022_12_31_0000097745_23_000008))
(assert (! (= xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2022_01_01_2022_12_31_unit_USD_dims_none 44915) :named xbrl_instance_revenue_from_contract_with_customer_excluding_assessed_tax_fy2022))
(assert (! (= costs_and_expenses_fy2022 xbrl_fact_us_gaap_CostsAndExpenses_duration_2022_01_01_2022_12_31_unit_USD_dims_none) :named xbrl_bind_costs_and_expenses_fy2022_edgar_2022_12_31_0000097745_23_000008))
(assert (! (= xbrl_fact_us_gaap_CostsAndExpenses_duration_2022_01_01_2022_12_31_unit_USD_dims_none 36522) :named xbrl_instance_costs_and_expenses_fy2022))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2022_01_01_2022_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2022_01_01_2022_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostsAndExpenses_duration_2022_01_01_2022_12_31_unit_USD_dims_none))) 1.5) :named xbrl_calc_9_162019931_OperatingIncomeLoss_ifc427a292c554fb6be77326a78328ca5_D20220101_20221231_upper))
(assert (! (>= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2022_01_01_2022_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2022_01_01_2022_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostsAndExpenses_duration_2022_01_01_2022_12_31_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_9_162019931_OperatingIncomeLoss_ifc427a292c554fb6be77326a78328ca5_D20220101_20221231_lower))

(check-sat)
(get-unsat-core)
(get-model)