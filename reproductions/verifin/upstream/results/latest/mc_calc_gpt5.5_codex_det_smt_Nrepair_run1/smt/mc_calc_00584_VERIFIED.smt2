(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_operating_income_loss_fy2021 Real)
(declare-const general_and_administrative_expense_fy2021 Real)
(declare-const gross_profit_fy2021 Real)
(declare-const research_and_development_expense_fy2021 Real)
(declare-const selling_and_marketing_expense_fy2021 Real)

(assert (! (= general_and_administrative_expense_fy2021 5107) :named evidence_general_and_administrative_expense_fy2021))
(assert (! (= gross_profit_fy2021 115856) :named evidence_gross_profit_fy2021))
(assert (! (= research_and_development_expense_fy2021 20716) :named evidence_research_and_development_expense_fy2021))
(assert (! (= selling_and_marketing_expense_fy2021 20117) :named evidence_selling_and_marketing_expense_fy2021))

(assert (! (= computed_operating_income_loss_fy2021 (+ gross_profit_fy2021 (* (- 1) research_and_development_expense_fy2021) (* (- 1) selling_and_marketing_expense_fy2021) (* (- 1) general_and_administrative_expense_fy2021))) :named formula_operating_income_loss_fy2021))

(assert (! (<= (- computed_operating_income_loss_fy2021 69916) 69.915999999999997) :named claim_upper))
(assert (! (<= (- 69916 computed_operating_income_loss_fy2021) 69.915999999999997) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2020_07_01_2021_06_30_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_GeneralAndAdministrativeExpense_duration_2020_07_01_2021_06_30_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_GrossProfit_duration_2020_07_01_2021_06_30_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2020_07_01_2021_06_30_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2020_07_01_2021_06_30_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2020_07_01_2021_06_30_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_SellingAndMarketingExpense_duration_2020_07_01_2021_06_30_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2020_07_01_2021_06_30_unit_USD_dims_none 52232) :named evidence_xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2020_07_01_2021_06_30_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2020_07_01_2021_06_30_unit_USD_dims_none 69916) :named evidence_xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2020_07_01_2021_06_30_unit_USD_dims_none))
(assert (! (= xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2020_07_01_2021_06_30_unit_USD_dims_none 168088) :named evidence_xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2020_07_01_2021_06_30_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= gross_profit_fy2021 xbrl_fact_us_gaap_GrossProfit_duration_2020_07_01_2021_06_30_unit_USD_dims_none) :named xbrl_bind_gross_profit_fy2021_edgar_2021_06_30_0001564590_21_039151))
(assert (! (= xbrl_fact_us_gaap_GrossProfit_duration_2020_07_01_2021_06_30_unit_USD_dims_none 115856) :named xbrl_instance_gross_profit_fy2021))
(assert (! (= research_and_development_expense_fy2021 xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2020_07_01_2021_06_30_unit_USD_dims_none) :named xbrl_bind_research_and_development_expense_fy2021_edgar_2021_06_30_0001564590_21_039151))
(assert (! (= xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2020_07_01_2021_06_30_unit_USD_dims_none 20716) :named xbrl_instance_research_and_development_expense_fy2021))
(assert (! (= selling_and_marketing_expense_fy2021 xbrl_fact_us_gaap_SellingAndMarketingExpense_duration_2020_07_01_2021_06_30_unit_USD_dims_none) :named xbrl_bind_selling_and_marketing_expense_fy2021_edgar_2021_06_30_0001564590_21_039151))
(assert (! (= xbrl_fact_us_gaap_SellingAndMarketingExpense_duration_2020_07_01_2021_06_30_unit_USD_dims_none 20117) :named xbrl_instance_selling_and_marketing_expense_fy2021))
(assert (! (= general_and_administrative_expense_fy2021 xbrl_fact_us_gaap_GeneralAndAdministrativeExpense_duration_2020_07_01_2021_06_30_unit_USD_dims_none) :named xbrl_bind_general_and_administrative_expense_fy2021_edgar_2021_06_30_0001564590_21_039151))
(assert (! (= xbrl_fact_us_gaap_GeneralAndAdministrativeExpense_duration_2020_07_01_2021_06_30_unit_USD_dims_none 5107) :named xbrl_instance_general_and_administrative_expense_fy2021))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2020_07_01_2021_06_30_unit_USD_dims_none (+ xbrl_fact_us_gaap_GrossProfit_duration_2020_07_01_2021_06_30_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2020_07_01_2021_06_30_unit_USD_dims_none) (* -1 xbrl_fact_us_gaap_SellingAndMarketingExpense_duration_2020_07_01_2021_06_30_unit_USD_dims_none) (* -1 xbrl_fact_us_gaap_GeneralAndAdministrativeExpense_duration_2020_07_01_2021_06_30_unit_USD_dims_none))) 2.5) :named xbrl_calc_2_23524336_OperatingIncomeLoss_C_0000789019_20200701_20210630_upper))
(assert (! (>= (- xbrl_fact_us_gaap_OperatingIncomeLoss_duration_2020_07_01_2021_06_30_unit_USD_dims_none (+ xbrl_fact_us_gaap_GrossProfit_duration_2020_07_01_2021_06_30_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_ResearchAndDevelopmentExpense_duration_2020_07_01_2021_06_30_unit_USD_dims_none) (* -1 xbrl_fact_us_gaap_SellingAndMarketingExpense_duration_2020_07_01_2021_06_30_unit_USD_dims_none) (* -1 xbrl_fact_us_gaap_GeneralAndAdministrativeExpense_duration_2020_07_01_2021_06_30_unit_USD_dims_none))) (- 2.5)) :named xbrl_calc_2_23524336_OperatingIncomeLoss_C_0000789019_20200701_20210630_lower))
(assert (! (<= (- xbrl_fact_us_gaap_GrossProfit_duration_2020_07_01_2021_06_30_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2020_07_01_2021_06_30_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2020_07_01_2021_06_30_unit_USD_dims_none))) 1.5) :named xbrl_calc_3_23524336_GrossProfit_C_0000789019_20200701_20210630_upper))
(assert (! (>= (- xbrl_fact_us_gaap_GrossProfit_duration_2020_07_01_2021_06_30_unit_USD_dims_none (+ xbrl_fact_us_gaap_RevenueFromContractWithCustomerExcludingAssessedTax_duration_2020_07_01_2021_06_30_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_CostOfGoodsAndServicesSold_duration_2020_07_01_2021_06_30_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_3_23524336_GrossProfit_C_0000789019_20200701_20210630_lower))

(check-sat)
(get-unsat-core)
(get-model)