# VeriFin

VeriFin verifies numerical answers about financial filings. It grounds the
required operands in filing data, checks that the calculation is authorized,
and uses SMT constraints to **accept**, **reject**, or **abstain**. The Python
package retains the historical import name `verifiqa` for compatibility.

This README describes the assembled public artifact: code, two frozen
evaluation datasets, per-question results, canonical SMT traces, notebooks,
figures, and checksum manifests. Exploratory runs, downloaded filing caches,
credentials, and local machine state are not included.

## Start here

| Goal | File or directory |
|---|---|
| Inspect the headline counts and metrics | [`results/paper_metrics.csv`](results/paper_metrics.csv) |
| Understand TA/FA/TR/FR/AB scoring | [`results/scoring_policy.json`](results/scoring_policy.json) |
| See every released run and its provenance | [`results/README.md`](results/README.md) |
| Audit every released file and checksum | [`ARTIFACT_MANIFEST.json`](ARTIFACT_MANIFEST.json), [`SHA256SUMS`](SHA256SUMS) |
| Recompute the paper tables | [`notebooks/verification_key_metrics.ipynb`](notebooks/verification_key_metrics.ipynb) |
| Inspect the full analysis | [`notebooks/agent_financebench_result_metrics.ipynb`](notebooks/agent_financebench_result_metrics.ipynb) |
| Reproduce experiment commands | [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md) |
| Inspect the exact prompts used by each stage | [`docs/PROMPTS.md`](docs/PROMPTS.md) |
| Review data provenance and licensing | [`docs/DATA.md`](docs/DATA.md) |

## Install and validate

Python 3.9 or newer is required. A fresh environment is recommended so the
`z3-solver` dependency is not shadowed by the unrelated package named `z3`.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,paper]"

# Unit and integration tests
python -m pytest -q

# Recompute every declared TA/FA/TR/FR/AB count from per-question files
python scripts/paper_scoring.py

# Verify all dataset, result, manifest, and SMT checksums in this clone
python scripts/build_publication_artifacts.py --check-release .
```

The command-line entry points are `verifiqa` for the general pipeline and
`verifiqa-agent` for the paper pipeline:

```bash
verifiqa --help
verifiqa-agent --help
```

## Datasets

Both headline denominators are fixed; no question is silently removed during
paper scoring.

| Dataset | Questions | Released input | Documentation | Terms |
|---|---:|---|---|---|
| XBRLFiling | 600 | `data/multicompany_provable/data/provable_calcrequired.jsonl` | [`datasets/xbrlbench-600/`](datasets/xbrlbench-600/) | Authors' annotation license pending |
| FinanceBench | 67 | `data/numerical_questions.jsonl` | [`datasets/financebench-67/`](datasets/financebench-67/) | CC BY-NC 4.0 |

XBRLFiling covers 15 subtotal metrics across income statements, balance
sheets, and cash-flow statements. Some historical notebook and figure labels
call this same frozen 600-question artifact “XBRLBench”; they do not denote a
second dataset.

FinanceBench-67 is the exact numeric subset used in the paper. Its dataset card
records the 67 identifiers, pinned upstream revision, selection metadata, and
document references. All 67 questions remain in the evaluation denominator.

The released JSONL files contain the benchmark question, evidence, answer, and
available computation provenance. Exact end-to-end retrieval reconstruction
also requires the filing/PDF and XBRL archives identified in the dataset cards;
those large third-party caches are not copied into this repository.

The filing/document registries shipped with the release are
[`datasets/xbrlbench-600/documents.jsonl`](datasets/xbrlbench-600/documents.jsonl)
and
[`datasets/financebench-67/documents.jsonl`](datasets/financebench-67/documents.jsonl).
They identify the filings or source documents used by the frozen questions.
The formula registry used by the verifier is separately versioned with the
implementation under [`src/verifiqa/policy/data/`](src/verifiqa/policy/data/).

## Code

The implementation lives under `src/verifiqa/`:

| Path | Responsibility |
|---|---|
| `src/verifiqa/agent/` | Paper pipeline orchestration and claim construction |
| `src/verifiqa/retrieval/` | Role-aware evidence planning and table-row retrieval |
| `src/verifiqa/verification/` | XBRL grounding, deterministic SMT generation, sanitization, and solving |
| `src/verifiqa/policy/` | Authorized formula registry and source checks |
| `src/verifiqa/formalization/` | Verification-plan and certificate validation |
| `src/verifiqa/eval/` | Outcome accounting and evaluation reports |

Important paper-facing scripts are:

| Script | Purpose |
|---|---|
| `scripts/baselines.py` | Direct-LLM, LLM-judge, judge-with-formula, and PoT baselines |
| `scripts/paper_scoring.py` | Canonical candidate-specific TA/FA/TR/FR/AB scorer |
| `scripts/plot_acceptance_outcomes.py` | Main baseline-versus-VeriFin result figure |
| `scripts/safety_coverage_tolerance.py` | Optional exact replay of stored SMT obligations under tolerance changes |
| `scripts/build_publication_artifacts.py` | Locked dataset/result/SMT bundle validation |
| `scripts/build_public_release.py` | Anonymous allowlisted release assembly |

The complete script index is in [`scripts/README.md`](scripts/README.md).
All paper-facing prompt templates are indexed in
[`docs/PROMPTS.md`](docs/PROMPTS.md); the linked source constants are the
executable prompts, not paraphrases prepared only for documentation.

## Results

The release contains 14 VeriFin result directories, eight one-pool baseline
results, 22 generated run manifests, and 5,202 status-matched SMT traces.

```text
results/
├── README.md                    # complete run inventory and caveats
├── paper_metrics.csv            # frozen paper counts and derived metrics
├── scoring_policy.json          # metric and outcome definitions
├── manual_adjudications.json    # candidate-specific reviewed targets
├── onepool/                     # eight shared-raw-answer baseline runs
├── latest/                      # selected final model runs
└── <run>/
    ├── results.jsonl            # one record per benchmark question
    ├── summary.json             # source run summary, when applicable
    ├── run_manifest.json        # dataset/model/file provenance and hashes
    └── smt/<id>_<status>.smt2   # exact released verification obligation
