# Reproducibility bundle

This directory defines the metadata and scoring rules for every result cited in
the paper. The publication builder adds the declared per-question outputs and
canonical SMT traces from the final local runs; exploratory and stale runs stay
outside the snapshot.

The publication builder emits `run_manifest.json` for every declared VeriFin
run and baseline. Each manifest records the dataset and file hashes, canonical
SMT tree where applicable, scoring policy, relative source path, and all model
or method provenance recoverable from the artifacts. Unrecoverable historical
fields are explicit `null` values with a stated metadata gap; they are never
guessed. Do not report a table or figure from a directory that lacks a manifest
and stable per-question identifiers.

## Outcome accounting

For a candidate answer whose correctness is known from the benchmark:

| Bucket | Candidate correctness | Verifier decision |
|---|---|---|
| `TA` | correct | accept |
| `FA` | wrong | accept |
| `TC` | wrong | reject/catch |
| `FR` | correct | reject |
| `ABST` | either | abstain/no decision |

Acceptance precision is `TA / (TA + FA)`. Wrong-claim catch rate is
`TC / (TC + FA)`. Coverage denominators and the treatment of missing or
non-numeric candidates must be stated explicitly for each dataset. Counts are
the canonical values; percentages should be recomputed from those counts.

## Published release contents

- machine-readable run manifest, including explicit historical metadata gaps;
- complete per-question outputs keyed by benchmark ID;
- aggregate counts generated from those outcomes;
- source-data and artifact SHA-256 hashes;
- exact plotting/scoring command; and
- one status-matched SMT trace per result row; and
- a generated checksum index covering every dataset, result, summary, and SMT
  file.

The source configuration is `publication_artifacts.json`. It freezes the two
dataset hashes, 11 locally available final answer-model runs, three
notebook-linked ablations, eight headline baselines, row counts, and canonical
trace counts. There is no local FinanceBench GPT-5.5
run; public tables must show that entry as unavailable until its per-question
artifact is supplied.
