"""At most two native questions to observe R24 graph-path coverage, separately."""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
ROUND=ROOT/'runs/gbfr_e2e_validation/r24'
SELECTION=ROOT/'data/validation/gbfr_r24_graph_coverage'

def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

async def main(check):
    if not load(ROOT/'runs/gpt56_sol_full_r19/control.json')['paused']:raise RuntimeError('Full must stay paused')
    if load(ROUND/'state.json')['status']!='finished':raise RuntimeError('R24 20-question validation must finish first')
    version=load(ROUND/'version.json')
    for name,digest in version['identity']['source_sha256'].items():
        if hashlib.sha256((ROUND/'source_snapshot/gbfr'/name).read_bytes()).hexdigest()!=digest:raise RuntimeError('R24 snapshot changed')
    sys.path.insert(0,str(ROUND/'source_snapshot'))
    from gbfr.engine import GBFR
    from gbfr.llm import ChatClient
    from gbfr.runner import preflight
    from gbfr.metrics import summarize
    cfg=load(ROUND/'configuration.json');graph,native=preflight(cfg)
    selected=[json.loads(x) for x in (SELECTION/'samples.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
    if not 1<=len(selected)<=2 or len({s['id'] for s in selected})!=len(selected):raise RuntimeError('Fixed scope must be 1 or 2 unique questions')
    lookup={s['id']:s for name in ['FinQA','TAT-QA'] for s in native[name]}
    if any(lookup.get(s['id'])!=s for s in selected):raise RuntimeError('Question/context/label differs from native')
    if check:print(json.dumps({'ready':True,'n':len(selected),'api_calls':0,'included_in_primary_metrics':False}));return
    out=ROUND/'graph_coverage'
    if out.exists():raise RuntimeError('Coverage already attempted; preserve it')
    out.mkdir();write(out/'selection.json',{'samples':selected,'selection_rationale':load(SELECTION/'selection.json'),'included_in_primary_metrics':False})
    client=ChatClient(cfg['backbones']['GPT-5.6 Sol'],out/'cache')
    model=GBFR(graph,client,cfg['execution_timeout'],evidence_policy=cfg['evidence_policy'])
    predictions=[]
    try:
        for s in selected:
            try:p=(await model.predict(s['question'],s['context'])).to_dict()
            except Exception as exc:p={'status':'error','value':None,'meta':{},'error_type':type(exc).__name__,'error':str(exc),'trace':getattr(exc,'gbfr_trace',{})}
            p.update(sample_id=s['id'],dataset=s['dataset']);predictions.append(p)
            with (out/'predictions.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(p,ensure_ascii=False)+'\n')
            print(json.dumps({'id':s['id'],'status':p['status'],'events':[e['operator'] for e in p['trace'].get('events',[])]},ensure_ascii=False),flush=True)
    finally:
        write(out/'api_usage.json',client.records);await client.close()
    from collections import Counter
    operators=Counter(e['operator'] for p in predictions for e in p['trace'].get('events',[]))
    result={'n':len(selected),'predictions':len(predictions),'included_in_primary_metrics':False,
        'operators':dict(operators),'fresh_operator_api_calls':dict(Counter(r['task'] for r in client.records if not r['cached'])),
        'diagnostic_metrics_only':summarize(selected,predictions,cfg['evaluation']['unspecified_decimals'],cfg['evaluation']['precision_policy']),
        'scope':'Native questions chosen for graph branch coverage by Q/D/graph only. Not a new performance evaluation or pooled with primary 20 questions.',
        'full_remains_paused':load(ROOT/'runs/gpt56_sol_full_r19/control.json')['paused']}
    write(out/'results.json',result);print(json.dumps(result,ensure_ascii=False),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();asyncio.run(main(args.check))
