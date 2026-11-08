(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_income_loss_fy2025 Real)
(declare-const cost_of_goods_and_services_sold_fy2025 Real)
(declare-const revenue_from_contract_with_customer_excluding_assessed_tax_fy2025 Real)
(declare-const selling_general_and_administrative_expense_fy2025 Real)

(assert (! (= cost_of_goods_and_services_sold_fy2025 239886) :named evidence_cost_of_goods_and_services_sold_fy2025))
(assert (! (= revenue_from_contract_with_customer_excluding_assessed_tax_fy2025 275235) :named evidence_revenue_from_contract_with_customer_excluding_assessed_tax_fy2025))
(assert (! (= selling_general_and_administrative_expense_fy2025 24966) :named evidence_selling_general_and_administrative_expense_fy2025))

(assert (! (= computed_operating_income_loss_fy2025 (+ revenue_from_contract_with_customer_excluding_assessed_tax_fy2025 (* (- 1) cost_of_goods_and_services_sold_fy2025) (* (- 1) selling_general_and_administrative_expense_fy2025))) :named formula_operating_income_loss_fy2025))

(assert (! (<= (- computed_operating_income_loss_fy2025 10383) 10.383000000000001) :named claim_upper))
(assert (! (<= (- 10383 computed_operating_income_loss_fy2025) 10.383000000000001) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_09_02_2025_08_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_09_02_2025_08_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2024_09_02_2025_08_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2024_09_02_2025_08_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_09_02_2025_08_31_unit_USD_dims_none 10383) :named evidence_xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_09_02_2025_08_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= revenue_from_contract_with_customer_excluding_assessed_tax_fy2025 xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2024_09_02_2025_08_31_unit_USD_dims_none) :named xbrl_bind_revenue_from_contract_with_customer_excluding_assessed_tax_fy2025_edgar_2025_08_31_0000909832_25_000101))
(assert (! (= xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2024_09_02_2025_08_31_unit_USD_dims_none 275235) :named xbrl_instance_revenue_from_contract_with_customer_excluding_assessed_tax_fy2025))
(assert (! (= cost_of_goods_and_services_sold_fy2025 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_09_02_2025_08_31_unit_USD_dims_none) :named xbrl_bind_cost_of_goods_and_services_sold_fy2025_edgar_2025_08_31_0000909832_25_000101))
(assert (! (= xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_09_02_2025_08_31_unit_USD_dims_none 239886) :named xbrl_instance_cost_of_goods_and_services_sold_fy2025))
(assert (! (= selling_general_and_administrative_expense_fy2025 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2024_09_02_2025_08_31_unit_USD_dims_none) :named xbrl_bind_selling_general_and_administrative_expense_fy2025_edgar_2025_08_31_0000909832_25_000101))
(assert (! (= xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2024_09_02_2025_08_31_unit_USD_dims_none 24966) :named xbrl_instance_selling_general_and_administrative_expense_fy2025))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_09_02_2025_08_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2024_09_02_2025_08_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_09_02_2025_08_31_unit_USD_dims_none) (* -1 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2024_09_02_2025_08_31_unit_USD_dims_none))) 2) :named xbrl_calc_1_628823250_OperatingIncomeLoss_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_09_02_2025_08_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2024_09_02_2025_08_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_09_02_2025_08_31_unit_USD_dims_none) (* -1 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2024_09_02_2025_08_31_unit_USD_dims_none))) (- 2)) :named xbrl_calc_1_628823250_OperatingIncomeLoss_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)