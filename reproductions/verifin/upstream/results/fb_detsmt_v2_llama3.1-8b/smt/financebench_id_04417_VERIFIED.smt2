(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_inventory Real)
(declare-const inventory Real)

(assert (! (= inventory 5409) :named evidence_inventory))

(assert (! (= computed_inventory inventory) :named formula_inventory))

(assert (! (<= (- computed_inventory 5409) 5.4089999999999998) :named claim_upper))
(assert (! (<= (- 5409 computed_inventory) 5.4089999999999998) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)