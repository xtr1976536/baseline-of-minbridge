"""Small REAL API integration check on synthetic cases, not benchmark scores."""
import argparse
import asyncio
from dataclasses import asdict
from datetime import datetime,timezone
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from gbfr.data import sha256,write_json
from gbfr.engine import GBFR
from gbfr.llm import ChatClient
from gbfr.runner import preflight,resolve_paths


async def run(config_path):
    config=resolve_paths(config_path)
    graph,_=preflight(config)
    if len(config['backbones'])!=1:
        raise ValueError('API smoke requires one explicitly selected backbone')
    name,backbone=next(iter(config['backbones'].items()))
    now=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=ROOT/'runs/api_smoke'/backbone['model']/now
    client=ChatClient(backbone,Path(config['cache_dir'])/name)
    model=GBFR(graph,client,config.get('execution_timeout',5))
    cases=[
        {'id':'paper-style-roe-multihop','question':"Compute Company A's Return on Equity (ROE) for fiscal year 2024 as a percentage, rounded to two decimal places. Use average equity.",
         'context':"Company A annual report. All financial amounts are in USD millions. Net Profit for fiscal year 2024: 500. Total Equity at the end of fiscal year 2024: 2500. Total Equity at the end of fiscal year 2023: 2200. No other values are reported.",
         'expected':'answered','expected_percent':500/2350*100},
        {'id':'atomic-time-mismatch','question':"What was Company A's Stock Price in 2024, in USD?",
         'context':"Company A's Stock Price in 2023 was USD 25. No stock price for any other year is provided.",
         'expected':'abstained'},
    ]
    results=[]
    try:
        for case in cases:
            print('START '+case['id'],flush=True)
            try:
                prediction=(await model.predict(case['question'],case['context'])).to_dict()
                passed=prediction['status']==case['expected']
                if passed and case['expected']=='answered':
                    from gbfr.metrics import normalized
                    value,dimension=normalized(prediction['value'],prediction['meta'])
                    passed=dimension[1]=='ratio' and abs(value*100-case['expected_percent'])<=.005
                    events=prediction['trace'].get('events',[])
                    passed=passed and sum(e.get('operator')=='OMD' for e in events)>=2
                result={'case':case,'prediction':prediction,'passed':passed}
            except Exception as exc:
                result={'case':case,'passed':False,'error_type':type(exc).__name__,'error':str(exc),'trace':getattr(exc,'gbfr_trace',{})}
            results.append(result)
            write_json(out/(case['id']+'.json'),result)
            print(json.dumps({'case':case['id'],'passed':result['passed'],'status':result.get('prediction',{}).get('status'),'error_type':result.get('error_type')},ensure_ascii=True),flush=True)
    finally:
        write_json(out/'api_usage.json',client.records)
        await client.close()
    summary={'purpose':'Real API integration smoke on two synthetic cases; not main benchmark results',
        'source_sha256':{p:sha256(ROOT/p) for p in ['gbfr/engine.py','gbfr/graph.py','gbfr/executor.py','gbfr/worker.py','gbfr/llm.py','gbfr/prompts.py']},
        'model':backbone['model'],'base_url':backbone['base_url'],'graph_sha256':sha256(config['graph']),
        'all_passed':all(r['passed'] for r in results),'results':[{'case':r['case']['id'],'passed':r['passed']} for r in results],
        'network_requests':sum(not r['cached'] for r in client.records),'cache_hits':sum(r['cached'] for r in client.records),
        'reported_usage':{k:sum(r.get('usage',{}).get(k,0) or 0 for r in client.records if not r['cached']) for k in ['prompt_tokens','completion_tokens','total_tokens']},
        'output_dir':str(out)}
    write_json(out/'summary.json',summary)
    write_json(ROOT/'research/reconstruction/gpt56_sol_api_smoke.json',summary)
    print(json.dumps(summary,ensure_ascii=True),flush=True)
    return summary['all_passed']


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=ROOT/'configs/gpt56_sol.json')
    args=parser.parse_args()
    raise SystemExit(0 if asyncio.run(run(args.config)) else 1)
