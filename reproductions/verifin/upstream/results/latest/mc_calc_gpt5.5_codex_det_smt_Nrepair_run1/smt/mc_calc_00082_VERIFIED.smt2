(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_stockholders_equity_fy2025 Real)
(declare-const accumulated_other_comprehensive_income_loss_net_of_tax_fy2025 Real)
(declare-const common_stocks_including_additional_paid_in_capital_fy2025 Real)
(declare-const retained_earnings_accumulated_deficit_fy2025 Real)
(declare-const treasury_stock_common_value_fy2025 Real)

(assert (! (= accumulated_other_comprehensive_income_loss_net_of_tax_fy2025 -15713) :named evidence_accumulated_other_comprehensive_income_loss_net_of_tax_fy2025))
(assert (! (= common_stocks_including_additional_paid_in_capital_fy2025 63318) :named evidence_common_stocks_including_additional_paid_in_capital_fy2025))
(assert (! (= retained_earnings_accumulated_deficit_fy2025 155648) :named evidence_retained_earnings_accumulated_deficit_fy2025))
(assert (! (= treasury_stock_common_value_fy2025 170605) :named evidence_treasury_stock_common_value_fy2025))

(assert (! (= computed_stockholders_equity_fy2025 (+ common_stocks_including_additional_paid_in_capital_fy2025 retained_earnings_accumulated_deficit_fy2025 (* (- 1) treasury_stock_common_value_fy2025) accumulated_other_comprehensive_income_loss_net_of_tax_fy2025)) :named formula_stockholders_equity_fy2025))

(assert (! (<= (- computed_stockholders_equity_fy2025 32648) 32.648000000000003) :named claim_upper))
(assert (! (<= (- 32648 computed_stockholders_equity_fy2025) 32.648000000000003) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_CommonStocksIncludingAdditionalPaidInCapital_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_StockholdersEquity_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2025_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_StockholdersEquity_instant_2025_12_31_unit_USD_dims_none 32648) :named evidence_xbrl_fact_us_gaap_StockholdersEquity_instant_2025_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= common_stocks_including_additional_paid_in_capital_fy2025 xbrl_fact_us_gaap_CommonStocksIncludingAdditionalPaidInCapital_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_common_stocks_including_additional_paid_in_capital_fy2025_edgar_2025_12_31_0000051143_26_000010))
(assert (! (= xbrl_fact_us_gaap_CommonStocksIncludingAdditionalPaidInCapital_instant_2025_12_31_unit_USD_dims_none 63318) :named xbrl_instance_common_stocks_including_additional_paid_in_capital_fy2025))
(assert (! (= retained_earnings_accumulated_deficit_fy2025 xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_retained_earnings_accumulated_deficit_fy2025_edgar_2025_12_31_0000051143_26_000010))
(assert (! (= xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2025_12_31_unit_USD_dims_none 155648) :named xbrl_instance_retained_earnings_accumulated_deficit_fy2025))
(assert (! (= treasury_stock_common_value_fy2025 xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_treasury_stock_common_value_fy2025_edgar_2025_12_31_0000051143_26_000010))
(assert (! (= xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2025_12_31_unit_USD_dims_none 170605) :named xbrl_instance_treasury_stock_common_value_fy2025))
(assert (! (= accumulated_other_comprehensive_income_loss_net_of_tax_fy2025 xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_accumulated_other_comprehensive_income_loss_net_of_tax_fy2025_edgar_2025_12_31_0000051143_26_000010))
(assert (! (= xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2025_12_31_unit_USD_dims_none -15713) :named xbrl_instance_accumulated_other_comprehensive_income_loss_net_of_tax_fy2025))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_StockholdersEquity_instant_2025_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_CommonStocksIncludingAdditionalPaidInCapital_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2025_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2025_12_31_unit_USD_dims_none) xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2025_12_31_unit_USD_dims_none)) 2.5) :named xbrl_calc_16_960031579_StockholdersEquity_c_58_upper))
(assert (! (>= (- xbrl_fact_us_gaap_StockholdersEquity_instant_2025_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_CommonStocksIncludingAdditionalPaidInCapital_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2025_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2025_12_31_unit_USD_dims_none) xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2025_12_31_unit_USD_dims_none)) (- 2.5)) :named xbrl_calc_16_960031579_StockholdersEquity_c_58_lower))

(check-sat)
(get-unsat-core)
(get-model)