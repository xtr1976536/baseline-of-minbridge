"""Read-only operational progress for the frozen GPT-5.6 Sol run (no API)."""
from collections import Counter
from datetime import datetime,timezone
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
config=json.loads((ROOT/'configs/gpt56_sol.json').read_text(encoding='utf-8'))
OUT=ROOT/config['output_dir']
manifest=json.loads((OUT/'full_run_manifest.json').read_text(encoding='utf-8'))
parallel_path=OUT/'scheduling/parallel_manifest.json'
parallel=json.loads(parallel_path.read_text(encoding='utf-8')) if parallel_path.exists() else None
scope_path=ROOT/'configs/gpt56_sol_scope.json'
selected=json.loads(scope_path.read_text(encoding='utf-8'))['datasets'] if scope_path.exists() else list(manifest['datasets'])
datasets={}
for name,spec in manifest['datasets'].items():
    if name not in selected:continue
    paths=([Path(s['journal']) for s in parallel['shards'] if s['dataset']==name] if parallel
           else [OUT/'GPT-5.6 Sol'/name/'predictions.jsonl'])
    statuses,errors=Counter(),Counter()
    predictions={}
    for path in paths:
      if path.exists():
        with path.open(encoding='utf-8') as stream:
            for line in stream:
                try:r=json.loads(line)
                except json.JSONDecodeError:continue  # An in-flight final append.
                if r['sample_id'] in predictions:raise RuntimeError('Duplicate scheduled prediction')
                predictions[r['sample_id']]=r
    for r in predictions.values():
        statuses[r['status']]+=1
        if r['status']=='error':errors[r.get('error','unknown')]+=1
    datasets[name]={'total':spec['n'],'completed':sum(statuses.values()),'statuses':dict(statuses),'errors':dict(errors)}
result={'checked_at':datetime.now(timezone.utc).isoformat(),'datasets':datasets,
        'completed':sum(v['completed'] for v in datasets.values()),'total':sum(v['total'] for v in datasets.values())}
state_path=OUT/'process_state.json'
if state_path.exists():
    try:result['process_state']=json.loads(state_path.read_text(encoding='utf-8'))
    except json.JSONDecodeError:result['process_state_pending_write']=True
path=OUT/('progress_snapshot.json' if len(selected)==len(manifest['datasets']) else '_'.join(selected)+'_progress.json')
path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
