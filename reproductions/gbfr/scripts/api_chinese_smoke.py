"""Real API regression check on synthetic Chinese labels/tables, not test gold."""
import asyncio
from datetime import datetime,timezone
from pathlib import Path
import sys,json

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from gbfr.runner import resolve_paths,preflight
from gbfr.llm import ChatClient
from gbfr.engine import GBFR
from gbfr.data import write_json,sha256


async def main():
    config=resolve_paths(ROOT/'configs/gpt56_sol.json');graph,_=preflight(config)
    name,backbone=next(iter(config['backbones'].items()))
    client=ChatClient(backbone,Path(config['cache_dir'])/name);model=GBFR(graph,client)
    out=ROOT/'runs/api_smoke/gpt-5.6-sol'/('chinese-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    cases=[{'id':'chinese-label','question':"What were Company A's Current Assets in 2024, in CNY?",
        'context':'Company A 2024年流动资产为42元。文档未提供其他资产数值。','expected_value':42},
        {'id':'table-header','question':"What is Company A's Fiscal Revenue for 2024, in CNY?",
         'context':'Company A财政数据，金额单位为人民币元。\n| 年份 | 财政收入 | 债务 |\n| --- | --- | --- |\n| 2023 | 31 | 80 |\n| 2024 | 42 | 99 |','expected_value':42}]
    results=[]
    try:
        for case in cases:
            print('START '+case['id'],flush=True)
            try:
                p=(await model.predict(case['question'],case['context'])).to_dict()
                r={'case':case,'prediction':p,'passed':p['status']=='answered' and abs(p['value']-case['expected_value'])<1e-9}
            except Exception as exc:
                r={'case':case,'passed':False,'error':str(exc),'error_type':type(exc).__name__,'trace':getattr(exc,'gbfr_trace',{})}
            results.append(r);write_json(out/(case['id']+'.json'),r)
            print(json.dumps({'case':case['id'],'passed':r['passed'],'error':r.get('error')},ensure_ascii=True),flush=True)
    finally:
        write_json(out/'api_usage.json',client.records);await client.close()
    summary={'purpose':'Synthetic Chinese evidence integration, no benchmark gold used','all_passed':all(r['passed'] for r in results),
        'source_sha256':{p:sha256(ROOT/p) for p in ['gbfr/engine.py','gbfr/prompts.py','gbfr/llm.py','gbfr/runner.py']},
        'cases':[{'id':r['case']['id'],'passed':r['passed']} for r in results],'output_dir':str(out),
        'network_requests':sum(not r['cached'] for r in client.records),'cache_hits':sum(r['cached'] for r in client.records)}
    write_json(ROOT/'research/reconstruction/chinese_api_smoke.json',summary)
    print(json.dumps(summary,ensure_ascii=True),flush=True)
    return summary['all_passed']


if __name__=='__main__':raise SystemExit(0 if asyncio.run(main()) else 1)
