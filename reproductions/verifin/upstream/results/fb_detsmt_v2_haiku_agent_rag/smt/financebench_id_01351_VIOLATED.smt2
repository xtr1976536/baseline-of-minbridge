(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_effective_tax_rate_change Real)
(declare-const effective_tax_rate_2021 Real)
(declare-const effective_tax_rate_2022 Real)

(assert (! (= effective_tax_rate_2021 24.600000000000001) :named evidence_effective_tax_rate_2021))
(assert (! (= effective_tax_rate_2022 21.600000000000001) :named evidence_effective_tax_rate_2022))

(assert (! (= computed_effective_tax_rate_change (* (- effective_tax_rate_2022 effective_tax_rate_2021) 100)) :named formula_effective_tax_rate_change))

(assert (! (<= (- computed_effective_tax_rate_change -3) 0.050000000000000003) :named claim_upper))
(assert (! (<= (- -3 computed_effective_tax_rate_change) 0.050000000000000003) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)