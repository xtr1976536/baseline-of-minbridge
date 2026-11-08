(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_comparable_constant_currency_sales_growth Real)
(declare-const fx_impact Real)
(declare-const one_off_items_impact Real)
(declare-const passthrough_impact Real)
(declare-const sales_2022 Real)
(declare-const sales_2023 Real)

(assert (! (= fx_impact -3) :named evidence_fx_impact))
(assert (! (= one_off_items_impact -1) :named evidence_one_off_items_impact))
(assert (! (= passthrough_impact 5) :named evidence_passthrough_impact))
(assert (! (= sales_2022 14544) :named evidence_sales_2022))
(assert (! (= sales_2023 14694) :named evidence_sales_2023))

(assert (! (= computed_comparable_constant_currency_sales_growth (- (- (- (* (/ (- sales_2023 sales_2022) sales_2022) 100) fx_impact) passthrough_impact) one_off_items_impact)) :named formula_comparable_constant_currency_sales_growth))
(assert (! (or (> sales_2022 0) (< sales_2022 0)) :named domain_comparable_constant_currency_sales_growth_0))

(assert (! (<= (- computed_comparable_constant_currency_sales_growth 0) 0.5) :named claim_upper))
(assert (! (<= (- 0 computed_comparable_constant_currency_sales_growth) 0.5) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)