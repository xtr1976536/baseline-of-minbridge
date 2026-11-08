(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_stockholders_equity_fy2022 Real)
(declare-const accumulated_other_comprehensive_income_loss_net_of_tax_fy2022 Real)
(declare-const additional_paid_in_capital_common_stock_fy2022 Real)
(declare-const common_stock_held_in_trust_fy2022 Real)
(declare-const common_stock_value_fy2022 Real)
(declare-const preferred_stock_value_fy2022 Real)
(declare-const retained_earnings_accumulated_deficit_fy2022 Real)
(declare-const treasury_stock_value_fy2022 Real)

(assert (! (= accumulated_other_comprehensive_income_loss_net_of_tax_fy2022 -2798) :named evidence_accumulated_other_comprehensive_income_loss_net_of_tax_fy2022))
(assert (! (= additional_paid_in_capital_common_stock_fy2022 18660) :named evidence_additional_paid_in_capital_common_stock_fy2022))
(assert (! (= common_stock_held_in_trust_fy2022 240) :named evidence_common_stock_held_in_trust_fy2022))
(assert (! (= common_stock_value_fy2022 1832) :named evidence_common_stock_value_fy2022))
(assert (! (= preferred_stock_value_fy2022 0) :named evidence_preferred_stock_value_fy2022))
(assert (! (= retained_earnings_accumulated_deficit_fy2022 190024) :named evidence_retained_earnings_accumulated_deficit_fy2022))
(assert (! (= treasury_stock_value_fy2022 48196) :named evidence_treasury_stock_value_fy2022))

(assert (! (= computed_stockholders_equity_fy2022 (+ preferred_stock_value_fy2022 common_stock_value_fy2022 additional_paid_in_capital_common_stock_fy2022 retained_earnings_accumulated_deficit_fy2022 accumulated_other_comprehensive_income_loss_net_of_tax_fy2022 (* (- 1) common_stock_held_in_trust_fy2022) (* (- 1) treasury_stock_value_fy2022))) :named formula_stockholders_equity_fy2022))

(assert (! (<= (- computed_stockholders_equity_fy2022 159282) 159.28200000000001) :named claim_upper))
(assert (! (<= (- 159282 computed_stockholders_equity_fy2022) 159.28200000000001) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2022_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_AdditionalPaidInCapitalCommonStock_instant_2022_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_CommonStockHeldInTrust_instant_2022_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_CommonStockValue_instant_2022_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_PreferredStockValue_instant_2022_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2022_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_StockholdersEquity_instant_2022_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_TreasuryStockValue_instant_2022_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_StockholdersEquity_instant_2022_12_31_unit_USD_dims_none 159282) :named evidence_xbrl_fact_us_gaap_StockholdersEquity_instant_2022_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= preferred_stock_value_fy2022 xbrl_fact_us_gaap_PreferredStockValue_instant_2022_12_31_unit_USD_dims_none) :named xbrl_bind_preferred_stock_value_fy2022_edgar_2022_12_31_0000093410_23_000009))
(assert (! (= xbrl_fact_us_gaap_PreferredStockValue_instant_2022_12_31_unit_USD_dims_none 0) :named xbrl_instance_preferred_stock_value_fy2022))
(assert (! (= common_stock_value_fy2022 xbrl_fact_us_gaap_CommonStockValue_instant_2022_12_31_unit_USD_dims_none) :named xbrl_bind_common_stock_value_fy2022_edgar_2022_12_31_0000093410_23_000009))
(assert (! (= xbrl_fact_us_gaap_CommonStockValue_instant_2022_12_31_unit_USD_dims_none 1832) :named xbrl_instance_common_stock_value_fy2022))
(assert (! (= additional_paid_in_capital_common_stock_fy2022 xbrl_fact_us_gaap_AdditionalPaidInCapitalCommonStock_instant_2022_12_31_unit_USD_dims_none) :named xbrl_bind_additional_paid_in_capital_common_stock_fy2022_edgar_2022_12_31_0000093410_23_000009))
(assert (! (= xbrl_fact_us_gaap_AdditionalPaidInCapitalCommonStock_instant_2022_12_31_unit_USD_dims_none 18660) :named xbrl_instance_additional_paid_in_capital_common_stock_fy2022))
(assert (! (= retained_earnings_accumulated_deficit_fy2022 xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2022_12_31_unit_USD_dims_none) :named xbrl_bind_retained_earnings_accumulated_deficit_fy2022_edgar_2022_12_31_0000093410_23_000009))
(assert (! (= xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2022_12_31_unit_USD_dims_none 190024) :named xbrl_instance_retained_earnings_accumulated_deficit_fy2022))
(assert (! (= accumulated_other_comprehensive_income_loss_net_of_tax_fy2022 xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2022_12_31_unit_USD_dims_none) :named xbrl_bind_accumulated_other_comprehensive_income_loss_net_of_tax_fy2022_edgar_2022_12_31_0000093410_23_000009))
(assert (! (= xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2022_12_31_unit_USD_dims_none -2798) :named xbrl_instance_accumulated_other_comprehensive_income_loss_net_of_tax_fy2022))
(assert (! (= common_stock_held_in_trust_fy2022 xbrl_fact_us_gaap_CommonStockHeldInTrust_instant_2022_12_31_unit_USD_dims_none) :named xbrl_bind_common_stock_held_in_trust_fy2022_edgar_2022_12_31_0000093410_23_000009))
(assert (! (= xbrl_fact_us_gaap_CommonStockHeldInTrust_instant_2022_12_31_unit_USD_dims_none 240) :named xbrl_instance_common_stock_held_in_trust_fy2022))
(assert (! (= treasury_stock_value_fy2022 xbrl_fact_us_gaap_TreasuryStockValue_instant_2022_12_31_unit_USD_dims_none) :named xbrl_bind_treasury_stock_value_fy2022_edgar_2022_12_31_0000093410_23_000009))
(assert (! (= xbrl_fact_us_gaap_TreasuryStockValue_instant_2022_12_31_unit_USD_dims_none 48196) :named xbrl_instance_treasury_stock_value_fy2022))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_StockholdersEquity_instant_2022_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_PreferredStockValue_instant_2022_12_31_unit_USD_dims_none xbrl_fact_us_gaap_CommonStockValue_instant_2022_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AdditionalPaidInCapitalCommonStock_instant_2022_12_31_unit_USD_dims_none xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2022_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2022_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CommonStockHeldInTrust_instant_2022_12_31_unit_USD_dims_none) (* -1 xbrl_fact_us_gaap_TreasuryStockValue_instant_2022_12_31_unit_USD_dims_none))) 4) :named xbrl_calc_13_653354734_StockholdersEquity_iade344a5d8d34d59aa1401c6982340a4_I20221231_upper))
(assert (! (>= (- xbrl_fact_us_gaap_StockholdersEquity_instant_2022_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_PreferredStockValue_instant_2022_12_31_unit_USD_dims_none xbrl_fact_us_gaap_CommonStockValue_instant_2022_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AdditionalPaidInCapitalCommonStock_instant_2022_12_31_unit_USD_dims_none xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2022_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2022_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CommonStockHeldInTrust_instant_2022_12_31_unit_USD_dims_none) (* -1 xbrl_fact_us_gaap_TreasuryStockValue_instant_2022_12_31_unit_USD_dims_none))) (- 4)) :named xbrl_calc_13_653354734_StockholdersEquity_iade344a5d8d34d59aa1401c6982340a4_I20221231_lower))

(check-sat)
(get-unsat-core)
(get-model)