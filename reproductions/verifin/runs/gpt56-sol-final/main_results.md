# VeriFin main experiment

Only new local runs are shown. Published/archived author outputs are not local measurements.

| Model | Dataset | N | TA | FA | TR | FR | Abs | Unresolved | Errors | Missing | Precision [95% CI] | Decision accuracy [95% CI] | Coverage [95% CI] | Status |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| GPT-5.6-Sol | FinanceBench | 67 | 18 | 6 | 1 | 1 | 39 | 2 | 0 | 0 | 75.00% [53.29, 90.23] | 73.08% [52.21, 88.43] | 41.79% [29.85, 54.48] | complete |

Intervals are exact 95% Clopper–Pearson intervals. Unresolved correctness is excluded from precision and decision accuracy, and retained in coverage. Errors and missing rows are reported separately from abstentions.

TA/FA: correct/incorrect accepted claims. TR/FR: incorrect/correct rejected claims. Precision = TA/(TA+FA); decision accuracy = (TA+TR)/(TA+FA+TR+FR); coverage includes every non-abstaining decision.

The backbone is an explicit user override. This is a method reproduction with documented public-asset differences, not a claim of numerical equivalence to the paper’s original backbone runs.
