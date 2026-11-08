"""Fetch an immutable source snapshot, then audit it. No upstream code is run."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gbfr.data import fetch_official, prepare, write_json
from gbfr.reconciliation import reconcile_datasets
from gbfr.source_recovery import source_audit
from gbfr.build_graph import build_graph
from gbfr.adjustments import prepare_main
from gbfr.runner import lock_assets, preflight, resolve_paths

REPOSITORY = "https://github.com/aolaoban/Graph-Bounded_Financial_Reasoning.git"
COMMIT = "e1c1704eacfb8a3a522999d4a0ea726189bf5482"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Require the existing source snapshot; no network")
    args = parser.parse_args()
    destination = ROOT / "research" / "upstream"
    if not destination.exists():
        if args.offline:
            parser.error("Missing research/upstream")
        destination.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--no-checkout", REPOSITORY, str(destination)], check=True)
        subprocess.run(["git", "-C", str(destination), "checkout", "--detach", COMMIT], check=True)
    revision = subprocess.check_output(["git", "-C", str(destination), "rev-parse", "HEAD"], text=True).strip()
    if revision != COMMIT:
        parser.error("Existing checkout differs from pinned source; no files were changed")
    official = ROOT / "data" / "raw" / "official"
    fetch_official(official, offline=args.offline)
    source_reviews = source_audit(destination, ROOT / "data/raw", ROOT / "research/reconciliation", offline=args.offline)
    recovered_dir = ROOT / "data" / "reconciled"
    recovered = reconcile_datasets(destination, official, ROOT / "research/history", recovered_dir, offline=args.offline)
    write_json(ROOT / "research/reconciliation/dataset_recovery.json", recovered)
    manifest = prepare(destination, ROOT / "data" / "processed", official, recovered_dir, source_reviews)
    write_json(ROOT / "research" / "asset_audit.json", manifest)
    graph = build_graph(destination / 'knowledge_base/term_en_final.json', ROOT / 'data/assets/fmkg.reconstructed.json', ROOT / 'research/reconstruction')
    main = prepare_main(ROOT, ROOT / 'data/processed', ROOT / 'data/main', ROOT / 'research/reconstruction')
    config = resolve_paths(ROOT / 'configs/main.json')
    lock_assets(config, 'User-authorized paper-method reconstruction; deterministic source-only DAG, uniform scalar-target filtering and two documented arithmetic gold corrections. See docs/RECONSTRUCTION.md.')
    checked, datasets = preflight(config)
    print('Main assets ready; no API call made. Graph:', checked.stats())
    print('Frozen dataset sizes:', {name: len(rows) for name, rows in datasets.items()})
    print('This is a paper-method reconstruction, not the unpublished exact FMKG snapshot.')


if __name__ == "__main__":
    main()
