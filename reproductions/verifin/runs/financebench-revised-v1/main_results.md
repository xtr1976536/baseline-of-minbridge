# VeriFin main experiment

Only new local runs are shown. Published/archived author outputs are not local measurements.

| Model | Dataset | N | TA | FA | TR | FR | Abs | Unresolved | Errors | Missing | Precision [95% CI] | Decision accuracy [95% CI] | Coverage [95% CI] | Status |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| GPT-5.6-Sol | FinanceBench | 67 | 19 | 5 | 5 | 1 | 34 | 3 | 0 | 0 | 79.17% [57.85, 92.87] | 80.00% [61.43, 92.29] | 49.25% [36.82, 61.76] | complete |

Intervals are exact 95% Clopper–Pearson intervals. Unresolved correctness is excluded from precision and decision accuracy, and retained in coverage. Errors and missing rows are reported separately from abstentions.

TA/FA: correct/incorrect accepted claims. TR/FR: incorrect/correct rejected claims. Precision = TA/(TA+FA); decision accuracy = (TA+TR)/(TA+FA+TR+FR); coverage includes every non-abstaining decision.

The backbone is an explicit user override. This is a method reproduction with documented public-asset differences, not a claim of numerical equivalence to the paper’s original backbone runs.
