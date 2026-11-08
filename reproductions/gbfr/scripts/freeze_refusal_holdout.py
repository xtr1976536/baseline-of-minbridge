"""Freeze a small unseen refusal holdout before the next implementation change."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from gbfr.runner import preflight
from gbfr.types import dumps

TARGET=ROOT/'data/validation/gbfr_refusal_holdout_v1'
SEED='gbfr-refusal-holdout-20261107-v1'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    if (TARGET/'manifest.json').exists():raise SystemExit('Holdout already frozen; never reselect after outcomes')
    cfg=json.loads((ROOT/'configs/gpt56_sol.json').read_text(encoding='utf-8'))
    for key in ['graph','asset_lock','data_dir','output_dir','cache_dir']:cfg[key]=str((ROOT/cfg[key]).resolve())
    _,datasets=preflight(cfg)
    seen=set();journals=[]
    for folder in ['gpt56_sol','gpt56_sol_full','gbfr_v3_validation']:
        for p in (ROOT/'runs'/folder).rglob('predictions.jsonl'):
            for line in p.read_text(encoding='utf-8').splitlines():
                if line.strip():seen.add(json.loads(line)['sample_id'])
            journals.append(p.relative_to(ROOT).as_posix())
    old=json.loads((ROOT/'data/validation/gbfr_v3/manifest.json').read_text(encoding='utf-8'))
    for entry in old['selection_audit'].values():seen.update(entry['sample_ids'])
    TARGET.mkdir(parents=True,exist_ok=False)
    manifest={'frozen_at':datetime.now(timezone.utc).isoformat(),'selection_seed':SEED,'total':30,
        'purpose':'Unseen refusal accuracy with answerable controls; not a replacement for the original 66-case regression.',
        'rule':'SHA-256 order within unprocessed strata, 10 counterfactuals plus 5 original controls per dataset. No selection by gold value, difficulty or outcome.',
        'api_calls_during_selection':0,'full_run_authorized':False,'inputs_and_gold_changed':False,
        'selection_journals':journals,'datasets':{},
        'pre_change_source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'gbfr').rglob('*') if p.suffix in {'.py','.txt'} and '__pycache__' not in p.parts}}
    for name in ['FinQA','TAT-QA']:
        eligible=[s for s in datasets[name] if s['id'] not in seen]
        order=lambda s:hashlib.sha256((SEED+'|'+name+'|'+s['id']).encode()).hexdigest()
        positives=sorted((s for s in eligible if not s['unanswerable']),key=order)
        negatives=sorted((s for s in eligible if s['unanswerable']),key=order)
        if len(positives)<5 or len(negatives)<10:raise RuntimeError('Insufficient unseen cases')
        chosen=positives[:5]+negatives[:10]
        p=TARGET/(name+'.jsonl');p.write_text(''.join(dumps(s)+'\n' for s in chosen),encoding='utf-8')
        manifest['datasets'][name]={'n':15,'original':5,'counterfactual':10,'sha256':sha(p),
            'eligible_original':len(positives),'eligible_counterfactual':len(negatives),'sample_ids':[s['id'] for s in chosen]}
    (TARGET/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(dumps({'frozen':True,'n':30,'datasets':{n:{k:v[k] for k in ['original','counterfactual','eligible_original','eligible_counterfactual']} for n,v in manifest['datasets'].items()},'api_calls':0}))

if __name__=='__main__':main()
