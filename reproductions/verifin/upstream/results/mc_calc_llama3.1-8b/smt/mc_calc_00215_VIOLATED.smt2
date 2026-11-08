(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_stockholders_equity_fy2024 Real)
(declare-const accumulated_other_comprehensive_income_loss_net_of_tax_fy2024 Real)
(declare-const common_stock_value_fy2024 Real)
(declare-const retained_earnings_accumulated_deficit_fy2024 Real)
(declare-const treasury_stock_common_value_fy2024 Real)

(assert (! (= accumulated_other_comprehensive_income_loss_net_of_tax_fy2024 -14619.0) :named evidence_accumulated_other_comprehensive_income_loss_net_of_tax_fy2024))
(assert (! (= common_stock_value_fy2024 46238.0) :named evidence_common_stock_value_fy2024))
(assert (! (= retained_earnings_accumulated_deficit_fy2024 470903.0) :named evidence_retained_earnings_accumulated_deficit_fy2024))
(assert (! (= treasury_stock_common_value_fy2024 238817.0) :named evidence_treasury_stock_common_value_fy2024))

(assert (! (= computed_stockholders_equity_fy2024 (+ common_stock_value_fy2024 retained_earnings_accumulated_deficit_fy2024 accumulated_other_comprehensive_income_loss_net_of_tax_fy2024 (* -1 treasury_stock_common_value_fy2024))) :named formula_stockholders_equity_fy2024))

(assert (! (or (> treasury_stock_common_value_fy2024 0) (< treasury_stock_common_value_fy2024 0)) :named denom_nonzero))

(assert (! (<= (- computed_stockholders_equity_fy2024 270606.0) 2706.06) :named claim_upper))
(assert (! (<= (- 270606.0 computed_stockholders_equity_fy2024) 2706.06) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_CommonStockValue_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_StockholdersEquity_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2024_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_StockholdersEquity_instant_2024_12_31_unit_USD_dims_none 263705) :named evidence_xbrl_fact_us_gaap_StockholdersEquity_instant_2024_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= common_stock_value_fy2024 xbrl_fact_us_gaap_CommonStockValue_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_common_stock_value_fy2024_edgar_2024_12_31_0000034088_25_000010))
(assert (! (= xbrl_fact_us_gaap_CommonStockValue_instant_2024_12_31_unit_USD_dims_none 46238) :named xbrl_instance_common_stock_value_fy2024))
(assert (! (= retained_earnings_accumulated_deficit_fy2024 xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_retained_earnings_accumulated_deficit_fy2024_edgar_2024_12_31_0000034088_25_000010))
(assert (! (= xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2024_12_31_unit_USD_dims_none 470903) :named xbrl_instance_retained_earnings_accumulated_deficit_fy2024))
(assert (! (= accumulated_other_comprehensive_income_loss_net_of_tax_fy2024 xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_accumulated_other_comprehensive_income_loss_net_of_tax_fy2024_edgar_2024_12_31_0000034088_25_000010))
(assert (! (= xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2024_12_31_unit_USD_dims_none -14619) :named xbrl_instance_accumulated_other_comprehensive_income_loss_net_of_tax_fy2024))
(assert (! (= treasury_stock_common_value_fy2024 xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_treasury_stock_common_value_fy2024_edgar_2024_12_31_0000034088_25_000010))
(assert (! (= xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2024_12_31_unit_USD_dims_none 238817) :named xbrl_instance_treasury_stock_common_value_fy2024))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_StockholdersEquity_instant_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_CommonStockValue_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2024_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2024_12_31_unit_USD_dims_none))) 2.5) :named xbrl_calc_7_725599592_StockholdersEquity_c_20_upper))
(assert (! (>= (- xbrl_fact_us_gaap_StockholdersEquity_instant_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_CommonStockValue_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2024_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2024_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2024_12_31_unit_USD_dims_none))) (- 2.5)) :named xbrl_calc_7_725599592_StockholdersEquity_c_20_lower))

(check-sat)
(get-unsat-core)
(get-model)