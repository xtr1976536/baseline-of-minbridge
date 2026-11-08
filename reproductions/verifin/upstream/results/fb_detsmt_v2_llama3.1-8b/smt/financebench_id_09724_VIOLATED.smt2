(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_cogs_percent_margin Real)
(declare-const cost_of_revenue Real)
(declare-const revenue Real)

(assert (! (= cost_of_revenue 15357) :named evidence_cost_of_revenue))
(assert (! (= revenue 38655) :named evidence_revenue))

(assert (! (= computed_cogs_percent_margin (* (/ cost_of_revenue revenue) 100)) :named formula_cogs_percent_margin))
(assert (! (or (> revenue 0) (< revenue 0)) :named domain_cogs_percent_margin_0))

(assert (! (<= (- computed_cogs_percent_margin 60.299999999999997) 0.050000000000000003) :named claim_upper))
(assert (! (<= (- 60.299999999999997 computed_cogs_percent_margin) 0.050000000000000003) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)