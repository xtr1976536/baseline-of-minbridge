"""Run the unmodified official workflow; replace only API transport. No 50-row sampling."""
import argparse,hashlib,json,os,sys,time
sys.dont_write_bytecode=True
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
VENDOR=ROOT/'vendor/gbfr'
sys.path.insert(0,str(VENDOR))
from dotenv import load_dotenv
load_dotenv(ROOT.parents[1]/'.env')
from openai import OpenAI
import utils.LLMClient as api
from apply_gbfr_fixes import install
workflow=install()
run_workflow=workflow.run_workflow
from py2neo import Graph

def main():
 p=argparse.ArgumentParser();p.add_argument('--dataset',choices=['FinQA','TAT-QA','FinanceReasoning','CFBenchmark'],required=True);p.add_argument('--model',default='gpt-5.6-sol');p.add_argument('--limit',type=int,default=4);p.add_argument('--output',required=True);a=p.parse_args()
 if a.limit is None or not 1 <= a.limit <= 8:
  p.error('Audit stage permits 1..8 samples only; full evaluation disabled by user')
 out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=True)
 # Fail closed: official code otherwise silently continues without its graph.
 uri=os.getenv('GBFR_NEO4J_URI','bolt://localhost:17687')
 password=os.environ['GBFR_NEO4J_PASSWORD']
 graph=Graph(uri,auth=('neo4j',password))
 n=graph.run('MATCH (n:FinanceTerm_en) RETURN count(n) AS n').evaluate()
 if n!=7513: raise RuntimeError(f'Expected 7513 audited release FMKG terms, got {n}')
 client=OpenAI(api_key=os.environ['OPENAI_API_KEY'],base_url=os.environ['OPENAI_BASE_URL'],timeout=180,max_retries=2)
 sample_id=None
 def invoke(self,prompt,system_prompt=None,temperature=0.1,max_tokens=16384):
  messages=prompt if isinstance(prompt,list) else ([{'role':'system','content':system_prompt}] if system_prompt else [])+[{'role':'user','content':prompt}]
  t=time.time();response=client.chat.completions.create(model=a.model,messages=messages,temperature=temperature,max_tokens=max_tokens)
  content=response.choices[0].message.content
  if not content or not content.strip(): raise RuntimeError('Empty API response')
  with (out/'api.jsonl').open('a') as f: f.write(json.dumps({'sample_id':sample_id,'messages':messages,'response':response.model_dump(),'seconds':time.time()-t},ensure_ascii=False)+'\n')
  return api.LLMResponse(content)
 api.LLMWrapper.invoke=invoke
 rows=[];manifest=[]
 for path in sorted((VENDOR/'data'/a.dataset).glob('*.json')):
  manifest.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
  for i,d in enumerate(json.loads(path.read_text())):
   rows.append((f'{path.name}:{i}',d))
 if a.limit is not None: rows=rows[:a.limit]
 config={'dataset':a.dataset,'actual_model':a.model,'paper_models':['GPT-5','Qwen3-14B'],'mode':'smoke' if a.limit else 'full_public_release_alternative_backbone','max_depth':6,'graph_terms':n,'graph_version':'release-derived: error rows skipped; duplicate names unioned; first definition retained; differs from paper 7521','files':manifest,'expected':len(rows),'language':'en (only released English FMKG available)','evaluation_status':'diagnostic only; core audit NOT_READY', 'patch_sha256':hashlib.sha256((ROOT/'scripts/apply_gbfr_fixes.py').read_bytes()).hexdigest()}
 if (out/'config.json').exists():
  previous=json.loads((out/'config.json').read_text())
  if previous != config:raise RuntimeError('Output config mismatch; use a fresh output directory')
 (out/'config.json').write_text(json.dumps(config,indent=2))
 done=set()
 if (out/'predictions.jsonl').exists():done={json.loads(s)['id'] for s in (out/'predictions.jsonl').read_text().splitlines()}
 os.chdir(VENDOR)
 for sample_id,d in rows:
  if sample_id in done: continue
  context=d['context'];table=d.get('table','')
  if table:context+='\n'+(table if isinstance(table,str) else json.dumps(table))
  t=time.time()
  result=run_workflow(query=d['question'],context=context,model_name='openai',lang='en',max_depth=6,db_uri=uri,db_user='neo4j',db_password=password)
  # Workflow failures are retained; they are not automatically scored as abstention.
  record={'id':sample_id,'gold':d.get('answer',d.get('ground_truth')),'output':result,'seconds':time.time()-t}
  with (out/'predictions.jsonl').open('a') as f:f.write(json.dumps(record,ensure_ascii=False,default=lambda obj:obj.model_dump(mode='json') if hasattr(obj,'model_dump') else str(obj))+'\n')
  print(sample_id,json.dumps(result,ensure_ascii=False,default=lambda obj:obj.model_dump(mode='json') if hasattr(obj,'model_dump') else str(obj)),flush=True)
 (out/'status.json').write_text(json.dumps({'status':'generation_complete','count':len(rows),'not_yet_scored':True}))
if __name__=='__main__':main()
