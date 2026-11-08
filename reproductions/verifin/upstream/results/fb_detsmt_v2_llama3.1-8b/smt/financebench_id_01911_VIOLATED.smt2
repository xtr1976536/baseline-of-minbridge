(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_interest_coverage_ratio Real)
(declare-const adjusted_ebit Real)
(declare-const interest_expense Real)

(assert (! (= adjusted_ebit 957.30700000000002) :named evidence_adjusted_ebit))
(assert (! (= interest_expense 594.95400000000006) :named evidence_interest_expense))

(assert (! (and (=> (<= adjusted_ebit 0) (= computed_interest_coverage_ratio 0)) (=> (> adjusted_ebit 0) (= computed_interest_coverage_ratio (/ adjusted_ebit interest_expense)))) :named formula_interest_coverage_ratio))
(assert (! (or (> interest_expense 0) (< interest_expense 0)) :named domain_interest_coverage_ratio_0))

(assert (! (<= (- computed_interest_coverage_ratio 169.90000000000001) 0.01) :named claim_upper))
(assert (! (<= (- 169.90000000000001 computed_interest_coverage_ratio) 0.01) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)