(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_tangible_book_value_per_share Real)
(declare-const tangible_book_value_per_share Real)

(assert (! (= tangible_book_value_per_share 66.560000000000002) :named evidence_tangible_book_value_per_share))

(assert (! (= computed_tangible_book_value_per_share tangible_book_value_per_share) :named formula_tangible_book_value_per_share))

(assert (! (<= (- computed_tangible_book_value_per_share 206000) 500) :named claim_upper))
(assert (! (<= (- 206000 computed_tangible_book_value_per_share) 500) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)