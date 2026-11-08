# R25 FinQA refusal audit

Only three historical FinQA examples were inspected. The agent made **0 API calls**, did not inspect the new ten-question validation set and did not resume the full experiment. The adjacent JSON preserves exact questions/contexts, real OQA/OES responses, native FinQA programs, before/after optional hints, source hashes and paper locations. No model OPE program exists for these refusals: they stop at missing evidence.

| Case | Evidence-based verdict | Safe boundary |
|---|---|---|
| R24 MKTX/2004/page_99.pdf-2 | The question asks outstanding shares; the gold program uses authorized shares. The model's refusal is justified under the paper. | Never equate authorized, issued and outstanding. Keep native benchmark scoring unchanged and explain the inconsistency separately. |
| R23 PNC/2014/page_111.pdf-2 | OQA adds Total and loses the local tax-credit scope. However gold -85 compares the included unfunded-commitment components, whereas the question refers to balances including them. | Preserve local antecedents and whole/component identity; do not pick amounts using gold or add an already included amount twice. Fixing Total does not prove -85 is the literal balance answer. |
| R23 ALXN/2016/page_153.pdf-2 | OES rejects the 2017 monetary dash. This is real U+2014. Other maturity rows sum to the separately reported 3081 term-loan balance, and gold uses 3500/3081. | No universal dash-to-zero or OES residual calculation. Source-defined nil can be normalized with provenance; no nil legend is present in this D. Voluntary 2017 payments are not contractual 2017 maturity evidence. |

The paper requires document-grounded answers and matching metric, entity, period and units; ambiguous or missing evidence must remain missing. OES cannot derive a missing operand by arithmetic. Therefore “benchmark misrefusal” and “a refusal inconsistent with the paper” are distinct audit findings, without changing labels or evaluation.

## Minimal confirmed repair

After the parent authorized implementation, only `metric_hints` and its new tests were changed. The old optional OQA suggestions demonstrably mapped query fragments to unrelated definitions: equity investments to shareholders equity, ordinary change to a security closing-price movement, term to duration, and borrowing to portfolio financing. The old prefix guard covered only one side of a phrase.

The repair conservatively filters generic task words, ordinary short words and incomplete noun/qualifier phrases on either side. Full registered names, lawful financial measure names and registered abbreviations remain candidates; Price Return on an investment remains valid. It does not maintain a benchmark-specific financial whitelist, change graph aliases, replace OES goals, rewrite accepted OQA plans or force any answer.

Validation: **146 passed, 0 failed**, including **35 new R25 tests** (6.75 seconds). These are offline protocol and phrase-boundary checks, **not fresh-API accuracy evidence**. Five Appendix F prompt bodies are byte-identical to frozen R24. Known compatibility cost: optional-hint recall is lower for short/ambiguous fragments; the original graph and request remain available to the model and resolver.
