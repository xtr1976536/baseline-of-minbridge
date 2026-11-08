(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_income_loss_fy2025 Real)
(declare-const gross_profit_fy2025 Real)
(declare-const impairment_of_intangible_assets_excluding_goodwill_fy2025 Real)
(declare-const selling_general_and_administrative_expense_fy2025 Real)

(assert (! (= gross_profit_fy2025 50859) :named evidence_gross_profit_fy2025))
(assert (! (= impairment_of_intangible_assets_excluding_goodwill_fy2025 1993) :named evidence_impairment_of_intangible_assets_excluding_goodwill_fy2025))
(assert (! (= selling_general_and_administrative_expense_fy2025 37368) :named evidence_selling_general_and_administrative_expense_fy2025))

(assert (! (= computed_operating_income_loss_fy2025 (+ gross_profit_fy2025 (* (- 1) selling_general_and_administrative_expense_fy2025) (* (- 1) impairment_of_intangible_assets_excluding_goodwill_fy2025))) :named formula_operating_income_loss_fy2025))

(assert (! (<= (- computed_operating_income_loss_fy2025 -12887) 12.887) :named claim_upper))
(assert (! (<= (- -12887 computed_operating_income_loss_fy2025) 12.887) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_12_29_2025_12_27_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_GrossProfit_duration_2024_12_29_2025_12_27_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_ImpairmentOfIntangibleAssetsExcludingGoodwill_duration_2024_12_29_2025_12_27_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_12_29_2025_12_27_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_Revenues_duration_2024_12_29_2025_12_27_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2024_12_29_2025_12_27_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_12_29_2025_12_27_unit_USD_dims_none 43066) :named evidence_xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_12_29_2025_12_27_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_12_29_2025_12_27_unit_USD_dims_none 11498) :named evidence_xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_12_29_2025_12_27_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_Revenues_duration_2024_12_29_2025_12_27_unit_USD_dims_none 93925) :named evidence_xbrl_fact_us_gaap_Revenues_duration_2024_12_29_2025_12_27_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= gross_profit_fy2025 xbrl_fact_us_gaap_GrossProfit_duration_2024_12_29_2025_12_27_unit_USD_dims_none) :named xbrl_bind_gross_profit_fy2025_edgar_2025_12_27_0000077476_26_000007))
(assert (! (= xbrl_fact_us_gaap_GrossProfit_duration_2024_12_29_2025_12_27_unit_USD_dims_none 50859) :named xbrl_instance_gross_profit_fy2025))
(assert (! (= selling_general_and_administrative_expense_fy2025 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2024_12_29_2025_12_27_unit_USD_dims_none) :named xbrl_bind_selling_general_and_administrative_expense_fy2025_edgar_2025_12_27_0000077476_26_000007))
(assert (! (= xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2024_12_29_2025_12_27_unit_USD_dims_none 37368) :named xbrl_instance_selling_general_and_administrative_expense_fy2025))
(assert (! (= impairment_of_intangible_assets_excluding_goodwill_fy2025 xbrl_fact_us_gaap_ImpairmentOfIntangibleAssetsExcludingGoodwill_duration_2024_12_29_2025_12_27_unit_USD_dims_none) :named xbrl_bind_impairment_of_intangible_assets_excluding_goodwill_fy2025_edgar_2025_12_27_0000077476_26_000007))
(assert (! (= xbrl_fact_us_gaap_ImpairmentOfIntangibleAssetsExcludingGoodwill_duration_2024_12_29_2025_12_27_unit_USD_dims_none 1993) :named xbrl_instance_impairment_of_intangible_assets_excluding_goodwill_fy2025))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_12_29_2025_12_27_unit_USD_dims_none (+ xbrl_fact_us_gaap_GrossProfit_duration_2024_12_29_2025_12_27_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2024_12_29_2025_12_27_unit_USD_dims_none) (* -1 xbrl_fact_us_gaap_ImpairmentOfIntangibleAssetsExcludingGoodwill_duration_2024_12_29_2025_12_27_unit_USD_dims_none))) 2) :named xbrl_calc_2_177463439_OperatingIncomeLoss_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2024_12_29_2025_12_27_unit_USD_dims_none (+ xbrl_fact_us_gaap_GrossProfit_duration_2024_12_29_2025_12_27_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_SellingGeneralAndAdministrativeExpense_duration_2024_12_29_2025_12_27_unit_USD_dims_none) (* -1 xbrl_fact_us_gaap_ImpairmentOfIntangibleAssetsExcludingGoodwill_duration_2024_12_29_2025_12_27_unit_USD_dims_none))) (- 2)) :named xbrl_calc_2_177463439_OperatingIncomeLoss_c_1_lower))
(assert (! (<= (- xbrl_fact_us_gaap_GrossProfit_duration_2024_12_29_2025_12_27_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2024_12_29_2025_12_27_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_12_29_2025_12_27_unit_USD_dims_none))) 1.5) :named xbrl_calc_4_177463439_GrossProfit_c_1_upper))
(assert (! (>= (- xbrl_fact_us_gaap_GrossProfit_duration_2024_12_29_2025_12_27_unit_USD_dims_none (+ xbrl_fact_us_gaap_Revenues_duration_2024_12_29_2025_12_27_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2024_12_29_2025_12_27_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_4_177463439_GrossProfit_c_1_lower))

(check-sat)
(get-unsat-core)
(get-model)