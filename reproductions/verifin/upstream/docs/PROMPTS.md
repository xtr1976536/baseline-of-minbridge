# Prompt index

This file points reviewers to the executable prompt templates used by the
released implementation. The source constants linked below are authoritative:
the pipeline formats them at runtime with the question, evidence, registry
entries, grounded facts, or repair diagnostics. No hidden system prompt is
required by these code paths.

## Paper pipeline

| Stage | Executable template |
|---|---|
| Answer generation | [`src/verifiqa/generation/answer_generator.py`](../src/verifiqa/generation/answer_generator.py) (`_PROMPT`) |
| Retrieval planning | [`src/verifiqa/retrieval/planner.py`](../src/verifiqa/retrieval/planner.py) (`_PROMPT`) |
| Claim decomposition and parsing | [`src/verifiqa/agent/claim_classifier.py`](../src/verifiqa/agent/claim_classifier.py) (`_DECOMPOSE_PROMPT`, `_CLAIM_PARSE_PROMPT`) |
| Operand extraction and feedback repair | [`src/verifiqa/agent/fact_extractor.py`](../src/verifiqa/agent/fact_extractor.py) (`_PROMPT`, `_FEEDBACK_PROMPT`) |
| Verification-plan formalization and repair | [`src/verifiqa/formalization/formalizer.py`](../src/verifiqa/formalization/formalizer.py) (`_PROMPT`, `_REPAIR_PROMPT`) |
| XBRL candidate binding | [`src/verifiqa/verification/xbrl_llm_binder.py`](../src/verifiqa/verification/xbrl_llm_binder.py) (`_BINDER_PROMPT`) |
| SMT generation and repair | [`src/verifiqa/verification/smt_generator.py`](../src/verifiqa/verification/smt_generator.py) (`_PROMPT` and repair templates) |
| Filing-specific non-GAAP reconciliation | [`src/verifiqa/verification/nongaap_reconciler.py`](../src/verifiqa/verification/nongaap_reconciler.py) (`_PROMPT`) |

The deterministic-SMT configuration used for the headline VeriFin runs renders
the obligation from the typed verification plan instead of calling the SMT
generation prompt. The earlier LLM-SMT ablations remain released and are
identified in [`results/README.md`](../results/README.md).

## Headline baselines

The exact paper baseline prompts are defined together in
[`scripts/baselines.py`](../scripts/baselines.py):

- `_DIRECT_PROMPT` — direct answer generation;
- `_JUDGE_PROMPT` — evidence-only LLM judge;
- `_JUDGE_GROUNDED_PROMPT` — judge supplied with formula and operands; and
- `_POT_PROMPT` — Program-of-Thought code generation.

The canonical comparison reuses one frozen Claude Haiku 4.5 raw-answer pool;
see [`docs/EXPERIMENTS.md`](EXPERIMENTS.md) and
[`results/README.md`](../results/README.md) for the exact source runs and paths.

## Registry construction

The runtime metric and concept registry is stored in
[`src/verifiqa/policy/data/`](../src/verifiqa/policy/data/). The optional
registry-construction prompts are in
[`src/verifiqa/agent/registry_builder/`](../src/verifiqa/agent/registry_builder/),
with the source inventory in `metric_sources.json` and the retained source text
under `source_texts/`.

## Provider wrappers

Provider adapters transmit the formatted user prompt without adding a private
researcher-specific system message. Model names and recoverable configuration
metadata are recorded in the per-run manifests. Historical fields that were
not retained by an original run are explicitly null rather than reconstructed.
