# Data and result policy

The working repository contains downloaded filings, derived XBRL artifacts,
benchmark inputs, model outputs, solver traces, and draft figures. These files
are valuable research state, but only a hash-pinned subset belongs in the public
paper artifact.

## Public source release

The public snapshot includes code, tests, configurations, documentation,
notebooks with cleared outputs, curated figures, and the following declared
paper assets:

- the frozen 600-row XBRLBench JSONL;
- the exact 67-row FinanceBench evaluation subset;
- the 11 final answer-model runs and three notebook-linked ablations that exist
  locally, with one canonical SMT trace per result row; and
- the eight baseline result files used in the headline comparison.

All other files under the private `data/`, `results/`, `runs/`, and `artifacts/`
trees remain excluded. The exporter validates this declaration instead of
copying either directory recursively. This keeps third-party data within its
license boundary, makes the snapshot reviewable, and prevents transient traces
or local machine state from leaking.

## Local directory meanings

| Directory | Contents | Release policy |
|---|---|---|
| `data/` | Benchmark inputs, SEC filings, XBRL, and derived corpora | Publish only the two declared JSONL inputs; archive larger frozen inputs separately |
| `results/` | Per-question verdicts, diagnostics, summaries, and SMT | Publish only declared paper runs and canonical status-matched SMT files |
| `runs/` | General-pipeline outputs | Generated; exclude |
| `artifacts/` | Caches, downloads, embeddings, and demo state | Generated or reacquired; exclude |
| `figures/` | Final and draft plots | Publish only cited, reproducible figures |

## SEC access and XBRL provenance

SEC download scripts require the `SEC_USER_AGENT` environment variable. Set it
to a descriptive application name plus a monitored email address, respect the
request pacing in each script, and comply with current SEC access guidance. Do
not hard-code a personal address into source code.

The XBRLBench records are derived from issuer filings and XBRL facts available
through SEC EDGAR. The public JSONL contains the question, rendered evidence,
answer, and computation provenance. Exact end-to-end fact-binding reproduction
also requires the pinned XBRL/companyfacts archive described in the dataset
card. Publish that as a separately versioned, checksummed release asset rather
than copying the full local cache.

## Dataset-specific terms

FinanceBench-67 is an unmodified subset of the 150-example FinanceBench public
sample and remains under CC BY-NC 4.0. Its notice, upstream citation and pinned
revision, 67 IDs, source hashes, and 55-document metadata projection travel
with the data. The historical reason those 67 IDs were selected is not recorded
in this worktree; the release describes it only as the fixed evaluation subset
used in the paper.

XBRLBench's 600 IDs are unique and complete, and every row carries one evidence
record plus computation provenance. A separate license for the authors'
questions and annotations is still required. SEC reuse guidance does not choose
a license for that added research content.

## Releasing results

The public result bundle contains, for each declared final run:

- dataset and split identifier;
- an honest model-identity/provenance status;
- exact source path and content hashes;
- all per-question outputs and aggregate source summary;
- a per-run manifest with hashes and explicit provenance gaps;
- the published answer-correctness scoring policy; and
- one non-empty `smt/<id>_<status>.smt2` file for every result row.

SMT directories are not copied recursively: some local folders preserve stale
status-named traces. Selection is driven by the current `results.jsonl` row, and
the exporter fails if that exact trace is absent or if its embedded SMT differs
on a decided row. Existing `summary.json` files report internal solver-label
metrics; paper answer-correctness metrics are generated separately under the
published scoring policy.

No FinanceBench GPT-5.5 artifact exists in the audited repository. A manually
entered table value is not a substitute for a publishable per-question run.
