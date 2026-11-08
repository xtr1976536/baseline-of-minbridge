(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_stockholders_equity_fy2022 Real)
(declare-const accumulated_other_comprehensive_income_loss_net_of_tax_fy2022 Real)
(declare-const common_stock_value_fy2022 Real)
(declare-const retained_earnings_accumulated_deficit_fy2022 Real)
(declare-const treasury_stock_common_value_fy2022 Real)

(assert (! (= accumulated_other_comprehensive_income_loss_net_of_tax_fy2022 -13270.0) :named evidence_accumulated_other_comprehensive_income_loss_net_of_tax_fy2022))
(assert (! (= common_stock_value_fy2022 15752.0) :named evidence_common_stock_value_fy2022))
(assert (! (= retained_earnings_accumulated_deficit_fy2022 432860.0) :named evidence_retained_earnings_accumulated_deficit_fy2022))
(assert (! (= treasury_stock_common_value_fy2022 240293.0) :named evidence_treasury_stock_common_value_fy2022))

(assert (! (= computed_stockholders_equity_fy2022 (+ common_stock_value_fy2022 retained_earnings_accumulated_deficit_fy2022 accumulated_other_comprehensive_income_loss_net_of_tax_fy2022 (- treasury_stock_common_value_fy2022))) :named formula_stockholders_equity_fy2022))

(assert (! (or (> accumulated_other_comprehensive_income_loss_net_of_tax_fy2022 0) (< accumulated_other_comprehensive_income_loss_net_of_tax_fy2022 0)) :named denom_nonzero_accumulated_other_comprehensive_income_loss_net_of_tax_fy2022))
(assert (! (or (> common_stock_value_fy2022 0) (< common_stock_value_fy2022 0)) :named denom_nonzero_common_stock_value_fy2022))
(assert (! (or (> retained_earnings_accumulated_deficit_fy2022 0) (< retained_earnings_accumulated_deficit_fy2022 0)) :named denom_nonzero_retained_earnings_accumulated_deficit_fy2022))
(assert (! (or (> treasury_stock_common_value_fy2022 0) (< treasury_stock_common_value_fy2022 0)) :named denom_nonzero_treasury_stock_common_value_fy2022))

(assert (! (<= (- computed_stockholders_equity_fy2022 202473.0) 2024.73) :named claim_upper))
(assert (! (<= (- 202473.0 computed_stockholders_equity_fy2022) 2024.73) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2022_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_CommonStockValue_instant_2022_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2022_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_StockholdersEquity_instant_2022_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2022_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_StockholdersEquity_instant_2022_12_31_unit_USD_dims_none 195049) :named evidence_xbrl_fact_us_gaap_StockholdersEquity_instant_2022_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= retained_earnings_accumulated_deficit_fy2022 xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2022_12_31_unit_USD_dims_none) :named xbrl_bind_retained_earnings_accumulated_deficit_fy2022_edgar_2022_12_31_0000034088_23_000020))
(assert (! (= xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2022_12_31_unit_USD_dims_none 432860) :named xbrl_instance_retained_earnings_accumulated_deficit_fy2022))
(assert (! (= common_stock_value_fy2022 xbrl_fact_us_gaap_CommonStockValue_instant_2022_12_31_unit_USD_dims_none) :named xbrl_bind_common_stock_value_fy2022_edgar_2022_12_31_0000034088_23_000020))
(assert (! (= xbrl_fact_us_gaap_CommonStockValue_instant_2022_12_31_unit_USD_dims_none 15752) :named xbrl_instance_common_stock_value_fy2022))
(assert (! (= accumulated_other_comprehensive_income_loss_net_of_tax_fy2022 xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2022_12_31_unit_USD_dims_none) :named xbrl_bind_accumulated_other_comprehensive_income_loss_net_of_tax_fy2022_edgar_2022_12_31_0000034088_23_000020))
(assert (! (= xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2022_12_31_unit_USD_dims_none -13270) :named xbrl_instance_accumulated_other_comprehensive_income_loss_net_of_tax_fy2022))
(assert (! (= treasury_stock_common_value_fy2022 xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2022_12_31_unit_USD_dims_none) :named xbrl_bind_treasury_stock_common_value_fy2022_edgar_2022_12_31_0000034088_23_000020))
(assert (! (= xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2022_12_31_unit_USD_dims_none 240293) :named xbrl_instance_treasury_stock_common_value_fy2022))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_StockholdersEquity_instant_2022_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_CommonStockValue_instant_2022_12_31_unit_USD_dims_none xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2022_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2022_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2022_12_31_unit_USD_dims_none))) 2.5) :named xbrl_calc_10_725599592_StockholdersEquity_i15692b26353e42aea7351f84210cab69_I20221231_upper))
(assert (! (>= (- xbrl_fact_us_gaap_StockholdersEquity_instant_2022_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_CommonStockValue_instant_2022_12_31_unit_USD_dims_none xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2022_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2022_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2022_12_31_unit_USD_dims_none))) (- 2.5)) :named xbrl_calc_10_725599592_StockholdersEquity_i15692b26353e42aea7351f84210cab69_I20221231_lower))

(check-sat)
(get-unsat-core)
(get-model)