(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_liabilities_fy2025 Real)
(declare-const deferred_income_tax_liabilities_net_fy2025 Real)
(declare-const liabilities_current_fy2025 Real)
(declare-const long_term_debt_and_capital_lease_obligations_fy2025 Real)
(declare-const operating_lease_liability_noncurrent_fy2025 Real)
(declare-const other_liabilities_noncurrent_fy2025 Real)

(assert (! (= deferred_income_tax_liabilities_net_fy2025 2845) :named evidence_deferred_income_tax_liabilities_net_fy2025))
(assert (! (= liabilities_current_fy2025 32424) :named evidence_liabilities_current_fy2025))
(assert (! (= long_term_debt_and_capital_lease_obligations_fy2025 46341) :named evidence_long_term_debt_and_capital_lease_obligations_fy2025))
(assert (! (= operating_lease_liability_noncurrent_fy2025 8160) :named evidence_operating_lease_liability_noncurrent_fy2025))
(assert (! (= other_liabilities_noncurrent_fy2025 2512) :named evidence_other_liabilities_noncurrent_fy2025))

(assert (! (= computed_liabilities_fy2025 (+ liabilities_current_fy2025 long_term_debt_and_capital_lease_obligations_fy2025 other_liabilities_noncurrent_fy2025 operating_lease_liability_noncurrent_fy2025 deferred_income_tax_liabilities_net_fy2025)) :named formula_liabilities_fy2025))

(assert (! (<= (- computed_liabilities_fy2025 89479) 89.478999999999999) :named claim_upper))
(assert (! (<= (- 89479 computed_liabilities_fy2025) 89.478999999999999) :named claim_lower))

; EDGAR-companyfacts fact bindings (no calculation-linkbase constraints).
(declare-const xbrl_fact_us_gaap_DeferredIncomeTaxLiabilitiesNet_instant_2026_02_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2026_02_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LongTermDebtAndCapitalLeaseObligations_instant_2026_02_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingLeaseLiabilityNoncurrent_instant_2026_02_01_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherLiabilitiesNoncurrent_instant_2026_02_01_unit_USD_dims_none Real)

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= liabilities_current_fy2025 xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2026_02_01_unit_USD_dims_none) :named xbrl_bind_liabilities_current_fy2025_edgar_2026_02_01_0001628280_26_019436))
(assert (! (= xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2026_02_01_unit_USD_dims_none 32424) :named xbrl_instance_liabilities_current_fy2025))
(assert (! (= long_term_debt_and_capital_lease_obligations_fy2025 xbrl_fact_us_gaap_LongTermDebtAndCapitalLeaseObligations_instant_2026_02_01_unit_USD_dims_none) :named xbrl_bind_long_term_debt_and_capital_lease_obligations_fy2025_edgar_2026_02_01_0001628280_26_019436))
(assert (! (= xbrl_fact_us_gaap_LongTermDebtAndCapitalLeaseObligations_instant_2026_02_01_unit_USD_dims_none 46341) :named xbrl_instance_long_term_debt_and_capital_lease_obligations_fy2025))
(assert (! (= other_liabilities_noncurrent_fy2025 xbrl_fact_us_gaap_OtherLiabilitiesNoncurrent_instant_2026_02_01_unit_USD_dims_none) :named xbrl_bind_other_liabilities_noncurrent_fy2025_edgar_2026_02_01_0001628280_26_019436))
(assert (! (= xbrl_fact_us_gaap_OtherLiabilitiesNoncurrent_instant_2026_02_01_unit_USD_dims_none 2512) :named xbrl_instance_other_liabilities_noncurrent_fy2025))
(assert (! (= operating_lease_liability_noncurrent_fy2025 xbrl_fact_us_gaap_OperatingLeaseLiabilityNoncurrent_instant_2026_02_01_unit_USD_dims_none) :named xbrl_bind_operating_lease_liability_noncurrent_fy2025_edgar_2026_02_01_0001628280_26_019436))
(assert (! (= xbrl_fact_us_gaap_OperatingLeaseLiabilityNoncurrent_instant_2026_02_01_unit_USD_dims_none 8160) :named xbrl_instance_operating_lease_liability_noncurrent_fy2025))
(assert (! (= deferred_income_tax_liabilities_net_fy2025 xbrl_fact_us_gaap_DeferredIncomeTaxLiabilitiesNet_instant_2026_02_01_unit_USD_dims_none) :named xbrl_bind_deferred_income_tax_liabilities_net_fy2025_edgar_2026_02_01_0001628280_26_019436))
(assert (! (= xbrl_fact_us_gaap_DeferredIncomeTaxLiabilitiesNet_instant_2026_02_01_unit_USD_dims_none 2845) :named xbrl_instance_deferred_income_tax_liabilities_net_fy2025))

(check-sat)
(get-unsat-core)
(get-model)