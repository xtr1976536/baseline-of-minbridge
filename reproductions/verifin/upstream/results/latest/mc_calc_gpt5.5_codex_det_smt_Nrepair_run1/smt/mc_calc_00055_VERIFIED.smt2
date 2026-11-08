(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_stockholders_equity_fy2025 Real)
(declare-const accumulated_other_comprehensive_income_loss_net_of_tax_fy2025 Real)
(declare-const additional_paid_in_capital_fy2025 Real)
(declare-const common_stock_value_fy2025 Real)
(declare-const preferred_stock_value_fy2025 Real)
(declare-const retained_earnings_accumulated_deficit_fy2025 Real)
(declare-const treasury_stock_value_fy2025 Real)

(assert (! (= accumulated_other_comprehensive_income_loss_net_of_tax_fy2025 -2414) :named evidence_accumulated_other_comprehensive_income_loss_net_of_tax_fy2025))
(assert (! (= additional_paid_in_capital_fy2025 9641) :named evidence_additional_paid_in_capital_fy2025))
(assert (! (= common_stock_value_fy2025 17) :named evidence_common_stock_value_fy2025))
(assert (! (= preferred_stock_value_fy2025 0) :named evidence_preferred_stock_value_fy2025))
(assert (! (= retained_earnings_accumulated_deficit_fy2025 70282) :named evidence_retained_earnings_accumulated_deficit_fy2025))
(assert (! (= treasury_stock_value_fy2025 79316) :named evidence_treasury_stock_value_fy2025))

(assert (! (= computed_stockholders_equity_fy2025 (+ preferred_stock_value_fy2025 common_stock_value_fy2025 additional_paid_in_capital_fy2025 retained_earnings_accumulated_deficit_fy2025 accumulated_other_comprehensive_income_loss_net_of_tax_fy2025 (* (- 1) treasury_stock_value_fy2025))) :named formula_stockholders_equity_fy2025))

(assert (! (<= (- computed_stockholders_equity_fy2025 -1790) 1.79) :named claim_upper))
(assert (! (<= (- -1790 computed_stockholders_equity_fy2025) 1.79) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_AdditionalPaidInCapital_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_CommonStockValue_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_PreferredStockValue_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_StockholdersEquity_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_TreasuryStockValue_instant_2025_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_StockholdersEquity_instant_2025_12_31_unit_USD_dims_none -1791) :named evidence_xbrl_fact_us_gaap_StockholdersEquity_instant_2025_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= preferred_stock_value_fy2025 xbrl_fact_us_gaap_PreferredStockValue_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_preferred_stock_value_fy2025_edgar_2025_12_31_0000063908_26_000035))
(assert (! (= xbrl_fact_us_gaap_PreferredStockValue_instant_2025_12_31_unit_USD_dims_none 0) :named xbrl_instance_preferred_stock_value_fy2025))
(assert (! (= common_stock_value_fy2025 xbrl_fact_us_gaap_CommonStockValue_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_common_stock_value_fy2025_edgar_2025_12_31_0000063908_26_000035))
(assert (! (= xbrl_fact_us_gaap_CommonStockValue_instant_2025_12_31_unit_USD_dims_none 17) :named xbrl_instance_common_stock_value_fy2025))
(assert (! (= additional_paid_in_capital_fy2025 xbrl_fact_us_gaap_AdditionalPaidInCapital_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_additional_paid_in_capital_fy2025_edgar_2025_12_31_0000063908_26_000035))
(assert (! (= xbrl_fact_us_gaap_AdditionalPaidInCapital_instant_2025_12_31_unit_USD_dims_none 9641) :named xbrl_instance_additional_paid_in_capital_fy2025))
(assert (! (= retained_earnings_accumulated_deficit_fy2025 xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_retained_earnings_accumulated_deficit_fy2025_edgar_2025_12_31_0000063908_26_000035))
(assert (! (= xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2025_12_31_unit_USD_dims_none 70282) :named xbrl_instance_retained_earnings_accumulated_deficit_fy2025))
(assert (! (= accumulated_other_comprehensive_income_loss_net_of_tax_fy2025 xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_accumulated_other_comprehensive_income_loss_net_of_tax_fy2025_edgar_2025_12_31_0000063908_26_000035))
(assert (! (= xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2025_12_31_unit_USD_dims_none -2414) :named xbrl_instance_accumulated_other_comprehensive_income_loss_net_of_tax_fy2025))
(assert (! (= treasury_stock_value_fy2025 xbrl_fact_us_gaap_TreasuryStockValue_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_treasury_stock_value_fy2025_edgar_2025_12_31_0000063908_26_000035))
(assert (! (= xbrl_fact_us_gaap_TreasuryStockValue_instant_2025_12_31_unit_USD_dims_none 79316) :named xbrl_instance_treasury_stock_value_fy2025))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_StockholdersEquity_instant_2025_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_PreferredStockValue_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_CommonStockValue_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AdditionalPaidInCapital_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2025_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_TreasuryStockValue_instant_2025_12_31_unit_USD_dims_none))) 3.5) :named xbrl_calc_12_337340623_StockholdersEquity_c_6_upper))
(assert (! (>= (- xbrl_fact_us_gaap_StockholdersEquity_instant_2025_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_PreferredStockValue_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_CommonStockValue_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AdditionalPaidInCapital_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_RetainedEarningsAccumulatedDeficit_instant_2025_12_31_unit_USD_dims_none xbrl_fact_us_gaap_AccumulatedOtherComprehensiveIncomeLossNetOfTax_instant_2025_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_TreasuryStockValue_instant_2025_12_31_unit_USD_dims_none))) (- 3.5)) :named xbrl_calc_12_337340623_StockholdersEquity_c_6_lower))

(check-sat)
(get-unsat-core)
(get-model)