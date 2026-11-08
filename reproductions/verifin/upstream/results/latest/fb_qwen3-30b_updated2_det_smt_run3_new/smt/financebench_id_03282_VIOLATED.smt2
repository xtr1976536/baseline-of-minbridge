(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_total_current_liabilities Real)
(declare-const current_liabilities Real)

(assert (! (= current_liabilities 5466.3119999999999) :named evidence_current_liabilities))

(assert (! (= computed_total_current_liabilities current_liabilities) :named formula_total_current_liabilities))

(assert (! (<= (- computed_total_current_liabilities 5466312) 5466.3119999999999) :named claim_upper))
(assert (! (<= (- 5466312 computed_total_current_liabilities) 5466.3119999999999) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)