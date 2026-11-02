"""Bounded greedy PoT API checks. Official prompts, execution and scoring; alternate backbone."""
import argparse,ast,json,os,subprocess,sys,time,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
from protocol import ROOT,VENDOR,official
sys.path.insert(0,str(VENDOR))
from tool import finqa_equal
from eval_tatqa.tatqa_metric import TaTQAEmAndF1
from dotenv import dotenv_values
import requests

def main():
 p=argparse.ArgumentParser();p.add_argument('--model',default='gpt-5.6-sol');p.add_argument('--per-task',type=int,default=1);p.add_argument('--stratified',action='store_true');p.add_argument('--output',default='smoke-greedy');a=p.parse_args()
 if not 1<=a.per_task<=4:p.error('Only 1..4 samples per task during acceptance')
 config_env={**dotenv_values(ROOT.parents[1]/'.env'),**os.environ}
 out=ROOT/'results'/a.output;out.mkdir(parents=True,exist_ok=True)
 config={'actual_model':a.model,'reference_model':'code-davinci-002','mode':'few-shot greedy alternative-backbone smoke','per_task':a.per_task,'stratified':a.stratified,'runtime_sha256':{f:hashlib.sha256((ROOT/'scripts'/f).read_bytes()).hexdigest() for f in ['run_smoke.py','protocol.py','execute_worker.py']},'source_commit':subprocess.check_output(['git','-C',str(VENDOR),'rev-parse','HEAD'],text=True).strip(),'tasks':{t:official(t)[3] for t in ['finqa','convfinqa','tatqa']},'adaptations':['Completion -> Chat with explicit Python-continuation system instruction; original user prompt unchanged','no logprobs: unused for n=1','API finite retries; failures retained','leading whitespace stripped only; internal indentation preserved; raw retained','preflight guard + separate worker/timeout']}
 if (out/'config.json').exists() and json.loads((out/'config.json').read_text())!=config:raise RuntimeError('Config mismatch')
 (out/'config.json').write_text(json.dumps(config,indent=2))
 done={}
 if (out/'predictions.jsonl').exists():
  done={r['id']:r for r in map(json.loads,(out/'predictions.jsonl').read_text().splitlines())}
 for task in config['tasks']:
  demo,builder,rows,meta=official(task)
  selected=list(range(a.per_task))
  if a.stratified:
   selected=[];categories=set()
   for i,example in enumerate(rows):
    category=example.get('answer_type') if task=='tatqa' else ('boolean' if isinstance(example['answer'],str) else 'percent' if '/' in str(example.get('program',example.get('programs',''))) else 'number')
    if category not in categories:selected.append(i);categories.add(category)
    if len(selected)>=a.per_task:break
  for i in selected:
   example=rows[i]
   ident=f'{task}:{i}'
   if ident in done:continue
   prompt=demo+'\n\n'+builder(example)
   request={'model':a.model,'messages':[{'role':'system','content':'Complete the Python program requested by the final example. Return only executable Python statements assigning ans (and units when the examples use units). No Markdown fences or prose. Do not repeat the examples.'},{'role':'user','content':prompt}],'temperature':0.0,'top_p':1,'max_tokens':meta['max_tokens'],'stop':['\n\n'],'n':1}
   record={'id':ident,'task':task,'example':example};start=time.time()
   try:
    for attempt in range(3):
     response=requests.post(config_env['OPENAI_BASE_URL'].rstrip('/')+'/chat/completions',headers={'Authorization':'Bearer '+config_env['OPENAI_API_KEY']},json=request,timeout=120)
     if response.status_code in [429,500,502,503,504] and attempt<2:time.sleep(2**attempt);continue
     response.raise_for_status();break
    raw=response.json()
    with (out/'api.jsonl').open('a') as f:f.write(json.dumps({'id':ident,'request':request,'response':raw},ensure_ascii=False)+'\n')
    code=raw['choices'][0]['message']['content']
    if not isinstance(code,str) or not code.strip():raise ValueError('Empty model response')
    record.update(code=code,finish_reason=raw['choices'][0].get('finish_reason'))
    # No fence stripping or algorithmic repair; worker only removes leading boundary whitespace.
    child=subprocess.run([sys.executable,str(ROOT/'scripts/execute_worker.py')],input=json.dumps({'task':task,'code':code}),text=True,capture_output=True,timeout=20,cwd='/tmp',env={'PATH':os.environ.get('PATH',''),'PYTHONDONTWRITEBYTECODE':'1','OPENBLAS_NUM_THREADS':'1'})
    if child.returncode:raise RuntimeError('Execution worker failed: '+child.stderr[-300:])
    execution=json.loads(child.stdout.strip());record['execution']=execution
    value=execution['value']
    if task=='tatqa':
     pred,scale=value if value is not None else (None,None)
     try:pred=ast.literal_eval(str(pred)) if pred is not None else ''
     except (ValueError,SyntaxError):pred=str(pred)
     scale=str(scale) if scale is not None else ''
     if isinstance(pred,str):pred=[pred]
     if isinstance(pred,list) and pred and isinstance(pred[0],str) and scale and scale in pred[0]:scale=''
     metric=TaTQAEmAndF1();metric(example,prediction=pred,pred_scale=scale)
     em,f1,*_=metric.get_overall_metric();record.update(pred_answer=pred,pred_scale=scale,correct=em,f1=f1)
    else:
     if task=='finqa' and isinstance(value,bool):value='yes' if value else 'no'
     record.update(executed=value,correct=finqa_equal(value,example['answer'],False))
    record['status']='scored'
    record['execution_failed']=execution['status']!='executed'
   except Exception as e:record.update(status='run_error',correct=False,error=type(e).__name__+': '+str(e))
   record['seconds']=time.time()-start
   with (out/'predictions.jsonl').open('a') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
   done[ident]=record;print(ident,record['status'],'correct=',record['correct'],flush=True)
 summary={t:{'count':sum(r['task']==t for r in done.values()),'correct':sum(float(r['correct']) for r in done.values() if r['task']==t),'run_errors':sum(r['status']=='run_error' for r in done.values() if r['task']==t)} for t in config['tasks']}
 (out/'summary.json').write_text(json.dumps({'scope':'small smoke only, not full paper reproduction','tasks':summary},indent=2))
if __name__=='__main__':main()
