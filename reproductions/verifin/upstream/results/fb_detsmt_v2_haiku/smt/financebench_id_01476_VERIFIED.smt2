(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_core_constant_currency_eps_growth_guidance_increase Real)
(declare-const new_guidance Real)
(declare-const previous_guidance Real)

(assert (! (= new_guidance 9) :named evidence_new_guidance))
(assert (! (= previous_guidance 8) :named evidence_previous_guidance))

(assert (! (= computed_core_constant_currency_eps_growth_guidance_increase (- new_guidance previous_guidance)) :named formula_core_constant_currency_eps_growth_guidance_increase))

(assert (! (<= (- computed_core_constant_currency_eps_growth_guidance_increase 1) 0.5) :named claim_upper))
(assert (! (<= (- 1 computed_core_constant_currency_eps_growth_guidance_increase) 0.5) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)