(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_liabilities_fy2024 Real)
(declare-const deferred_income_tax_liabilities_net_fy2024 Real)
(declare-const liabilities_current_fy2024 Real)
(declare-const long_term_debt_noncurrent_fy2024 Real)
(declare-const other_liabilities_noncurrent_fy2024 Real)

(assert (! (= deferred_income_tax_liabilities_net_fy2024 3484) :named evidence_deferred_income_tax_liabilities_net_fy2024))
(assert (! (= liabilities_current_fy2024 31536) :named evidence_liabilities_current_fy2024))
(assert (! (= long_term_debt_noncurrent_fy2024 37224) :named evidence_long_term_debt_noncurrent_fy2024))
(assert (! (= other_liabilities_noncurrent_fy2024 9052) :named evidence_other_liabilities_noncurrent_fy2024))

(assert (! (= computed_liabilities_fy2024 (+ liabilities_current_fy2024 long_term_debt_noncurrent_fy2024 other_liabilities_noncurrent_fy2024 deferred_income_tax_liabilities_net_fy2024)) :named formula_liabilities_fy2024))

(assert (! (<= (- computed_liabilities_fy2024 81300) 81.299999999999997) :named claim_upper))
(assert (! (<= (- 81300 computed_liabilities_fy2024) 81.299999999999997) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_DeferredIncomeTaxLiabilitiesNet_instant_2024_12_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2024_12_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_Liabilities_instant_2024_12_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LongTermDebtNoncurrent_instant_2024_12_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherLiabilitiesNoncurrent_instant_2024_12_28_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_Liabilities_instant_2024_12_28_unit_USD_dims_none 81296) :named evidence_xbrl_fact_us_gaap_Liabilities_instant_2024_12_28_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= liabilities_current_fy2024 xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2024_12_28_unit_USD_dims_none) :named xbrl_bind_liabilities_current_fy2024_edgar_2024_12_28_0000077476_25_000007))
(assert (! (= xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2024_12_28_unit_USD_dims_none 31536) :named xbrl_instance_liabilities_current_fy2024))
(assert (! (= long_term_debt_noncurrent_fy2024 xbrl_fact_us_gaap_LongTermDebtNoncurrent_instant_2024_12_28_unit_USD_dims_none) :named xbrl_bind_long_term_debt_noncurrent_fy2024_edgar_2024_12_28_0000077476_25_000007))
(assert (! (= xbrl_fact_us_gaap_LongTermDebtNoncurrent_instant_2024_12_28_unit_USD_dims_none 37224) :named xbrl_instance_long_term_debt_noncurrent_fy2024))
(assert (! (= other_liabilities_noncurrent_fy2024 xbrl_fact_us_gaap_OtherLiabilitiesNoncurrent_instant_2024_12_28_unit_USD_dims_none) :named xbrl_bind_other_liabilities_noncurrent_fy2024_edgar_2024_12_28_0000077476_25_000007))
(assert (! (= xbrl_fact_us_gaap_OtherLiabilitiesNoncurrent_instant_2024_12_28_unit_USD_dims_none 9052) :named xbrl_instance_other_liabilities_noncurrent_fy2024))
(assert (! (= deferred_income_tax_liabilities_net_fy2024 xbrl_fact_us_gaap_DeferredIncomeTaxLiabilitiesNet_instant_2024_12_28_unit_USD_dims_none) :named xbrl_bind_deferred_income_tax_liabilities_net_fy2024_edgar_2024_12_28_0000077476_25_000007))
(assert (! (= xbrl_fact_us_gaap_DeferredIncomeTaxLiabilitiesNet_instant_2024_12_28_unit_USD_dims_none 3484) :named xbrl_instance_deferred_income_tax_liabilities_net_fy2024))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_Liabilities_instant_2024_12_28_unit_USD_dims_none (+ xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2024_12_28_unit_USD_dims_none xbrl_fact_us_gaap_LongTermDebtNoncurrent_instant_2024_12_28_unit_USD_dims_none xbrl_fact_us_gaap_OtherLiabilitiesNoncurrent_instant_2024_12_28_unit_USD_dims_none xbrl_fact_us_gaap_DeferredIncomeTaxLiabilitiesNet_instant_2024_12_28_unit_USD_dims_none)) 2.5) :named xbrl_calc_18_530985866_Liabilities_c_21_upper))
(assert (! (>= (- xbrl_fact_us_gaap_Liabilities_instant_2024_12_28_unit_USD_dims_none (+ xbrl_fact_us_gaap_LiabilitiesCurrent_instant_2024_12_28_unit_USD_dims_none xbrl_fact_us_gaap_LongTermDebtNoncurrent_instant_2024_12_28_unit_USD_dims_none xbrl_fact_us_gaap_OtherLiabilitiesNoncurrent_instant_2024_12_28_unit_USD_dims_none xbrl_fact_us_gaap_DeferredIncomeTaxLiabilitiesNet_instant_2024_12_28_unit_USD_dims_none)) (- 2.5)) :named xbrl_calc_18_530985866_Liabilities_c_21_lower))

(check-sat)
(get-unsat-core)
(get-model)