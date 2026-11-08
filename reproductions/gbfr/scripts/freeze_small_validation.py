"""Freeze unseen, hash-selected main-model validation cases before repairs."""
import asyncio
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'runs/gpt56_sol_full'
sys.path.insert(0,str(OLD/'source_snapshot'))
from gbfr.engine import GBFR
from gbfr.runner import preflight,resolve_paths
from gbfr.types import dumps

TARGET=ROOT/'data/validation/gbfr_v3'
SEED='gbfr-paper-validation-20261107-v3'

class Captured(Exception):
    def __init__(self,prompt):self.prompt=prompt
class CaptureClient:
    async def json(self,task,prompt):
        if task!='OQA':raise RuntimeError('No API allowed in validation selection')
        raise Captured(prompt)

async def main():
    if (TARGET/'manifest.json').exists():raise SystemExit('Validation is already frozen')
    config=resolve_paths(OLD/'source_snapshot/configs/run.json')
    graph,datasets=preflight(config)
    model=GBFR(graph,CaptureClient())
    backend=config['backbones']['GPT-5.6 Sol']
    seen=set()
    for p in OLD.rglob('predictions.jsonl'):
        for line in p.read_text(encoding='utf-8').splitlines():
            if line.strip():seen.add(json.loads(line)['sample_id'])
    selected={};audits={}
    for name in ['FinQA','TAT-QA']:
        eligible=[];cached=0
        for sample in datasets[name]:
            if sample['id'] in seen:continue
            try:await model.predict(sample['question'],sample['context'])
            except Captured as exc:prompt=exc.prompt
            params=dict(backend.get('parameters',{}))
            if backend.get('json_response_format'):params['response_format']=backend['json_response_format']
            messages=[{'role':'user','content':prompt}]
            if backend.get('system_message'):messages.insert(0,{'role':'system','content':backend['system_message']})
            body={'model':backend['model'],'messages':messages,'stream':False,'n':1,**params}
            key=hashlib.sha256(dumps({'endpoint':backend['base_url'].rstrip('/'),'body':body}).encode()).hexdigest()
            if (Path(config['cache_dir'])/'GPT-5.6 Sol'/(key+'.json')).exists():cached+=1;continue
            eligible.append(sample)
        order=lambda s:hashlib.sha256((SEED+'|'+name+'|'+s['id']).encode()).hexdigest()
        positive=sorted((s for s in eligible if not s['unanswerable']),key=order)
        negative=sorted((s for s in eligible if s['unanswerable']),key=order)
        if len(positive)<30 or len(negative)<3:raise RuntimeError('Not enough untouched examples')
        chosen=positive[:30]+negative[:3]
        selected[name]=chosen
        audits[name]={'eligible_positive':len(positive),'eligible_counterfactual':len(negative),'excluded_cached_OQA':cached,
                      'selected_positive':30,'selected_counterfactual':3,'sample_ids':[s['id'] for s in chosen]}
        print(dumps({'dataset':name,'selected':33,'untouched_pool':len(eligible)}),flush=True)
    TARGET.mkdir(parents=True,exist_ok=False)
    files={}
    for name,samples in selected.items():
        path=TARGET/(name+'.jsonl')
        path.write_text(''.join(dumps(s)+'\n' for s in samples),encoding='utf-8')
        files[name]={'n':len(samples),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    manifest={'frozen_at':datetime.now(timezone.utc).isoformat(),'selection_seed':SEED,'total':66,
        'rule':'SHA-256 order within previously unprocessed and uncached-OQA examples; 30 originals plus 3 counterfactuals per dataset. No selection by answer value, difficulty or model outcome.',
        'datasets':files,'selection_audit':audits,'api_requests_during_selection':0,
        'full_run_authorized':False,'validation_gold_or_questions_changed':False,
        'reference':{'FinQA':{'total_accuracy':84.98,'abstention_accuracy':98.80},'TAT-QA':{'total_accuracy':95.75,'abstention_accuracy':96.69}},
        'pre_fix_source_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'gbfr').rglob('*') if p.suffix in {'.py','.txt'} and '__pycache__' not in p.parts}}
    (TARGET/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(dumps({'frozen':True,'n':66,'manifest':str(TARGET/'manifest.json')}))

if __name__=='__main__':asyncio.run(main())