```

The headline baselines use the same frozen Claude Haiku 4.5 `raw_answer` text
for every question. Parsing remains part of each method: baseline loading
recovered a numeric value from seven XBRLFiling and six FinanceBench responses
whose source VeriFin records stored a null `claimed_value`. The comparison is
therefore a shared **raw-answer** pool, not a claim that every parsed field is
identical. See [`results/README.md`](results/README.md) for exact paths, hashes,
counts, fallbacks, and known provenance gaps.

Paper metrics use:

- precision = `TA / (TA + FA)`;
- decision accuracy = `(TA + TR) / (TA + FA + TR + FR)`;
- coverage = `(TA + FA + TR + FR) / N`; and
- abstention = `AB / N`.

A zero observed FA count is an empirical result on a finite benchmark, not a
universal guarantee.

## Notebooks and figures

The public notebooks have their execution outputs cleared deliberately. After
installing the `paper` dependencies, they can be executed against the released
JSONL files without contacting a model provider:

- `notebooks/verification_key_metrics.ipynb` — compact metric audit;
- `notebooks/visualizations.ipynb` — paper visualizations; and
- `notebooks/agent_financebench_result_metrics.ipynb` — full analysis history.

The full notebook reads the frozen tolerance-sweep CSV by default. Re-solving
all SMT obligations is an explicit, separate operation; it is never triggered
merely by opening or executing the publication notebook.

Curated vector figures and high-resolution previews are under `figures/`.
Notably:

- `acceptance_outcomes.{pdf,svg,png}` compares baselines with VeriFin on both
  complete denominators;
- `risk_coverage_operating_points.{pdf,svg,png}` shows observed coverage and
  false-accept risk; and
- `xbrl_error_profile_by_statement_family.{pdf,svg,png}` breaks XBRLFiling
  errors down by statement family and answer model.

## Repository structure

| Path | Contents |
|---|---|
| `src/` | Installable Python package |
| `scripts/` | Data, experiment, scoring, plotting, and release utilities |
| `tests/` | Unit, integration, scoring, and fixture tests |
| `configs/` | Example run configurations |
| `data/` | The two hash-pinned paper inputs plus small synthetic test fixtures |
| `datasets/` | Dataset cards, notices, selection metadata, and document manifests |
| `results/` | Declared per-question results, summaries, SMT, and run manifests |
| `notebooks/` | Cleared, executable analysis notebooks |
| `figures/` | Curated paper figures and plotted data |
| `examples/` | Small inspectable verification trace |
| `reproducibility/` | Artifact and metric conventions |
| `docs/` | Data, experiment, anonymity, and publication documentation |
| `.github/workflows/` | Continuous-integration checks |

## Recompute versus rerun

Everything needed to **recompute the published metrics and figures** is in this
release. A full **model rerun** additionally requires a configured model
provider or local vLLM endpoint and, for retrieval experiments, the external
filing/XBRL archives documented in the dataset cards. The exact commands are in
[`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md).

Keep provider credentials in a local `.env` file, which is ignored. SEC-facing
download scripts require `SEC_USER_AGENT` with a real project name and monitored
contact address. Never commit either value.

## Scope and limitations

- Coverage depends on retrievable facts, context resolution, and available
  calculation authority.
- Abstention means the verifier did not establish all conditions needed for a
  decision; it is not an incorrect-answer judgment.
- No auditable FinanceBench GPT-5.5 result artifact is present, so that entry is
  reported as unavailable rather than inferred or manually filled.
- Fin-o1's immutable checkpoint identity is not embedded in its historical
  artifacts; the release therefore uses the size-neutral `Fin-o1` label.

## Citation and licensing

`CITATION.cff` is intentionally anonymous for review and must be updated after
deanonymization. FinanceBench-67 retains its upstream CC BY-NC 4.0 terms. A
software license and a license for the authors' XBRLFiling questions and
annotations must be selected before public redistribution.

Maintainers creating a new anonymous snapshot from the private research tree
must follow [`docs/PUBLICATION.md`](docs/PUBLICATION.md). The exporter uses an
explicit allowlist, refuses to overwrite existing destinations, clears notebook
outputs, verifies ID sets and hashes, selects one current SMT trace per result
row, and scans the copy for secrets and personal paths.
