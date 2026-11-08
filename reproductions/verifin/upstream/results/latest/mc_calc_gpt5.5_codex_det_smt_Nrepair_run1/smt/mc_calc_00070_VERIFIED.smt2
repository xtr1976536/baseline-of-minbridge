(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_stockholders_equity_fy2025 Real)
(declare-const accumulated_other_comprehensive_income_loss_net_of_tax_fy2025 Real)
(declare-const additional_paid_in_capital_fy2025 Real)
(declare-const common_stock_value_fy2025 Real)
(declare-const preferred_stock_value_fy2025 Real)
(declare-const retained_earnings_accumulated_deficit_fy2025 Real)
(declare-const treasury_stock_common_value_fy2025 Real)

(assert (! (= accumulated_other_comprehensive_income_loss_net_of_tax_fy2025 -245) :named evidence_accumulated_other_comprehensive_income_loss_net_of_tax_fy2025))
(assert (! (= additional_paid_in_capital_fy2025 15361) :named evidence_additional_paid_in_capital_fy2025))
(assert (! (= common_stock_value_fy2025 0) :named evidence_common_stock_value_fy2025))
(assert (! (= preferred_stock_value_fy2025 0) :named evidence_preferred_stock_value_fy2025))
(assert (! (= retained_earnings_accumulated_deficit_fy2025 45354) :named evidence_retained_earnings_accumulated_deficit_fy2025))
(assert (! (= treasury_stock_common_value_fy2025 48847) :named evidence_treasury_stock_common_value_fy2025))

(assert (! (= computed_stockholders_equity_fy2025 (+ preferred_stock_value_fy2025 common_stock_value_fy2025 additional_paid_in_capital_fy2025 retained_earnings_accumulated_deficit_fy2025 accumulated_other_comprehensive_income_loss_net_of_tax_fy2025 (* (- 1) treasury_stock_common_value_fy2025))) :named formula_stockholders_equity_fy2025))

(assert (! (<= (- computed_stockholders_equity_fy2025 11623) 11.623000000000001) :named claim_upper))
(assert (! (<= (- 11623 computed_stockholders_equity_fy2025) 11.623000000000001) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2025_11_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_AdditionalPaidInCapital_instant_2025_11_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_CommonStockValue_instant_2025_11_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_PreferredStockValue_instant_2025_11_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2025_11_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_StockholdersEquity_instant_2025_11_28_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2025_11_28_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_StockholdersEquity_instant_2025_11_28_unit_USD_dims_none 11623) :named evidence_xbrl_fact_us_gaap_StockholdersEquity_instant_2025_11_28_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= preferred_stock_value_fy2025 xbrl_fact_us_gaap_PreferredStockValue_instant_2025_11_28_unit_USD_dims_none) :named xbrl_bind_preferred_stock_value_fy2025_edgar_2025_11_28_0000796343_26_000003))
(assert (! (= xbrl_fact_us_gaap_PreferredStockValue_instant_2025_11_28_unit_USD_dims_none 0) :named xbrl_instance_preferred_stock_value_fy2025))
(assert (! (= common_stock_value_fy2025 xbrl_fact_us_gaap_CommonStockValue_instant_2025_11_28_unit_USD_dims_none) :named xbrl_bind_common_stock_value_fy2025_edgar_2025_11_28_0000796343_26_000003))
(assert (! (= xbrl_fact_us_gaap_CommonStockValue_instant_2025_11_28_unit_USD_dims_none 0) :named xbrl_instance_common_stock_value_fy2025))
(assert (! (= additional_paid_in_capital_fy2025 xbrl_fact_us_gaap_AdditionalPaidInCapital_instant_2025_11_28_unit_USD_dims_none) :named xbrl_bind_additional_paid_in_capital_fy2025_edgar_2025_11_28_0000796343_26_000003))
(assert (! (= xbrl_fact_us_gaap_AdditionalPaidInCapital_instant_2025_11_28_unit_USD_dims_none 15361) :named xbrl_instance_additional_paid_in_capital_fy2025))
(assert (! (= retained_earnings_accumulated_deficit_fy2025 xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2025_11_28_unit_USD_dims_none) :named xbrl_bind_retained_earnings_accumulated_deficit_fy2025_edgar_2025_11_28_0000796343_26_000003))
(assert (! (= xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2025_11_28_unit_USD_dims_none 45354) :named xbrl_instance_retained_earnings_accumulated_deficit_fy2025))
(assert (! (= accumulated_other_comprehensive_income_loss_net_of_tax_fy2025 xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2025_11_28_unit_USD_dims_none) :named xbrl_bind_accumulated_other_comprehensive_income_loss_net_of_tax_fy2025_edgar_2025_11_28_0000796343_26_000003))
(assert (! (= xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2025_11_28_unit_USD_dims_none -245) :named xbrl_instance_accumulated_other_comprehensive_income_loss_net_of_tax_fy2025))
(assert (! (= treasury_stock_common_value_fy2025 xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2025_11_28_unit_USD_dims_none) :named xbrl_bind_treasury_stock_common_value_fy2025_edgar_2025_11_28_0000796343_26_000003))
(assert (! (= xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2025_11_28_unit_USD_dims_none 48847) :named xbrl_instance_treasury_stock_common_value_fy2025))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_StockholdersEquity_instant_2025_11_28_unit_USD_dims_none (+ xbrl_fact_us_gaap_PreferredStockValue_instant_2025_11_28_unit_USD_dims_none xbrl_fact_us_gaap_CommonStockValue_instant_2025_11_28_unit_USD_dims_none xbrl_fact_us_gaap_AdditionalPaidInCapital_instant_2025_11_28_unit_USD_dims_none xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2025_11_28_unit_USD_dims_none xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2025_11_28_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2025_11_28_unit_USD_dims_none))) 3.5) :named xbrl_calc_3_857209937_StockholdersEquity_c_4_upper))
(assert (! (>= (- xbrl_fact_us_gaap_StockholdersEquity_instant_2025_11_28_unit_USD_dims_none (+ xbrl_fact_us_gaap_PreferredStockValue_instant_2025_11_28_unit_USD_dims_none xbrl_fact_us_gaap_CommonStockValue_instant_2025_11_28_unit_USD_dims_none xbrl_fact_us_gaap_AdditionalPaidInCapital_instant_2025_11_28_unit_USD_dims_none xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2025_11_28_unit_USD_dims_none xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2025_11_28_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_TreasuryStockCommonValue_instant_2025_11_28_unit_USD_dims_none))) (- 3.5)) :named xbrl_calc_3_857209937_StockholdersEquity_c_4_lower))

(check-sat)
(get-unsat-core)
(get-model)