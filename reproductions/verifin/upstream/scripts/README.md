# Script index

Scripts remain at one level because several derive the repository root from
their current path. This index supplies organization without breaking those
assumptions.

## Data acquisition and construction

- `build_apple_two_year_financebench.py`
- `build_filingcalc_doclinks.py`
- `build_multicompany_provable.py`
- `download_calculation_linkbases.py`
- `download_edgar_missing.py`
- `download_finqa_xbrl.py`

All SEC-facing scripts require `SEC_USER_AGENT` with a real contact address.

## Experiments and scoring

- `baselines.py`
- `compute_agent_results.py`
- `model_comparison.py`
- `paper_scoring.py` (canonical published TA/FA/TR/FR/AB scorer)
- `run_model_sweep.py`
- `run_rag_ablation.sh`
- `safety_coverage_tolerance.py`

## Diagnostics and prototypes

- `diagnose_retrieval.py`
- `diagnose_retrieval_light.py`
- `nongaap_reconciliation_prototype.py`
- `smoke_fino1.py`

## Figures and notebook maintenance

- `plot_acceptance_outcomes.py`
- `plot_six_model_accuracy_heatmap.py`
- `update_financebench_notebook_scoring.py`
- `viz_embeddings.py`

Plotting scripts should read declared result files and write vector output plus a
high-resolution preview. One-off notebook mutators and local path-repair helpers
remain preserved in the working research tree but are excluded from the public
snapshot.

## Publication assembly

- `build_publication_artifacts.py` validates and copies only the two locked
  datasets, declared final/baseline results, and one current SMT per result row;
  it also generates one provenance manifest per declared run directory.
- `build_public_release.py` assembles the anonymous code/notebook snapshot and
  embeds that locked artifact bundle in one step.

Both builders preserve all source files, refuse overwrites, and generate or
verify SHA-256 inventories. They never recursively publish the private `data/`
or `results/` trees.
