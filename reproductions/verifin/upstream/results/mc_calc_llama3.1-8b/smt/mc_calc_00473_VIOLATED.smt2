(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_income_before_income_taxes Real)
(declare-const income_from_continuing_operations_before_income_2021 Real)
(declare-const income_from_continuing_operations_before_income_2022 Real)
(declare-const income_from_continuing_operations_before_income_2023 Real)

(assert (! (= income_from_continuing_operations_before_income_2021 -2654.0) :named evidence_income_from_continuing_operations_before_income_2021))
(assert (! (= income_from_continuing_operations_before_income_2022 -6602.0) :named evidence_income_from_continuing_operations_before_income_2022))
(assert (! (= income_from_continuing_operations_before_income_2023 -227.0) :named evidence_income_from_continuing_operations_before_income_2023))

(assert (! (= computed_income_before_income_taxes (/ (- income_from_continuing_operations_before_income_2023 income_from_continuing_operations_before_income_2022) income_from_continuing_operations_before_income_2021)) :named formula_income_before_income_taxes))

(assert (! (or (> income_from_continuing_operations_before_income_2021 0) (< income_from_continuing_operations_before_income_2021 0)) :named denom_nonzero))

(assert (! (<= (- computed_income_before_income_taxes 8917.0) 89.17) :named claim_upper))
(assert (! (<= (- 8917.0 computed_income_before_income_taxes) 89.17) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)