"""Concurrent full FinQA greedy run, fixed acceptance protocol, no other datasets."""
import concurrent.futures as cf
import argparse,ast,hashlib,json,os,subprocess,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
from protocol import ROOT,VENDOR,official
from dotenv import dotenv_values
sys.path.insert(0,str(VENDOR))
from tool import finqa_equal
from eval_tatqa.tatqa_metric import TaTQAEmAndF1
import requests
SYSTEM='Complete the Python program requested by the final example. Return only executable Python statements assigning ans (and units when the examples use units). No Markdown fences or prose. Do not repeat the examples.'


def write(path,data):
 temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2));temp.replace(path)

def main():
 p=argparse.ArgumentParser();p.add_argument('--task',choices=['convfinqa','tatqa'],required=True);a=p.parse_args()
 task=a.task;expected={'convfinqa':421,'tatqa':1668}[task];reference={'convfinqa':64.6,'tatqa':69.0}[task]
 OUT=ROOT/'results'/f'{task}-full-greedy-20261102'
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'samples').mkdir(exist_ok=True)
 env={**dotenv_values(ROOT.parents[1]/'.env'),**os.environ}
 demo,builder,rows,meta=official(task);assert len(rows)==expected
 config={'dataset':task,'expected':expected,'mode':'few-shot greedy','actual_model':'gpt-5.6-sol','paper_model':'code-davinci-002','workers':8,'protocol':meta,'system':SYSTEM,'runtime_sha256':{f:hashlib.sha256((ROOT/'scripts'/f).read_bytes()).hexdigest() for f in ['run_financial_full.py','protocol.py','execute_worker.py']},'source_commit':subprocess.check_output(['git','-C',str(VENDOR),'rev-parse','HEAD'],text=True).strip(),'paper_reference_accuracy_percent':reference,'adaptations':['Chat completion with fixed Python continuation instruction','leading boundary whitespace only; raw saved','same official execution/postprocess/score','finite transport retries only; no answer repair']}
 if (OUT/'config.json').exists() and json.loads((OUT/'config.json').read_text())!=config:raise RuntimeError('Immutable config mismatch')
 write(OUT/'config.json',config)
 records={int(p.stem):json.loads(p.read_text()) for p in (OUT/'samples').glob('*.json')}
 def run(i):
  example=rows[i];prompt=demo+'\n\n'+builder(example);start=time.time()
  request={'model':config['actual_model'],'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':prompt}],'temperature':0.0,'top_p':1,'max_tokens':meta['max_tokens'],'stop':['\n\n'],'n':1}
  r={'index':i,'id':example.get('id',example.get('question_id')),'task':task,'gold':example['answer'],'request':request,'attempts':[],'correct':False}
  try:
   for attempt in range(3):
    try:
     response=requests.post(env['OPENAI_BASE_URL'].rstrip('/')+'/chat/completions',headers={'Authorization':'Bearer '+env['OPENAI_API_KEY']},json=request,timeout=(20,180))
     r['attempts'].append({'attempt':attempt+1,'http_status':response.status_code})
     if response.status_code in [429,500,502,503,504]:raise RuntimeError('Temporary HTTP '+str(response.status_code))
     if response.status_code!=200:raise ValueError('Nonretryable HTTP '+str(response.status_code))
     raw=response.json();r['attempts'][-1]['response']=raw
     code=raw['choices'][0]['message']['content']
     if not isinstance(code,str) or not code.strip():raise RuntimeError('Empty model output')
     break
    except (requests.RequestException,RuntimeError,KeyError,IndexError) as e:
     if attempt==2:raise
     time.sleep(2**attempt)
   r.update(code=code,finish_reason=raw['choices'][0].get('finish_reason'))
   child=subprocess.run([sys.executable,str(ROOT/'scripts/execute_worker.py')],input=json.dumps({'task':task,'code':code}),capture_output=True,text=True,timeout=20,cwd='/tmp',env={'PATH':os.environ.get('PATH',''),'PYTHONDONTWRITEBYTECODE':'1','OPENBLAS_NUM_THREADS':'1'})
   if child.returncode:raise RuntimeError('Execution worker failed')
   execution=json.loads(child.stdout);value=execution['value']
   r.update(execution=execution,status='scored')
   if task=='convfinqa':
    r.update(executed=value,correct=finqa_equal(value,example['answer'],False))
   else:
    pred,scale=value if value is not None else (None,None)
    try:pred=ast.literal_eval(str(pred)) if pred is not None else ''
    except (ValueError,SyntaxError):pred=str(pred)
    scale=str(scale) if scale is not None else ''
    if isinstance(pred,str):pred=[pred]
    if isinstance(pred,list) and pred and isinstance(pred[0],str) and scale and scale in pred[0]:scale=''
    metric=TaTQAEmAndF1();metric(example,prediction=pred,pred_scale=scale)
    em,f1,*_=metric.get_overall_metric();r.update(pred_answer=pred,pred_scale=scale,correct=em,f1=f1)
  except Exception as e:r.update(status='run_error',error=type(e).__name__+': '+str(e))
  r['seconds']=time.time()-start
  return r
 def status(state):
  correct=sum(r['correct'] for r in records.values());errors=sum(r['status']=='run_error' for r in records.values());n=len(records)
  report={'status':state,'completed':n,'expected':len(rows),'correct':correct,'run_errors':errors,'execution_failures':sum(r.get('execution',{}).get('status')!='executed' for r in records.values() if r['status']=='scored'),'elapsed_seconds':time.time()-started,'accuracy_percent_completed_only':100*correct/n if n else None}
  write(OUT/'status.json',report)
  return report
 started=time.time();pending=iter(i for i in range(len(rows)) if i not in records)
 with cf.ThreadPoolExecutor(max_workers=8) as pool:
  active={}
  for _ in range(8):
   i=next(pending,None)
   if i is not None:active[pool.submit(run,i)]=i
  while active:
   finished,_=cf.wait(active,return_when=cf.FIRST_COMPLETED)
   for future in finished:
    i=active.pop(future);r=future.result();write(OUT/'samples'/f'{i:04d}.json',r);records[i]=r
    i=next(pending,None)
    if i is not None:active[pool.submit(run,i)]=i
   if len(records)%10==0 or not active:print(json.dumps(status('running')),flush=True)
   else:status('running')
 report=status('complete' if len(records)==len(rows) else 'incomplete')
 report.update(accuracy_percent=100*report['correct']/len(rows),paper_reference_percent=reference,difference_percentage_points=100*report['correct']/len(rows)-reference,comparison='Alternative backbone; cannot attribute difference to algorithm reproduction alone',unique_ids=len({r['id'] for r in records.values()}))
 usage={'prompt_tokens':0,'completion_tokens':0,'total_tokens':0}
 for r in records.values():
  for attempt in r['attempts']:
   u=attempt.get('response',{}).get('usage',{})
   for k in usage:usage[k]+=u.get(k,0) or 0
 if task=='tatqa':report['f1_percent']=100*sum(r.get('f1',0) for r in records.values())/len(rows)
 report['usage']=usage;report['truncated_outputs']=sum(r.get('finish_reason')=='length' for r in records.values())
 write(OUT/'summary.json',report)
 with (OUT/'predictions.jsonl').open('w') as f:
  for i in sorted(records):f.write(json.dumps(records[i],ensure_ascii=False)+'\n')
 print(json.dumps(report),flush=True)
if __name__=='__main__':main()
