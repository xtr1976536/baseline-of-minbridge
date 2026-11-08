(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_liabilities_noncurrent_fy2022 Real)
(declare-const accrued_income_taxes_noncurrent_fy2022 Real)
(declare-const deferred_income_tax_liabilities_net_fy2022 Real)
(declare-const long_term_notes_and_loans_fy2022 Real)
(declare-const other_liabilities_noncurrent_fy2022 Real)

(assert (! (= accrued_income_taxes_noncurrent_fy2022 12210) :named evidence_accrued_income_taxes_noncurrent_fy2022))
(assert (! (= deferred_income_tax_liabilities_net_fy2022 6031) :named evidence_deferred_income_tax_liabilities_net_fy2022))
(assert (! (= long_term_notes_and_loans_fy2022 72110) :named evidence_long_term_notes_and_loans_fy2022))
(assert (! (= other_liabilities_noncurrent_fy2022 5203) :named evidence_other_liabilities_noncurrent_fy2022))

(assert (! (= computed_liabilities_noncurrent_fy2022 (+ long_term_notes_and_loans_fy2022 accrued_income_taxes_noncurrent_fy2022 deferred_income_tax_liabilities_net_fy2022 other_liabilities_noncurrent_fy2022)) :named formula_liabilities_noncurrent_fy2022))

(assert (! (<= (- computed_liabilities_noncurrent_fy2022 95554) 95.554000000000002) :named claim_upper))
(assert (! (<= (- 95554 computed_liabilities_noncurrent_fy2022) 95.554000000000002) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccruedIncomeTaxesNoncurrent_instant_2022_05_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_DeferredIncomeTaxAssetsNet_instant_2022_05_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_DeferredIncomeTaxLiabilitiesNet_instant_2022_05_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_DeferredTaxAssetsLiabilitiesNet_instant_2022_05_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LiabilitiesNoncurrent_instant_2022_05_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_LongTermNotesAndLoans_instant_2022_05_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OtherLiabilitiesNoncurrent_instant_2022_05_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_DeferredIncomeTaxAssetsNet_instant_2022_05_31_unit_USD_dims_none 12782) :named evidence_xbrl_fact_us_gaap_DeferredIncomeTaxAssetsNet_instant_2022_05_31_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_DeferredTaxAssetsLiabilitiesNet_instant_2022_05_31_unit_USD_dims_none 6751) :named evidence_xbrl_fact_us_gaap_DeferredTaxAssetsLiabilitiesNet_instant_2022_05_31_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_LiabilitiesNoncurrent_instant_2022_05_31_unit_USD_dims_none 95554) :named evidence_xbrl_fact_us_gaap_LiabilitiesNoncurrent_instant_2022_05_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= long_term_notes_and_loans_fy2022 xbrl_fact_us_gaap_LongTermNotesAndLoans_instant_2022_05_31_unit_USD_dims_none) :named xbrl_bind_long_term_notes_and_loans_fy2022_edgar_2022_05_31_0001564590_22_023675))
(assert (! (= xbrl_fact_us_gaap_LongTermNotesAndLoans_instant_2022_05_31_unit_USD_dims_none 72110) :named xbrl_instance_long_term_notes_and_loans_fy2022))
(assert (! (= accrued_income_taxes_noncurrent_fy2022 xbrl_fact_us_gaap_AccruedIncomeTaxesNoncurrent_instant_2022_05_31_unit_USD_dims_none) :named xbrl_bind_accrued_income_taxes_noncurrent_fy2022_edgar_2022_05_31_0001564590_22_023675))
(assert (! (= xbrl_fact_us_gaap_AccruedIncomeTaxesNoncurrent_instant_2022_05_31_unit_USD_dims_none 12210) :named xbrl_instance_accrued_income_taxes_noncurrent_fy2022))
(assert (! (= deferred_income_tax_liabilities_net_fy2022 xbrl_fact_us_gaap_DeferredIncomeTaxLiabilitiesNet_instant_2022_05_31_unit_USD_dims_none) :named xbrl_bind_deferred_income_tax_liabilities_net_fy2022_edgar_2022_05_31_0001564590_22_023675))
(assert (! (= xbrl_fact_us_gaap_DeferredIncomeTaxLiabilitiesNet_instant_2022_05_31_unit_USD_dims_none 6031) :named xbrl_instance_deferred_income_tax_liabilities_net_fy2022))
(assert (! (= other_liabilities_noncurrent_fy2022 xbrl_fact_us_gaap_OtherLiabilitiesNoncurrent_instant_2022_05_31_unit_USD_dims_none) :named xbrl_bind_other_liabilities_noncurrent_fy2022_edgar_2022_05_31_0001564590_22_023675))
(assert (! (= xbrl_fact_us_gaap_OtherLiabilitiesNoncurrent_instant_2022_05_31_unit_USD_dims_none 5203) :named xbrl_instance_other_liabilities_noncurrent_fy2022))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_LiabilitiesNoncurrent_instant_2022_05_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_LongTermNotesAndLoans_instant_2022_05_31_unit_USD_dims_none xbrl_fact_us_gaap_AccruedIncomeTaxesNoncurrent_instant_2022_05_31_unit_USD_dims_none xbrl_fact_us_gaap_DeferredIncomeTaxLiabilitiesNet_instant_2022_05_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherLiabilitiesNoncurrent_instant_2022_05_31_unit_USD_dims_none)) 2.5) :named xbrl_calc_3_472616215_LiabilitiesNoncurrent_C_0001341439_20220531_upper))
(assert (! (>= (- xbrl_fact_us_gaap_LiabilitiesNoncurrent_instant_2022_05_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_LongTermNotesAndLoans_instant_2022_05_31_unit_USD_dims_none xbrl_fact_us_gaap_AccruedIncomeTaxesNoncurrent_instant_2022_05_31_unit_USD_dims_none xbrl_fact_us_gaap_DeferredIncomeTaxLiabilitiesNet_instant_2022_05_31_unit_USD_dims_none xbrl_fact_us_gaap_OtherLiabilitiesNoncurrent_instant_2022_05_31_unit_USD_dims_none)) (- 2.5)) :named xbrl_calc_3_472616215_LiabilitiesNoncurrent_C_0001341439_20220531_lower))
(assert (! (<= (- xbrl_fact_us_gaap_DeferredTaxAssetsLiabilitiesNet_instant_2022_05_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_DeferredIncomeTaxAssetsNet_instant_2022_05_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_DeferredIncomeTaxLiabilitiesNet_instant_2022_05_31_unit_USD_dims_none))) 1.5) :named xbrl_calc_48_235402361_DeferredTaxAssetsLiabilitiesNet_C_0001341439_20220531_upper))
(assert (! (>= (- xbrl_fact_us_gaap_DeferredTaxAssetsLiabilitiesNet_instant_2022_05_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_DeferredIncomeTaxAssetsNet_instant_2022_05_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_DeferredIncomeTaxLiabilitiesNet_instant_2022_05_31_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_48_235402361_DeferredTaxAssetsLiabilitiesNet_C_0001341439_20220531_lower))

(check-sat)
(get-unsat-core)
(get-model)