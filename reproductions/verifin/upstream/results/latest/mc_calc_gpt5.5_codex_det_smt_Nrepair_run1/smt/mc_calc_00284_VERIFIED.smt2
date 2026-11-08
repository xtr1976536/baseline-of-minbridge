(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_stockholders_equity_fy2024 Real)
(declare-const accumulated_other_comprehensive_income_loss_net_of_tax_fy2024 Real)
(declare-const additional_paid_in_capital_fy2024 Real)
(declare-const common_stock_value_fy2024 Real)
(declare-const preferred_stock_value_fy2024 Real)
(declare-const retained_earnings_accumulated_deficit_fy2024 Real)
(declare-const treasury_stock_common_value_fy2024 Real)

(assert (! (= accumulated_other_comprehensive_income_loss_net_of_tax_fy2024 -34) :named evidence_accumulated_other_comprehensive_income_loss_net_of_tax_fy2024))
(assert (! (= additional_paid_in_capital_fy2024 120864) :named evidence_additional_paid_in_capital_fy2024))
(assert (! (= common_stock_value_fy2024 111) :named evidence_common_stock_value_fy2024))
(assert (! (= preferred_stock_value_fy2024 0) :named evidence_preferred_stock_value_fy2024))
(assert (! (= retained_earnings_accumulated_deficit_fy2024 172866) :named evidence_retained_earnings_accumulated_deficit_fy2024))
(assert (! (= treasury_stock_common_value_fy2024 7837) :named evidence_treasury_stock_common_value_fy2024))

(assert (! (= computed_stockholders_equity_fy2024 (+ preferred_stock_value_fy2024 common_stock_value_fy2024 (* (- 1) treasury_stock_common_value_fy2024) additional_paid_in_capital_fy2024 accumulated_other_comprehensive_income_loss_net_of_tax_fy2024 retained_earnings_accumulated_deficit_fy2024)) :named formula_stockholders_equity_fy2024))

(assert (! (<= (- computed_stockholders_equity_fy2024 285970) 285.97000000000003) :named claim_upper))
(assert (! (<= (- 285970 computed_stockholders_equity_fy2024) 285.97000000000003) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_AdditionalPaidInCapital_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_CommonStockValue_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_PreferredStockValue_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_StockholdersEquity_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2024_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_StockholdersEquity_instant_2024_12_31_unit_USD_dims_none 285970) :named evidence_xbrl_fact_us_gaap_StockholdersEquity_instant_2024_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= preferred_stock_value_fy2024 xbrl_fact_us_gaap_PreferredStockValue_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_preferred_stock_value_fy2024_edgar_2024_12_31_0001018724_25_000004))
(assert (! (= xbrl_fact_us_gaap_PreferredStockValue_instant_2024_12_31_unit_USD_dims_none 0) :named xbrl_instance_preferred_stock_value_fy2024))
(assert (! (= common_stock_value_fy2024 xbrl_fact_us_gaap_CommonStockValue_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_common_stock_value_fy2024_edgar_2024_12_31_0001018724_25_000004))
(assert (! (= xbrl_fact_us_gaap_CommonStockValue_instant_2024_12_31_unit_USD_dims_none 111) :named xbrl_instance_common_stock_value_fy2024))
(assert (! (= treasury_stock_common_value_fy2024 xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_treasury_stock_common_value_fy2024_edgar_2024_12_31_0001018724_25_000004))
(assert (! (= xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2024_12_31_unit_USD_dims_none 7837) :named xbrl_instance_treasury_stock_common_value_fy2024))
(assert (! (= additional_paid_in_capital_fy2024 xbrl_fact_us_gaap_AdditionalPaidInCapital_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_additional_paid_in_capital_fy2024_edgar_2024_12_31_0001018724_25_000004))
(assert (! (= xbrl_fact_us_gaap_AdditionalPaidInCapital_instant_2024_12_31_unit_USD_dims_none 120864) :named xbrl_instance_additional_paid_in_capital_fy2024))
(assert (! (= accumulated_other_comprehensive_income_loss_net_of_tax_fy2024 xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_accumulated_other_comprehensive_income_loss_net_of_tax_fy2024_edgar_2024_12_31_0001018724_25_000004))
(assert (! (= xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2024_12_31_unit_USD_dims_none -34) :named xbrl_instance_accumulated_other_comprehensive_income_loss_net_of_tax_fy2024))
(assert (! (= retained_earnings_accumulated_deficit_fy2024 xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_retained_earnings_accumulated_deficit_fy2024_edgar_2024_12_31_0001018724_25_000004))
(assert (! (= xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2024_12_31_unit_USD_dims_none 172866) :named xbrl_instance_retained_earnings_accumulated_deficit_fy2024))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_StockholdersEquity_instant_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_PreferredStockValue_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_CommonStockValue_instant_2024_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2024_12_31_unit_USD_dims_none) xbrl_fact_us_gaap_AdditionalPaidInCapital_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2024_12_31_unit_USD_dims_none)) 3.5) :named xbrl_calc_14_468678268_StockholdersEquity_c_9_upper))
(assert (! (>= (- xbrl_fact_us_gaap_StockholdersEquity_instant_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_PreferredStockValue_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_CommonStockValue_instant_2024_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2024_12_31_unit_USD_dims_none) xbrl_fact_us_gaap_AdditionalPaidInCapital_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2024_12_31_unit_USD_dims_none)) (- 3.5)) :named xbrl_calc_14_468678268_StockholdersEquity_c_9_lower))

(check-sat)
(get-unsat-core)
(get-model)