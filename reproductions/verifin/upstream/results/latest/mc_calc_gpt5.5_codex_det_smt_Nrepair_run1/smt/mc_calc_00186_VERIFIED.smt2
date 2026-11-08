(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_gross_profit_fy2026 Real)
(declare-const cost_of_revenue_fy2026 Real)
(declare-const revenue_from_contract_with_customer_excluding_assessed_tax_fy2026 Real)

(assert (! (= cost_of_revenue_fy2026 109818) :named evidence_cost_of_revenue_fy2026))
(assert (! (= revenue_from_contract_with_customer_excluding_assessed_tax_fy2026 164683) :named evidence_revenue_from_contract_with_customer_excluding_assessed_tax_fy2026))

(assert (! (= computed_gross_profit_fy2026 (+ revenue_from_contract_with_customer_excluding_assessed_tax_fy2026 (* (- 1) cost_of_revenue_fy2026))) :named formula_gross_profit_fy2026))

(assert (! (<= (- computed_gross_profit_fy2026 54865) 54.865000000000002) :named claim_upper))
(assert (! (<= (- 54865 computed_gross_profit_fy2026) 54.865000000000002) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)