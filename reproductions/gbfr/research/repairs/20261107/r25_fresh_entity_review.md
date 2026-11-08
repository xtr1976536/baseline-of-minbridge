# R25 fresh FinQA entity review

This is a **read-only, 0 API** review of `FinQA:counterfactual:50`. R25 code, native data, labels, predictions and scores remain frozen. The adjacent JSON preserves the exact input, OQA/OES responses, final program, source hashes and the old supplemental prompt sentence.

## What the evidence establishes

The question names **Nimbus Corp**. The complete supplied document contains no Nimbus name and no identified issuer: it uses **we 12 times / our 13 times**. OQA retains Nimbus correctly as the requested entity constraint. OES then copies Nimbus into its binding and returns found=true with confidence 0.98, but its notes only explain the lease-obligation row alias and unit. Its evidence is the `Less current portion` table cell; no quoted span connects that row's anonymous issuer to Nimbus.

The table/lexical audit reports supported because the numeric cell is present. That must not be read as independent validation of issuer identity. Query-constraint propagation likewise preserves the request; it does not supply identity evidence.

The narrative and all 13 table rows exactly match original FinQA `ANET/2015/page_156.pdf-2`. That filename is **audit-only provenance**: it was not supplied to the model as issuer evidence. It cannot be used retrospectively as a hidden company lookup or an answer oracle.

## Overbroad policy and identifiability

The supplemental OES sentence permits the anonymous reporting entity to refer to a company named by the query/variable when there is no competing referent. This is too broad for the paper's strict entity constraint: **absence of a competing issuer does not establish the requested issuer**. The OES response's copied constraint is also not proof.

At the same time, Q/D alone does not prove that the excerpt belongs to a different company. An otherwise identical anonymous excerpt could genuinely be from Nimbus. What is visible is **unverified entity scope**; the hidden entity swap itself is not visible without trusted source identity. Thus both findings hold: the policy permits an unsupported assertion, and the mismatch cannot be diagnosed as an explicit contradiction from these inputs alone.

The native unanswerable label and failed-abstention score stay unchanged. This audit neither drops the example nor changes any denominator.

## Minimal future proposal; not applied

Require a document-supported or explicitly supplied trusted source-identity anchor before resolving we/our/the company to a particular externally named company. A query name is a constraint, not evidence of ownership; no competing name alone is insufficient. If that link is absent, OES should mark the named entity unresolved and explain missing entity evidence, rather than claim a proven wrong issuer.

Preserve normal reference resolution when the source already establishes the reporter, supports a company alias, or the question simply asks about the anonymous reporting entity. Separate numeric/table support from entity-link provenance in audit reporting. No extra judge, hidden-label lookup or answer-driven retry is needed for that distinction.

This can reduce entity-swap leaks, but can increase refusals on legitimate named-company questions whose financial excerpts omit issuer identity. A Q/D-only rule cannot eliminate both errors when the ownership link is absent. Trusted document ownership, if the task assumes it, must be supplied consistently and disclosed rather than guessed from the question.

No improvement is claimed from this audit. R25 remains **fixed-two 50%, reference-display 60%, abstention accuracy 50%, false refusals 0/8**. Any future policy change requires a separately frozen, new validation set.
