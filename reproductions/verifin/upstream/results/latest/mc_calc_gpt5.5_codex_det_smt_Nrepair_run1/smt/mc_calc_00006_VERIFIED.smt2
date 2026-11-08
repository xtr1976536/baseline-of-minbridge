(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_stockholders_equity_fy2025 Real)
(declare-const accumulated_other_comprehensive_income_loss_net_of_tax_fy2025 Real)
(declare-const additional_paid_in_capital_fy2025 Real)
(declare-const common_stock_value_fy2025 Real)
(declare-const retained_earnings_accumulated_deficit_fy2025 Real)

(assert (! (= accumulated_other_comprehensive_income_loss_net_of_tax_fy2025 271) :named evidence_accumulated_other_comprehensive_income_loss_net_of_tax_fy2025))
(assert (! (= additional_paid_in_capital_fy2025 95793) :named evidence_additional_paid_in_capital_fy2025))
(assert (! (= common_stock_value_fy2025 0) :named evidence_common_stock_value_fy2025))
(assert (! (= retained_earnings_accumulated_deficit_fy2025 121179) :named evidence_retained_earnings_accumulated_deficit_fy2025))

(assert (! (= computed_stockholders_equity_fy2025 (+ common_stock_value_fy2025 additional_paid_in_capital_fy2025 accumulated_other_comprehensive_income_loss_net_of_tax_fy2025 retained_earnings_accumulated_deficit_fy2025)) :named formula_stockholders_equity_fy2025))

(assert (! (<= (- computed_stockholders_equity_fy2025 217243) 217.24299999999999) :named claim_upper))
(assert (! (<= (- 217243 computed_stockholders_equity_fy2025) 217.24299999999999) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_AdditionalPaidInCapital_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_CommonStockValue_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_StockholdersEquity_instant_2025_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_StockholdersEquity_instant_2025_12_31_unit_USD_dims_none 217243) :named evidence_xbrl_fact_us_gaap_StockholdersEquity_instant_2025_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= common_stock_value_fy2025 xbrl_fact_us_gaap_CommonStockValue_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_common_stock_value_fy2025_edgar_2025_12_31_0001628280_26_003942))
(assert (! (= xbrl_fact_us_gaap_CommonStockValue_instant_2025_12_31_unit_USD_dims_none 0) :named xbrl_instance_common_stock_value_fy2025))
(assert (! (= additional_paid_in_capital_fy2025 xbrl_fact_us_gaap_AdditionalPaidInCapital_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_additional_paid_in_capital_fy2025_edgar_2025_12_31_0001628280_26_003942))
(assert (! (= xbrl_fact_us_gaap_AdditionalPaidInCapital_instant_2025_12_31_unit_USD_dims_none 95793) :named xbrl_instance_additional_paid_in_capital_fy2025))
(assert (! (= accumulated_other_comprehensive_income_loss_net_of_tax_fy2025 xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_accumulated_other_comprehensive_income_loss_net_of_tax_fy2025_edgar_2025_12_31_0001628280_26_003942))
(assert (! (= xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2025_12_31_unit_USD_dims_none 271) :named xbrl_instance_accumulated_other_comprehensive_income_loss_net_of_tax_fy2025))
(assert (! (= retained_earnings_accumulated_deficit_fy2025 xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_retained_earnings_accumulated_deficit_fy2025_edgar_2025_12_31_0001628280_26_003942))
(assert (! (= xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2025_12_31_unit_USD_dims_none 121179) :named xbrl_instance_retained_earnings_accumulated_deficit_fy2025))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_StockholdersEquity_instant_2025_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_CommonStockValue_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AdditionalPaidInCapital_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2025_12_31_unit_USD_dims_none)) 2.5) :named xbrl_calc_0_377470884_StockholdersEquity_c_5_upper))
(assert (! (>= (- xbrl_fact_us_gaap_StockholdersEquity_instant_2025_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_CommonStockValue_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AdditionalPaidInCapital_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2025_12_31_unit_USD_dims_none)) (- 2.5)) :named xbrl_calc_0_377470884_StockholdersEquity_c_5_lower))

(check-sat)
(get-unsat-core)
(get-model)