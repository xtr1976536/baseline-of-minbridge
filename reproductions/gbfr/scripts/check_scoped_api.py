"""Check the actual first OQA request for each selected dataset; no gold used."""
import asyncio,json,re,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'runs/gpt56_sol_full'
sys.path.insert(0,str(OUT/'source_snapshot'))
from gbfr.runner import preflight,resolve_paths
from gbfr.engine import GBFR
from gbfr.llm import ChatClient
from gbfr.data import sha256,write_json

class RequestReady(Exception):pass
class ProbeClient(ChatClient):
    async def complete(self,task,prompt,*,json_mode=False):
        if task!='OQA':raise RuntimeError('Probe must stop after OQA')
        await super().complete(task,prompt,json_mode=json_mode)
        raise RequestReady()

async def main():
    config=resolve_paths(OUT/'source_snapshot/configs/run.json')
    graph,datasets=preflight(config)
    frozen=json.loads((OUT/'full_run_manifest.json').read_text(encoding='utf-8'))
    for name,digest in frozen['source_sha256'].items():
        if sha256(OUT/'source_snapshot'/name)!=digest:raise RuntimeError('Frozen source mismatch')
    scope=json.loads((ROOT/'configs/gpt56_sol_scope.json').read_text(encoding='utf-8'))
    checks=[]
    for name in scope['datasets']:
        sample=datasets[name][0]
        client=ProbeClient(config['backbones']['GPT-5.6 Sol'],Path(config['cache_dir'])/'GPT-5.6 Sol')
        failures=[]
        async def capture(response):
            if response.status_code<400:return
            await response.aread()
            try:body=response.json();error=body.get('error',body)
            except ValueError:error={'message':response.text[:1500]}
            if isinstance(error,dict):error={k:error[k] for k in ('code','type','message','detail') if k in error}
            safe=re.sub(r'sk-[A-Za-z0-9_-]+','[REDACTED]',json.dumps(error,ensure_ascii=False).replace(client.api_key,'[REDACTED]'))
            failures.append({'status_code':response.status_code,'error':json.loads(safe)})
        client.http.event_hooks['response']=[capture]
        row={'dataset':name,'sample_id':sample['id'],'purpose':'Only first OQA request; not a prediction or an accuracy result.'}
        try:
            await GBFR(graph,client,config['execution_timeout']).predict(sample['question'],sample['context'])
        except RequestReady:row['ready']=True
        except Exception as exc:row.update(ready=False,error_type=type(exc).__name__,error=str(exc),failures=failures)
        finally:await client.close()
        checks.append(row)
        print(json.dumps(row,ensure_ascii=False),flush=True)
        if not row['ready']:break
    result={'checked_at':datetime.now(timezone.utc).isoformat(),'datasets':scope['datasets'],'total':scope['total'],
            'ready':len(checks)==len(scope['datasets']) and all(c['ready'] for c in checks),'checks':checks}
    write_json(OUT/'scheduling/scoped_api_check.json',result)
    print(json.dumps({'ready':result['ready'],'scope':scope['datasets'],'total':scope['total']},ensure_ascii=False))

if __name__=='__main__':asyncio.run(main())
