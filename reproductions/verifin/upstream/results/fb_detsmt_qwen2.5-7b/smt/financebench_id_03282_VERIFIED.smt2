(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_total_current_liabilities Real)
(declare-const accounts_payable Real)
(declare-const accrued_expenses Real)
(declare-const current_content_liabilities Real)
(declare-const deferred_revenue Real)

(assert (! (= accounts_payable 359.55500000000001) :named evidence_accounts_payable))
(assert (! (= accrued_expenses 315.09399999999999) :named evidence_accrued_expenses))
(assert (! (= current_content_liabilities 4173.0410000000002) :named evidence_current_content_liabilities))
(assert (! (= deferred_revenue 618.62199999999996) :named evidence_deferred_revenue))

(assert (! (= computed_total_current_liabilities (+ current_content_liabilities accounts_payable accrued_expenses deferred_revenue)) :named formula_total_current_liabilities))

(assert (! (<= (- computed_total_current_liabilities 5466.3119999999999) 5.4663120000000003) :named claim_upper))
(assert (! (<= (- 5466.3119999999999 computed_total_current_liabilities) 5.4663120000000003) :named claim_lower))

(check-sat)
(get-unsat-core)
(get-model)