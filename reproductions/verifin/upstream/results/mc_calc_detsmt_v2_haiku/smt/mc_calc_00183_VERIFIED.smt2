(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_gross_profit_fy2026 Real)
(declare-const cost_of_goods_and_services_sold_fy2026 Real)
(declare-const revenue_from_contract_with_customer_excluding_assessed_tax_fy2026 Real)

(assert (! (= cost_of_goods_and_services_sold_fy2026 9270) :named evidence_cost_of_goods_and_services_sold_fy2026))
(assert (! (= revenue_from_contract_with_customer_excluding_assessed_tax_fy2026 41525) :named evidence_revenue_from_contract_with_customer_excluding_assessed_tax_fy2026))

(assert (! (= computed_gross_profit_fy2026 (+ revenue_from_contract_with_customer_excluding_assessed_tax_fy2026 (* (- 1) cost_of_goods_and_services_sold_fy2026))) :named formula_gross_profit_fy2026))

(assert (! (<= (- computed_gross_profit_fy2026 32255) 32.255000000000003) :named claim_upper))
(assert (! (<= (- 32255 computed_gross_profit_fy2026) 32.255000000000003) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)