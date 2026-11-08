"""Freeze the authorized 5,089-example run; contains no credentials."""
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

from gbfr.data import sha256, write_json
from gbfr.runner import preflight, resolve_paths

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'configs/gpt56_sol.json'
config = resolve_paths(CONFIG)
graph, datasets = preflight(config)
out = Path(config['output_dir'])
if (out / 'full_run_manifest.json').exists():
    raise SystemExit('Run already frozen; do not overwrite its identity.')
if sum(map(len, datasets.values())) != 5089:
    raise SystemExit('Wrong full-run denominator.')
snapshot = out / 'source_snapshot'
snapshot.mkdir(parents=True, exist_ok=False)
shutil.copytree(ROOT / 'gbfr', snapshot / 'gbfr', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
write_json(snapshot / 'configs/run.json', config)
shutil.copy2(CONFIG, out / 'configuration_snapshot.json')
source_hashes = {p.relative_to(ROOT).as_posix(): sha256(p) for p in sorted((ROOT/'gbfr').rglob('*'))
                 if p.suffix in {'.py','.txt'} and '__pycache__' not in p.parts}
for name, digest in source_hashes.items():
    if sha256(snapshot / name) != digest:
        raise SystemExit('Source snapshot mismatch: '+name)
manifest = {
    'frozen_at': datetime.now(timezone.utc).isoformat(),
    'scope': 'all frozen 5089 examples, four datasets, GPT-5.6 Sol',
    'model': 'gpt-5.6-sol', 'configuration_sha256': sha256(CONFIG),
    'resolved_configuration_sha256': sha256(snapshot/'configs/run.json'),
    'source_snapshot': str(snapshot), 'source_sha256': source_hashes,
    'asset_lock_sha256': sha256(config['asset_lock']), 'graph_sha256': sha256(config['graph']),
    'datasets': {name: {'n':len(rows), 'original':sum(not s['unanswerable'] for s in rows),
        'counterfactual':sum(s['unanswerable'] for s in rows),
        'sha256':sha256(Path(config['data_dir'])/(name+'.jsonl'))} for name,rows in datasets.items()},
    'example_concurrency':config['example_concurrency'],
    'max_api_concurrency':config['backbones']['GPT-5.6 Sol']['concurrency'],
    'previous_attempt':'runs/gpt56_sol (aborted; excluded)',
    'restart_reason':'General UTF-8 execution and verbatim Chinese/table evidence grounding fixes, verified on synthetic cases; no dataset or graph changes based on predictions.',
    'failure_policy':'Stop on auth/billing rejection or three consecutive systemic API failures; preserve journals and full denominators. Never count technical errors as abstentions.',
    'test_evidence':'136 tests passed and one new test fixture failed before its local-variable fix; all 137 tests rerun before launch.',
}
write_json(out/'full_run_manifest.json', manifest)
print(json.dumps({'frozen':True,'n':5089,'snapshot':str(snapshot)}, ensure_ascii=False))
