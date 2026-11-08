# Notebooks

The notebooks are analysis companions, not the source of truth for metrics.
Final values should be recomputed from declared result files with the scripts in
`scripts/`. In particular, `scripts/paper_scoring.py` is the canonical scorer
for TA/FA/TR/FR/AB. It applies the published candidate-specific FinanceBench
adjudications; no question ID is treated as automatically correct.

The public-release builder clears cell outputs and execution counts and replaces
machine-specific kernel metadata in the exported copies. This prevents stale
results, local paths, warnings, and embedded display payloads from leaking while
keeping every analysis cell reproducible. Re-run the exported notebooks from the
repository root after obtaining the required data and result bundles.
