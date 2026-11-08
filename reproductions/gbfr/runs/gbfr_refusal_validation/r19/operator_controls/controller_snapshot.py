"""Positive API controls, separate from every benchmark score."""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
CASES=[
    {'id':'price-only-supported','question':"What is Orion Labs' price return excluding dividends from 2022 to 2023, as a percentage?",
     'context':"Orion Labs actual share prices were USD 20 per share on December 31, 2022 and USD 24 per share on December 31, 2023. A separate wealth index including reinvested dividends was 100 and 130 on those dates, respectively.",
     'answer':'20%','unanswerable':False},
    {'id':'gross-margin-supported','question':"What was Orion Labs' Gross Margin in 2023, as a percentage?",
     'context':'Orion Labs 2023 Revenue: USD 120 million. Cost of goods sold: USD 90 million.',
     'answer':'25%','unanswerable':False},
    {'id':'series-label-supported','question':'What was the return on an investment in Lyra Corporation from 2021 to 2022, as a percentage?',
     'context':'|  | 2021 | 2022 |\n| --- | --- | --- |\n| Lyra Corporation | 80 | 100 |\n| Broad Market Index | 120 | 132 |',
     'answer':'25%','unanswerable':False},
]

async def main(round_name):
    version=ROOT/'runs/gbfr_refusal_validation'/round_name
    sys.path.insert(0,str(version/'source_snapshot'))
    from gbfr.engine import GBFR
    from gbfr.graph import MetricGraph
    from gbfr.llm import ChatClient
    from gbfr.metrics import correct
    cfg=json.loads((version/'regression/configuration.json').read_text(encoding='utf-8'))
    out=version/'operator_controls';out.mkdir(parents=True,exist_ok=True)
    c=ChatClient(cfg['backbones']['GPT-5.6 Sol'],Path(cfg['cache_dir'])/'GPT-5.6 Sol')
    model=GBFR(MetricGraph.load(cfg['graph']),c,cfg['execution_timeout'],evidence_policy=cfg['evidence_policy'])
    results=[]
    try:
        for s in CASES:
            try:p=(await model.predict(s['question'],s['context'])).to_dict()
            except Exception as e:p={'status':'error','value':None,'error':str(e),'trace':getattr(e,'gbfr_trace',{})}
            results.append({'id':s['id'],'prediction':p,'expected':s['answer'],'passed':correct(p,s,2,'reference_display')})
            (out/'results.json').write_text(json.dumps({'benchmark_examples':0,'synthetic_controls':results,'all_passed':all(x['passed'] for x in results),
                'controller_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            print(json.dumps({'id':s['id'],'status':p['status'],'value':p.get('value'),'passed':results[-1]['passed']},ensure_ascii=False),flush=True)
    finally:
        (out/'api_usage.json').write_text(json.dumps(c.records,indent=2)+'\n',encoding='utf-8');await c.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--round',default='r8');args=p.parse_args()
    if not args.round.replace('_','').replace('-','').isalnum():p.error('Invalid round name')
    asyncio.run(main(args.round))
