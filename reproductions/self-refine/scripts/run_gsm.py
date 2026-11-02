"""Official GSM self-feedback loop; same model each stage; gold used only in local score."""
import argparse,concurrent.futures as cf,contextlib,hashlib,io,json,os,subprocess,sys,threading,time
sys.dont_write_bytecode=True
from protocol import ROOT,VENDOR,instantiate,check_corr,manifest
from dotenv import dotenv_values
import requests
LOCK=threading.Lock()
def write(p,data):
 tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2));tmp.replace(p)
def main():
 p=argparse.ArgumentParser();p.add_argument('--limit',type=int,default=3);p.add_argument('--full',action='store_true');p.add_argument('--workers',type=int,default=4);p.add_argument('--output',default='gsm-smoke');a=p.parse_args()
 rows=[json.loads(s) for s in (VENDOR/'data/tasks/gsm/gsm.jsonl').read_text().splitlines()];assert len(rows)==1319
 if not a.full:rows=rows[:a.limit]
 out=ROOT/'results'/a.output;out.mkdir(parents=True,exist_ok=True);(out/'samples').mkdir(exist_ok=True);(out/'traces').mkdir(exist_ok=True)
 env={**dotenv_values(ROOT.parents[1]/'.env'),**os.environ}
 config={'actual_model':'gpt-5.6-sol','source_commit':subprocess.check_output(['git','-C',str(VENDOR),'rev-parse','HEAD'],text=True).strip(),'expected':len(rows),'max_attempts':4,'initial_temperature':0.7,'feedback_temperature':0.7,'choice':'paper temperature0.7 takes precedence over CLI initial default0.0','manifest':manifest(),'workers':a.workers,'mode':'full GSM only' if a.full else 'smoke','api_adaptation':'Chat continuation system instructions; original user prompt and stop tokens unchanged','metrics':['initial','final_output','official_cumulative_any_correct'],'code_sha256':{f:hashlib.sha256((ROOT/'scripts'/f).read_bytes()).hexdigest() for f in ['protocol.py','run_gsm.py','execute_worker.py']}}
 if (out/'config.json').exists() and json.loads((out/'config.json').read_text())!=config:raise RuntimeError('Config mismatch')
 write(out/'config.json',config);done={int(f.stem):json.loads(f.read_text()) for f in (out/'samples').glob('*.json')}
 def run(i):
  traces=[];start=time.time();record={'index':i,'input':rows[i]['input'],'target':rows[i]['target'],'api':traces}
  def call(prompt,engine,max_tokens,stop_token,temperature):
   system=('Continue the examples by returning only Python code defining solution(). Preserve the question as a docstring inside solution(), as in the examples. No Markdown fences or prose.' if not traces else 'Continue the examples with feedback comments followed by the complete revised Python def solution(): function. Always include the function, even if feedback says it is correct. No Markdown fences. Do not introduce outside information.')
   request={'model':'gpt-5.6-sol','messages':[{'role':'system','content':system},{'role':'user','content':prompt}],'temperature':temperature,'max_tokens':max_tokens,'stop':stop_token}
   trace={'stage':'init' if not traces else 'feedback_refine','request':request,'attempts':[]};traces.append(trace)
   for attempt in range(3):
    try:
     response=requests.post(env['OPENAI_BASE_URL'].rstrip('/')+'/chat/completions',headers={'Authorization':'Bearer '+env['OPENAI_API_KEY']},json=request,timeout=(20,180));trace['attempts'].append({'http_status':response.status_code})
     if response.status_code!=200:raise RuntimeError('HTTP '+str(response.status_code))
     raw=response.json();trace['attempts'][-1]['response']=raw;content=raw['choices'][0]['message']['content']
     if not content:raise RuntimeError('Empty response')
     write(out/'traces'/f'{i:04d}.json',traces)
     return content
    except (requests.RequestException,RuntimeError) as e:
     if attempt==2:raise
     time.sleep(2**attempt)
  # Author classes read relative prompt paths; cwd is set globally before launching.
  try:
   iterative=instantiate(call)
   logs=iterative(rows[i]['input'],4,'rich',0.7);record['run_logs']=logs;record['status']='generated'
  except Exception as e:record.update(status='generation_or_parse_error',error=type(e).__name__+': '+str(e));logs=[]
  solutions=[l['solution_curr'] for l in logs]+([logs[-1]['solution_fixed']] if logs else [])
  evaluations=[]
  for code in solutions:
   try:
    child=subprocess.run([sys.executable,str(ROOT/'scripts/execute_worker.py')],input=json.dumps({'code':code}),text=True,capture_output=True,timeout=5,cwd='/tmp',env={'PATH':os.environ.get('PATH',''),'PYTHONDONTWRITEBYTECODE':'1'})
    result=json.loads(child.stdout);result['correct']=bool(check_corr(result['value'],rows[i]['target'])) if result['value'] is not None else False
   except Exception as e:result={'status':'worker_error','correct':False,'error':type(e).__name__}
   evaluations.append(result)
  record.update(evaluations=evaluations,initial_correct=bool(evaluations and evaluations[0]['correct']),final_correct=bool(evaluations and evaluations[-1]['correct']),any_correct=any(e['correct'] for e in evaluations),seconds=time.time()-start)
  return record
 os.chdir(VENDOR);start=time.time()
 def status(state):
  n=len(done);s={'status':state,'completed':n,'expected':len(rows),'initial_correct':sum(r['initial_correct'] for r in done.values()),'final_correct':sum(r['final_correct'] for r in done.values()),'any_correct':sum(r['any_correct'] for r in done.values()),'run_errors':sum(r['status']!='generated' for r in done.values()),'elapsed_seconds':time.time()-start};write(out/'status.json',s);return s
 with cf.ThreadPoolExecutor(max_workers=a.workers) as pool:
  active={pool.submit(run,i):i for i in range(len(rows)) if i not in done}
  for future in cf.as_completed(active):
   i=active[future];r=future.result();write(out/'samples'/f'{i:04d}.json',r);done[i]=r;status('running')
 s=status('complete');s['initial_accuracy']=100*s['initial_correct']/len(rows);s['final_accuracy']=100*s['final_correct']/len(rows);s['official_cumulative_accuracy']=100*s['any_correct']/len(rows)
 write(out/'summary.json',s)
 with (out/'predictions.jsonl').open('w') as f:
  for i in sorted(done):f.write(json.dumps(done[i],ensure_ascii=False)+'\n')
 print(json.dumps(s),flush=True)
if __name__=='__main__':main()
