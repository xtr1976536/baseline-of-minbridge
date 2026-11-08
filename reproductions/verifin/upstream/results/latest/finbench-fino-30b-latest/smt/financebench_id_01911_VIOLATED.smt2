(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_interest_coverage_ratio Real)
(declare-const adjusted_ebit Real)
(declare-const interest_expense Real)

(assert (! (= adjusted_ebit 957.30700000000002) :named evidence_adjusted_ebit))
(assert (! (= interest_expense 594.95400000000006) :named evidence_interest_expense))

(assert (! (= computed_interest_coverage_ratio (/ adjusted_ebit interest_expense)) :named formula_interest_coverage_ratio))
(assert (! (or (> interest_expense 0) (< interest_expense 0)) :named domain_interest_coverage_ratio_0))

(assert (! (<= (- computed_interest_coverage_ratio 7) 0.050000000000000003) :named claim_upper))
(assert (! (<= (- 7 computed_interest_coverage_ratio) 0.050000000000000003) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)