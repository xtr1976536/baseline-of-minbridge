# VeriFin main experiment

Only new local runs are shown. Published/archived author outputs are not local measurements.

| Model | Dataset | N | TA | FA | TR | FR | Abs | Unresolved | Errors | Missing | Precision [95% CI] | Decision accuracy [95% CI] | Coverage [95% CI] | Status |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| GPT-5.6-Sol | FinanceBench | 35 | 27 | 0 | 2 | 0 | 6 | 0 | 0 | 0 | 100.00% [87.23, 100.00] | 100.00% [88.06, 100.00] | 82.86% [66.35, 93.44] | complete |

Intervals are exact 95% Clopper–Pearson intervals. Unresolved correctness is excluded from precision and decision accuracy, and retained in coverage. Errors and missing rows are reported separately from abstentions.

TA/FA: correct/incorrect accepted claims. TR/FR: incorrect/correct rejected claims. Precision = TA/(TA+FA); decision accuracy = (TA+TR)/(TA+FA+TR+FR); coverage includes every non-abstaining decision.

The backbone is an explicit user override. This is a method reproduction with documented public-asset differences, not a claim of numerical equivalence to the paper’s original backbone runs.
