# FinanceBench First-Question Trace

This folder puts the first completed FinanceBench verifier run in one place.
It is generated from `runs/verification_complete` and traces question `financebench_id_03029` end to end.

Question: What is the FY2018 capital expenditure amount (in USD millions) for 3M? Give a response to the question by relying on the details shown in the cash flow statement.
Gold answer: $1577.00
Final verifier status: VERIFIED
First-pass solver status: UNSAT
Verified answer: The verified capital expenditures is 1577 USD millions. Calculation: 1577.

For the concrete output of each stage, start with [`PIPELINE_OUTPUTS.md`](PIPELINE_OUTPUTS.md).

Open [`index.html`](index.html) for the browser view of the same stage outputs.

## Stage Index

0. `00_dataset_load_and_filter`: FinanceBench source row, direct-numerical filter result, and run-level counts.
1. `01_filing_corpus_and_retriever`: corpus/load stats and retriever configuration used by the run.
2. `02_retrieval_plan_llm`: retrieval-plan LLM prompt, response, and parsed plan.
3. `03_planned_evidence_retrieval`: retrieved chunk ids and full evidence text used downstream.
4. `04_answer_llm`: answer LLM prompt, response, and parsed answer.
5. `05_formalizer_llm_certificate`: formalizer LLM prompt, response, and verification certificate.
6. `06_certificate_grounding_validator`: grounding validator result plus evidence bindings/provenance.
7. `07_typed_verification_ir`: typed `VerificationIR`, claim, formula, facts, units, and tolerance.
8. `08_optional_policy_semantic_check`: policy semantic check status for this run.
9. `09_smt_generation_llm`: SMT-generation LLM prompt, response, and emitted SMT-LIB.
10. `10_smt_semantic_sanitizer`: sanitizer validation of the SMT against the typed IR.
11. `11_z3_counterexample_check`: recorded Z3 counterexample-check result and the SMT file.
12. `12_final_decision_and_artifacts`: final `RavResult`, verifier certificate, and decision summary.

## Notes

- The folder is an artifact trace, not a new run. It does not call an LLM.
- The run used a prebuilt filing corpus at `data/corpus` with real retrieval, not oracle evidence.
- `z3` and Python `z3` are not available in this shell now, so the Z3 and SMT-sanitizer stages preserve the statuses already captured by the completed run.
