"""Reproduce one service rejection without using its gold label."""
import asyncio,json,os,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'runs/gpt56_sol_full'
sys.path.insert(0,str(OUT/'source_snapshot'))
from gbfr.runner import preflight,resolve_paths
from gbfr.engine import GBFR
from gbfr.llm import ChatClient
from gbfr.data import write_json

async def main():
    config=resolve_paths(OUT/'source_snapshot/configs/run.json')
    graph,datasets=preflight(config)
    prior=None
    for path in (OUT/'shards').rglob('predictions.jsonl'):
        for line in path.read_text(encoding='utf-8').splitlines():
            p=json.loads(line)
            if p.get('error_type')=='APIError' and 'HTTP 403' in p.get('error',''):
                prior=p;break
        if prior:break
    if not prior:raise RuntimeError('No recorded 403')
    sample=next(s for rows in datasets.values() for s in rows if s['id']==prior['sample_id'])
    client=ChatClient(config['backbones']['GPT-5.6 Sol'],Path(config['cache_dir'])/'GPT-5.6 Sol')
    failures=[]
    async def inspect(response):
        if response.status_code<400:return
        await response.aread()
        try:body=response.json();error=body.get('error',body)
        except ValueError:error={'message':response.text[:1500]}
        if isinstance(error,dict):error={k:error[k] for k in ('code','type','message','detail') if k in error}
        safe=re.sub(r'sk-[A-Za-z0-9_-]+','[REDACTED]',json.dumps(error,ensure_ascii=False).replace(client.api_key,'[REDACTED]'))
        failures.append({'status_code':response.status_code,'error':json.loads(safe)})
    client.http.event_hooks['response']=[inspect]
    try:
        pred=await GBFR(graph,client,config['execution_timeout']).predict(sample['question'],sample['context'])
        result={'sample_id':sample['id'],'retry_status':pred.status,'failures':failures}
    except Exception as exc:
        result={'sample_id':sample['id'],'retry_error_type':type(exc).__name__,'retry_error':str(exc),'failures':failures}
    finally:await client.close()
    write_json(OUT/'scheduling/exact_failure_probe.json',result)
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':asyncio.run(main())
