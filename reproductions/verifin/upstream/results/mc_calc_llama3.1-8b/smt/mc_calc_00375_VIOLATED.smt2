(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_stockholders_equity_fy2024 Real)
(declare-const accumulated_other_comprehensive_income_loss_net_of_tax_fy2024 Real)
(declare-const common_stocks_including_additional_paid_in_capital_fy2024 Real)
(declare-const preferred_stock_value_fy2024 Real)
(declare-const retained_earnings_accumulated_deficit_fy2024 Real)

(assert (! (= accumulated_other_comprehensive_income_loss_net_of_tax_fy2024 -711.0) :named evidence_accumulated_other_comprehensive_income_loss_net_of_tax_fy2024))
(assert (! (= common_stocks_including_additional_paid_in_capital_fy2024 50949.0) :named evidence_common_stocks_including_additional_paid_in_capital_fy2024))
(assert (! (= preferred_stock_value_fy2024 0.0) :named evidence_preferred_stock_value_fy2024))
(assert (! (= retained_earnings_accumulated_deficit_fy2024 49032.0) :named evidence_retained_earnings_accumulated_deficit_fy2024))

(assert (! (= computed_stockholders_equity_fy2024 (+ preferred_stock_value_fy2024 common_stocks_including_additional_paid_in_capital_fy2024 accumulated_other_comprehensive_income_loss_net_of_tax_fy2024 retained_earnings_accumulated_deficit_fy2024)) :named formula_stockholders_equity_fy2024))

(assert (! (or (> preferred_stock_value_fy2024 0) (< preferred_stock_value_fy2024 0)) :named denom_nonzero))
(assert (! (or (> common_stocks_including_additional_paid_in_capital_fy2024 0) (< common_stocks_including_additional_paid_in_capital_fy2024 0)) :named denom_nonzero1))
(assert (! (or (> accumulated_other_comprehensive_income_loss_net_of_tax_fy2024 0) (< accumulated_other_comprehensive_income_loss_net_of_tax_fy2024 0)) :named denom_nonzero2))
(assert (! (or (> retained_earnings_accumulated_deficit_fy2024 0) (< retained_earnings_accumulated_deficit_fy2024 0)) :named denom_nonzero3))

(assert (! (<= (- computed_stockholders_equity_fy2024 105032.0) 1050.32) :named claim_upper))
(assert (! (<= (- 105032.0 computed_stockholders_equity_fy2024) 1050.32) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2024_12_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_CommonStocksIncludingAdditionalPaidInCapital_instant_2024_12_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_PreferredStockValue_instant_2024_12_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2024_12_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_StockholdersEquity_instant_2024_12_28_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_StockholdersEquity_instant_2024_12_28_unit_USD_dims_none 99270) :named evidence_xbrl_fact_us_gaap_StockholdersEquity_instant_2024_12_28_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= preferred_stock_value_fy2024 xbrl_fact_us_gaap_PreferredStockValue_instant_2024_12_28_unit_USD_dims_none) :named xbrl_bind_preferred_stock_value_fy2024_edgar_2024_12_28_0000050863_25_000009))
(assert (! (= xbrl_fact_us_gaap_PreferredStockValue_instant_2024_12_28_unit_USD_dims_none 0) :named xbrl_instance_preferred_stock_value_fy2024))
(assert (! (= common_stocks_including_additional_paid_in_capital_fy2024 xbrl_fact_us_gaap_CommonStocksIncludingAdditionalPaidInCapital_instant_2024_12_28_unit_USD_dims_none) :named xbrl_bind_common_stocks_including_additional_paid_in_capital_fy2024_edgar_2024_12_28_0000050863_25_000009))
(assert (! (= xbrl_fact_us_gaap_CommonStocksIncludingAdditionalPaidInCapital_instant_2024_12_28_unit_USD_dims_none 50949) :named xbrl_instance_common_stocks_including_additional_paid_in_capital_fy2024))
(assert (! (= accumulated_other_comprehensive_income_loss_net_of_tax_fy2024 xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2024_12_28_unit_USD_dims_none) :named xbrl_bind_accumulated_other_comprehensive_income_loss_net_of_tax_fy2024_edgar_2024_12_28_0000050863_25_000009))
(assert (! (= xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2024_12_28_unit_USD_dims_none -711) :named xbrl_instance_accumulated_other_comprehensive_income_loss_net_of_tax_fy2024))
(assert (! (= retained_earnings_accumulated_deficit_fy2024 xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2024_12_28_unit_USD_dims_none) :named xbrl_bind_retained_earnings_accumulated_deficit_fy2024_edgar_2024_12_28_0000050863_25_000009))
(assert (! (= xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2024_12_28_unit_USD_dims_none 49032) :named xbrl_instance_retained_earnings_accumulated_deficit_fy2024))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_StockholdersEquity_instant_2024_12_28_unit_USD_dims_none (+ xbrl_fact_us_gaap_PreferredStockValue_instant_2024_12_28_unit_USD_dims_none xbrl_fact_us_gaap_CommonStocksIncludingAdditionalPaidInCapital_instant_2024_12_28_unit_USD_dims_none xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2024_12_28_unit_USD_dims_none xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2024_12_28_unit_USD_dims_none)) 2.5) :named xbrl_calc_12_779910405_StockholdersEquity_c_7_upper))
(assert (! (>= (- xbrl_fact_us_gaap_StockholdersEquity_instant_2024_12_28_unit_USD_dims_none (+ xbrl_fact_us_gaap_PreferredStockValue_instant_2024_12_28_unit_USD_dims_none xbrl_fact_us_gaap_CommonStocksIncludingAdditionalPaidInCapital_instant_2024_12_28_unit_USD_dims_none xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2024_12_28_unit_USD_dims_none xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2024_12_28_unit_USD_dims_none)) (- 2.5)) :named xbrl_calc_12_779910405_StockholdersEquity_c_7_lower))

(check-sat)
(get-unsat-core)
(get-model)