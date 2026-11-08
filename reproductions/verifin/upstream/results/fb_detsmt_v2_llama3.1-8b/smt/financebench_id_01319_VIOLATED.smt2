(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_restructuring_costs_income_statement Real)
(declare-const restructuring_costs Real)

(assert (! (= restructuring_costs 129) :named evidence_restructuring_costs))

(assert (! (= computed_restructuring_costs_income_statement restructuring_costs) :named formula_restructuring_costs_income_statement))

(assert (! (<= (- computed_restructuring_costs_income_statement 0) 0.5) :named claim_upper))
(assert (! (<= (- 0 computed_restructuring_costs_income_statement) 0.5) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)