(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_gross_profit_fy2025 Real)
(declare-const cost_of_revenue_fy2025 Real)
(declare-const revenue_from_contract_with_customer_excluding_assessed_tax_fy2025 Real)

(assert (! (= cost_of_revenue_fy2025 109818) :named evidence_cost_of_revenue_fy2025))
(assert (! (= revenue_from_contract_with_customer_excluding_assessed_tax_fy2025 164683) :named evidence_revenue_from_contract_with_customer_excluding_assessed_tax_fy2025))

(assert (! (= computed_gross_profit_fy2025 (+ revenue_from_contract_with_customer_excluding_assessed_tax_fy2025 (* (- 1) cost_of_revenue_fy2025))) :named formula_gross_profit_fy2025))

(assert (! (<= (- computed_gross_profit_fy2025 53) 0.5) :named claim_upper))
(assert (! (<= (- 53 computed_gross_profit_fy2025) 0.5) :named claim_lower))

; EDGAR-companyfacts fact bindings (no calculation-linkbase constraints).
(declare-const xbrl_fact_us_gaap_CostOfRevenue_duration_2025_02_03_2026_02_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_03_2026_02_01_unit_USD_dims_none Real)

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= revenue_from_contract_with_customer_excluding_assessed_tax_fy2025 xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_03_2026_02_01_unit_USD_dims_none) :named xbrl_bind_revenue_from_contract_with_customer_excluding_assessed_tax_fy2025_edgar_2026_02_01_0001628280_26_019436))
(assert (! (= xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_03_2026_02_01_unit_USD_dims_none 164683) :named xbrl_instance_revenue_from_contract_with_customer_excluding_assessed_tax_fy2025))
(assert (! (= cost_of_revenue_fy2025 xbrl_fact_us_gaap_CostOfRevenue_duration_2025_02_03_2026_02_01_unit_USD_dims_none) :named xbrl_bind_cost_of_revenue_fy2025_edgar_2026_02_01_0001628280_26_019436))
(assert (! (= xbrl_fact_us_gaap_CostOfRevenue_duration_2025_02_03_2026_02_01_unit_USD_dims_none 109818) :named xbrl_instance_cost_of_revenue_fy2025))

(check-sat)
(get-unsat-core)
(get-model)