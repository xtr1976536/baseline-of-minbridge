(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_stockholders_equity_fy2025 Real)
(declare-const accumulated_other_comprehensive_income_loss_net_of_tax_fy2025 Real)
(declare-const additional_paid_in_capital_common_stock_fy2025 Real)
(declare-const common_stock_value_fy2025 Real)
(declare-const preferred_stock_value_fy2025 Real)
(declare-const retained_earnings_accumulated_deficit_fy2025 Real)
(declare-const treasury_stock_common_value_fy2025 Real)

(assert (! (= accumulated_other_comprehensive_income_loss_net_of_tax_fy2025 313) :named evidence_accumulated_other_comprehensive_income_loss_net_of_tax_fy2025))
(assert (! (= additional_paid_in_capital_common_stock_fy2025 68835) :named evidence_additional_paid_in_capital_common_stock_fy2025))
(assert (! (= common_stock_value_fy2025 1) :named evidence_common_stock_value_fy2025))
(assert (! (= preferred_stock_value_fy2025 0) :named evidence_preferred_stock_value_fy2025))
(assert (! (= retained_earnings_accumulated_deficit_fy2025 22221) :named evidence_retained_earnings_accumulated_deficit_fy2025))
(assert (! (= treasury_stock_common_value_fy2025 32228) :named evidence_treasury_stock_common_value_fy2025))

(assert (! (= computed_stockholders_equity_fy2025 (+ common_stock_value_fy2025 additional_paid_in_capital_common_stock_fy2025 accumulated_other_comprehensive_income_loss_net_of_tax_fy2025 (* (- 1) treasury_stock_common_value_fy2025) preferred_stock_value_fy2025 retained_earnings_accumulated_deficit_fy2025)) :named formula_stockholders_equity_fy2025))

(assert (! (<= (- computed_stockholders_equity_fy2025 59646) 59.646000000000001) :named claim_upper))
(assert (! (<= (- 59646 computed_stockholders_equity_fy2025) 59.646000000000001) :named claim_lower))

; EDGAR-companyfacts fact bindings (no calculation-linkbase constraints).
(declare-const xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_AdditionalPaidInCapitalCommonStock_instant_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_CommonStockValue_instant_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_PreferredStockValue_instant_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2026_01_31_unit_USD_dims_none Real)

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= common_stock_value_fy2025 xbrl_fact_us_gaap_CommonStockValue_instant_2026_01_31_unit_USD_dims_none) :named xbrl_bind_common_stock_value_fy2025_edgar_2026_01_31_0001108524_26_000060))
(assert (! (= xbrl_fact_us_gaap_CommonStockValue_instant_2026_01_31_unit_USD_dims_none 1) :named xbrl_instance_common_stock_value_fy2025))
(assert (! (= additional_paid_in_capital_common_stock_fy2025 xbrl_fact_us_gaap_AdditionalPaidInCapitalCommonStock_instant_2026_01_31_unit_USD_dims_none) :named xbrl_bind_additional_paid_in_capital_common_stock_fy2025_edgar_2026_01_31_0001108524_26_000060))
(assert (! (= xbrl_fact_us_gaap_AdditionalPaidInCapitalCommonStock_instant_2026_01_31_unit_USD_dims_none 68835) :named xbrl_instance_additional_paid_in_capital_common_stock_fy2025))
(assert (! (= accumulated_other_comprehensive_income_loss_net_of_tax_fy2025 xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2026_01_31_unit_USD_dims_none) :named xbrl_bind_accumulated_other_comprehensive_income_loss_net_of_tax_fy2025_edgar_2026_01_31_0001108524_26_000060))
(assert (! (= xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2026_01_31_unit_USD_dims_none 313) :named xbrl_instance_accumulated_other_comprehensive_income_loss_net_of_tax_fy2025))
(assert (! (= treasury_stock_common_value_fy2025 xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2026_01_31_unit_USD_dims_none) :named xbrl_bind_treasury_stock_common_value_fy2025_edgar_2026_01_31_0001108524_26_000060))
(assert (! (= xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2026_01_31_unit_USD_dims_none 32228) :named xbrl_instance_treasury_stock_common_value_fy2025))
(assert (! (= preferred_stock_value_fy2025 xbrl_fact_us_gaap_PreferredStockValue_instant_2026_01_31_unit_USD_dims_none) :named xbrl_bind_preferred_stock_value_fy2025_edgar_2026_01_31_0001108524_26_000060))
(assert (! (= xbrl_fact_us_gaap_PreferredStockValue_instant_2026_01_31_unit_USD_dims_none 0) :named xbrl_instance_preferred_stock_value_fy2025))
(assert (! (= retained_earnings_accumulated_deficit_fy2025 xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2026_01_31_unit_USD_dims_none) :named xbrl_bind_retained_earnings_accumulated_deficit_fy2025_edgar_2026_01_31_0001108524_26_000060))
(assert (! (= xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2026_01_31_unit_USD_dims_none 22221) :named xbrl_instance_retained_earnings_accumulated_deficit_fy2025))

(check-sat)
(get-unsat-core)
(get-model)