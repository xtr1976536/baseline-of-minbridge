(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_gross_profit_fy2026 Real)
(declare-const cost_of_revenue_fy2026 Real)
(declare-const revenue_from_contract_with_customer_excluding_assessed_tax_fy2026 Real)

(assert (! (= cost_of_revenue_fy2026 109818.0) :named evidence_cost_of_revenue_fy2026))
(assert (! (= revenue_from_contract_with_customer_excluding_assessed_tax_fy2026 164683.0) :named evidence_revenue_from_contract_with_customer_excluding_assessed_tax_fy2026))

(assert (! (= computed_gross_profit_fy2026 (+ revenue_from_contract_with_customer_excluding_assessed_tax_fy2026 (- cost_of_revenue_fy2026))) :named formula_gross_profit_fy2026))

(assert (! (or (> cost_of_revenue_fy2026 0) (< cost_of_revenue_fy2026 0)) :named denom_nonzero_cost_of_revenue))
(assert (! (or (> revenue_from_contract_with_customer_excluding_assessed_tax_fy2026 0) (< revenue_from_contract_with_customer_excluding_assessed_tax_fy2026 0)) :named denom_nonzero_revenue))

(assert (! (<= (- computed_gross_profit_fy2026 54.0) 0.54) :named claim_upper))
(assert (! (<= (- 54.0 computed_gross_profit_fy2026) 0.54) :named claim_lower))

; XBRL calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostOfRevenue_duration_2025_02_03_2026_02_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_DepreciationAndAmortization_duration_2025_02_03_2026_02_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_GrossProfit_duration_2025_02_03_2026_02_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_02_03_2026_02_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_03_2026_02_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_02_03_2026_02_01_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_DepreciationAndAmortization_duration_2025_02_03_2026_02_01_unit_USD_dims_none 3273) :named evidence_xbrl_fact_us_gaap_DepreciationAndAmortization_duration_2025_02_03_2026_02_01_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_GrossProfit_duration_2025_02_03_2026_02_01_unit_USD_dims_none 54865) :named evidence_xbrl_fact_us_gaap_GrossProfit_duration_2025_02_03_2026_02_01_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_02_03_2026_02_01_unit_USD_dims_none 20890) :named evidence_xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_02_03_2026_02_01_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_03_2026_02_01_unit_USD_dims_none 164683) :named evidence_xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_03_2026_02_01_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_02_03_2026_02_01_unit_USD_dims_none 30702) :named evidence_xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_02_03_2026_02_01_unit_USD_dims_none))

; IR-to-XBRL bindings and independent instance-value witnesses.
(assert (! (= cost_of_revenue_fy2026 xbrl_fact_us_gaap_CostOfRevenue_duration_2025_02_03_2026_02_01_unit_USD_dims_none) :named xbrl_bind_cost_of_revenue_fy2026_c_1))
(assert (! (= xbrl_fact_us_gaap_CostOfRevenue_duration_2025_02_03_2026_02_01_unit_USD_dims_none 109818) :named xbrl_instance_cost_of_revenue_fy2026))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_GrossProfit_duration_2025_02_03_2026_02_01_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_03_2026_02_01_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfRevenue_duration_2025_02_03_2026_02_01_unit_USD_dims_none))) 1.5) :named xbrl_calc_10_939849317_GrossProfit_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_GrossProfit_duration_2025_02_03_2026_02_01_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_03_2026_02_01_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfRevenue_duration_2025_02_03_2026_02_01_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_10_939849317_GrossProfit_c_1_lower))
(assert (! (<= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_02_03_2026_02_01_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_03_2026_02_01_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfRevenue_duration_2025_02_03_2026_02_01_unit_USD_dims_none) (* -1 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_02_03_2026_02_01_unit_USD_dims_none) (* -1 xbrl_fact_us_gaap_DepreciationAndAmortization_duration_2025_02_03_2026_02_01_unit_USD_dims_none))) 2.5) :named xbrl_calc_18_751348759_OperatingIncomeLoss_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2025_02_03_2026_02_01_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2025_02_03_2026_02_01_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfRevenue_duration_2025_02_03_2026_02_01_unit_USD_dims_none) (* -1 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2025_02_03_2026_02_01_unit_USD_dims_none) (* -1 xbrl_fact_us_gaap_DepreciationAndAmortization_duration_2025_02_03_2026_02_01_unit_USD_dims_none))) (- 2.5)) :named xbrl_calc_18_751348759_OperatingIncomeLoss_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)