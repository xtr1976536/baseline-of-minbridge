# Publication checklist

The full private research worktree must not be pushed directly to a public
remote. Its Git object database retains historical credentials and author
identities even when the current files look clean. These instructions are for
maintainers; a public clone created by the allowlisted builder has no inherited
history.

## Before creating a release

1. Revoke and rotate the historically exposed Anthropic credential. Rotate any
   other credential that was stored alongside it or may have been copied.
2. Confirm the intended software license and a separate XBRLBench dataset
   license. Retain FinanceBench-67's CC BY-NC 4.0 notice.
3. Decide whether the repository must remain anonymous for review. If so, use a
   neutral Git host account, remote name, commit author, issue links, and
   citation metadata.
4. Run the full test suite and regenerate final summaries/figures from the
   declared final runs.

## Build an allowlisted snapshot

From the working repository:

```bash
python scripts/build_public_release.py --output ../verifin-public
```

The destination must not already exist. The builder copies only the source paths
in `publication_manifest.json`, adds only the datasets and result runs declared
in `publication_artifacts.json`, selects canonical SMT by result ID and current
status, applies publication-safe notebook handling, and runs a conservative
scan. It does not delete, move, or edit anything in the working repository.

Inspect the result:

```bash
cd ../verifin-public
find . -type f | sort
python scripts/build_public_release.py --check .
python -m pytest -q
python -m build
```

Then create fresh history using a neutral identity appropriate to the venue:

```bash
git init
git add .
git status --short
git ls-files --error-unmatch \
  data/numerical_questions.jsonl \
  data/multicompany_provable/data/provable_calcrequired.jsonl \
  results/paper_metrics.csv \
  results/onepool/xbrl_none/results.jsonl
git commit -m "Initial artifact release"
```

The exporter removes the private worktree's top-level `/data/` and `/results/`
ignore rules from the copied `.gitignore`. The `git ls-files` check above is a
release gate: if any path is absent, do not commit or push the snapshot.

Do not copy `.git`, use `git push --mirror`, or reuse the current remote. A new
commit is essential: deleting a secret in a later commit does not remove it from
older objects.

## Release gate

- credential rotation confirmed;
- no `.env`, local agent settings, caches, virtual environments, undeclared
  result runs, or unlicensed datasets in the snapshot;
- no personal paths, contact addresses, notebook execution state, or identifying
  PDF metadata when anonymity is required;
- no file near GitHub's per-file size limit;
- tests, wheel build, and CLI smoke checks pass in a fresh environment;
- metric tables and figures trace to declared run IDs and hashes;
- all 22 declared run and baseline directories contain generated
  `run_manifest.json` files, with unavailable historical provenance explicit;
- all 600/67 dataset IDs match every corresponding result run, all 5,202
  declared SMT files are present, and stale status variants are absent;
- the missing FinanceBench GPT-5.5 run is disclosed rather than reconstructed
  from manually entered aggregate counts;
- Fin-o1's exact checkpoint identity is recovered and recorded, or the release
  and paper use the explicit identity-pending label;
- license, dataset attribution, and post-review citation metadata finalized.
