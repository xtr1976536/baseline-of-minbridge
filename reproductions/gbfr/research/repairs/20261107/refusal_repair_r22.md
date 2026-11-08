# R22 minimal general repairs

The source is stable. This agent made **0 API calls** and did not resume the full experiment.

Changes are static OQA/OES/OPE contracts for period flows versus balances, local footnote scope and whole/component inclusion, percentage-point differences versus relative growth, directional versus symmetric differences, and DirectRetrieval scalar identity. Both rate and principal retain entity/instrument/time/coverage scope. No output is rewritten to match an answer.

The code-level metadata repair preserves an explicit OES unknown source scale instead of inheriting the requested display scale. The source number is unchanged; known thousand/ones scale conversions remain permitted in OPE. Each applicable direct path records requested, observed and effective scale in `source_scale_resolution`. Legacy responses lacking observed_meta retain the earlier fallback for compatibility.

Validation: **111 passed, 0 failed**, including **19 new R22 cases** (5.66 seconds). The tests cover the positive and negative protocol boundaries and actual local program execution, but use scripted plans/programs. They are **not fresh-API semantic accuracy verification**. The parent will separately run the full suite and true end-to-end validation.

All five Appendix F prompt bodies are byte-identical to the frozen R21 snapshot; their SHA256 values and current code hashes are in the adjacent JSON. No dash-to-zero fallback, contra-asset absolute value, special benchmark coefficient, scorer change, gold edit, additional judge or answer-driven retry was introduced.
