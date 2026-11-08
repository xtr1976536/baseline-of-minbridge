(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_stockholders_equity_fy2023 Real)
(declare-const accumulated_other_comprehensive_income_loss_net_of_tax_fy2023 Real)
(declare-const common_stock_value_fy2023 Real)
(declare-const retained_earnings_accumulated_deficit_fy2023 Real)
(declare-const treasury_stock_common_value_fy2023 Real)

(assert (! (= accumulated_other_comprehensive_income_loss_net_of_tax_fy2023 -11989.0) :named evidence_accumulated_other_comprehensive_income_loss_net_of_tax_fy2023))
(assert (! (= common_stock_value_fy2023 17781.0) :named evidence_common_stock_value_fy2023))
(assert (! (= retained_earnings_accumulated_deficit_fy2023 453927.0) :named evidence_retained_earnings_accumulated_deficit_fy2023))
(assert (! (= treasury_stock_common_value_fy2023 254917.0) :named evidence_treasury_stock_common_value_fy2023))

(assert (! (= computed_stockholders_equity_fy2023 (+ common_stock_value_fy2023 retained_earnings_accumulated_deficit_fy2023 accumulated_other_comprehensive_income_loss_net_of_tax_fy2023 (* -1 treasury_stock_common_value_fy2023))) :named formula_stockholders_equity_fy2023))

(assert (! (or (> treasury_stock_common_value_fy2023 0) (< treasury_stock_common_value_fy2023 0)) :named denom_nonzero))
(assert (! (or (> common_stock_value_fy2023 0) (< common_stock_value_fy2023 0)) :named denom_nonzero2))

(assert (! (<= (- computed_stockholders_equity_fy2023 212538.0) 2125.38) :named claim_upper))
(assert (! (<= (- 212538.0 computed_stockholders_equity_fy2023) 2125.38) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2023_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_CommonStockValue_instant_2023_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2023_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_StockholdersEquity_instant_2023_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2023_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_StockholdersEquity_instant_2023_12_31_unit_USD_dims_none 204802) :named evidence_xbrl_fact_us_gaap_StockholdersEquity_instant_2023_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= common_stock_value_fy2023 xbrl_fact_us_gaap_CommonStockValue_instant_2023_12_31_unit_USD_dims_none) :named xbrl_bind_common_stock_value_fy2023_edgar_2023_12_31_0000034088_24_000018))
(assert (! (= xbrl_fact_us_gaap_CommonStockValue_instant_2023_12_31_unit_USD_dims_none 17781) :named xbrl_instance_common_stock_value_fy2023))
(assert (! (= retained_earnings_accumulated_deficit_fy2023 xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2023_12_31_unit_USD_dims_none) :named xbrl_bind_retained_earnings_accumulated_deficit_fy2023_edgar_2023_12_31_0000034088_24_000018))
(assert (! (= xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2023_12_31_unit_USD_dims_none 453927) :named xbrl_instance_retained_earnings_accumulated_deficit_fy2023))
(assert (! (= accumulated_other_comprehensive_income_loss_net_of_tax_fy2023 xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2023_12_31_unit_USD_dims_none) :named xbrl_bind_accumulated_other_comprehensive_income_loss_net_of_tax_fy2023_edgar_2023_12_31_0000034088_24_000018))
(assert (! (= xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2023_12_31_unit_USD_dims_none -11989) :named xbrl_instance_accumulated_other_comprehensive_income_loss_net_of_tax_fy2023))
(assert (! (= treasury_stock_common_value_fy2023 xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2023_12_31_unit_USD_dims_none) :named xbrl_bind_treasury_stock_common_value_fy2023_edgar_2023_12_31_0000034088_24_000018))
(assert (! (= xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2023_12_31_unit_USD_dims_none 254917) :named xbrl_instance_treasury_stock_common_value_fy2023))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_StockholdersEquity_instant_2023_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_CommonStockValue_instant_2023_12_31_unit_USD_dims_none xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2023_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2023_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2023_12_31_unit_USD_dims_none))) 2.5) :named xbrl_calc_8_725599592_StockholdersEquity_c_21_upper))
(assert (! (>= (- xbrl_fact_us_gaap_StockholdersEquity_instant_2023_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_CommonStockValue_instant_2023_12_31_unit_USD_dims_none xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2023_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2023_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2023_12_31_unit_USD_dims_none))) (- 2.5)) :named xbrl_calc_8_725599592_StockholdersEquity_c_21_lower))

(check-sat)
(get-unsat-core)
(get-model)