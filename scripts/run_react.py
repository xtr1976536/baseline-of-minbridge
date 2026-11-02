"""运行作者 ReAct 主模型 notebook；不运行 Act/CoT 基线。"""
import argparse,ast,json,os,sys,time,random,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--task',choices=['hotpotqa','fever','alfworld','webshop'],required=True);p.add_argument('--model',default='gpt-5.6-sol',help='API 实际模型 ID');p.add_argument('--reference-model',default='text-davinci-002',help='作者代码中的参考模型');p.add_argument('--api-mode',choices=['completion','chat'],default='chat');p.add_argument('--limit',type=int,default=500);p.add_argument('--prepare-only',action='store_true');p.add_argument('--resume',type=Path);p.add_argument('--sample-indices',type=Path);p.add_argument('--run-dir',type=Path);p.add_argument('--sampling',choices=['author-notebook','all-dev'],default='author-notebook');a=p.parse_args()
if a.limit<1:p.error('--limit must be positive')
if a.sample_indices:a.sample_indices=a.sample_indices.resolve()
if a.run_dir:a.run_dir=a.run_dir.resolve()
u=ROOT/'upstream/ReAct';name={'fever':'FEVER','webshop':'WebShop'}.get(a.task,a.task);nb=json.loads((u/f'{name}.ipynb').read_text())
# Keep author definitions and environment setup; remove top-level evaluation loops/calls.
nodes=[]
for c in nb['cells']:
 if c['cell_type']!='code':continue
 tree=ast.parse(''.join(c['source']))
 for n in tree.body:
  text=ast.unparse(n)
  if isinstance(n,(ast.For,ast.Expr)):continue
  if isinstance(n,ast.FunctionDef) and n.name=='llm':continue
  if 'openai.api_key' in text:continue
  if isinstance(n,ast.Assign) and any(isinstance(x,ast.Call) and getattr(x.func,'id','') in ['webthink','run_episodes'] for x in ast.walk(n)):continue
  nodes.append(n)
source=ast.unparse(ast.Module(body=nodes,type_ignores=[]));(ROOT/f'configs/react-{a.task}-author-extracted.py').write_text(source+'\n')
if a.prepare_only:print('已导出作者主模型定义，未请求 API。');sys.exit()
# Same local credentials convention as finalized Logic-LM, with exported values first.
for line in (ROOT/'.env').read_text().splitlines() if (ROOT/'.env').exists() else []:
 if line.strip() and not line.lstrip().startswith('#'):
  key,value=line.split('=',1);os.environ.setdefault(key.strip(),value.strip())
if a.limit<1:raise SystemExit('--limit must be positive')
if not os.getenv('OPENAI_API_KEY'):raise SystemExit('缺少 OPENAI_API_KEY；请先配置环境变量。')
import openai,requests
from api_compat import generate
openai.api_key=os.environ['OPENAI_API_KEY'];openai.api_base=os.getenv('OPENAI_BASE_URL','https://api.openai.com/v1')
run=a.resume.resolve() if a.resume else a.run_dir if a.run_dir else ROOT/'results'/f'react-{a.task}-{a.model.replace("/","_")}-{int(time.time())}'
if a.resume and a.task not in ('hotpotqa','fever'):raise SystemExit('Resume currently supports QA episodes only')
if a.resume and a.run_dir:raise SystemExit('Choose --resume or --run-dir')
if not a.resume:run.mkdir(parents=True)
print('RUN',run,flush=True)
config={'task':a.task,'api_model':a.model,'reference_model':a.reference_model,'api_mode':a.api_mode,'requested_episodes':a.limit,'temperature':0,'max_tokens':100,'top_p':1,'notebook_sha256':hashlib.sha256((u/f'{name}.ipynb').read_bytes()).hexdigest(),'prompt_policy':'author notebook examples/functions unchanged; declared ReAct Chat format prefix','adapter':'react-continuation-v1','adapter_sha256':hashlib.sha256((ROOT/'scripts/react_adapter.py').read_bytes()).hexdigest(),'api_calls':0,'explicit_indices':json.loads(a.sample_indices.read_text()) if a.sample_indices else None}
if a.resume:
 old=json.loads((run/'run.json').read_text())
 for key in ('task','api_model','reference_model','api_mode','requested_episodes','notebook_sha256','adapter_sha256','explicit_indices'):
  if old[key]!=config[key]:raise SystemExit('Resume configuration mismatch: '+key)
 config['api_calls']=old['api_calls']
(run/'run.json').write_text(json.dumps(config,indent=2))
(run/'status.json').write_text(json.dumps({'state':'initializing'}))
def llm(prompt,stop=['\n']):
 from react_adapter import request_prefix, adapt_response
 # Keep the original prompt as an exact suffix. No other model or Logic-LM adapter.
 prefix=request_prefix(a.task,prompt) if a.api_mode=='chat' else ''
 request_prompt=prefix+prompt
 out,response,_,_=generate(request_prompt,a.reference_model,a.model,a.api_mode,100,0,stop,90)
 config['api_calls']+=1
 entry={'original_author_prompt':prompt,'prompt':request_prompt,'format_prefix':prefix,'stop':stop,'response':response,'reference_model':a.reference_model,'api_model':a.model,'api_mode':a.api_mode}
 try:
  if not out.strip():raise ValueError('Empty model response')
  adapted,audit=adapt_response(a.task,prompt,out,stop) if a.api_mode=='chat' else (out,{'policy':'author-completion'})
  entry.update(adapted_output=adapted,adaptation=audit)
 except ValueError as ex:
  if not out.strip():raise RuntimeError('Empty model response') from ex
  if a.task not in ('hotpotqa','fever'):raise
  # The author webthink already retries malformed Thought/Action continuations.
  # Return only the first model line, never its generated observations or future plan.
  import re
  first=re.split(r'\bObservation(?:\s+\d+)?\s*:',out,flags=re.I)[0].strip().split('\n')[0]
  adapted=first or 'Invalid model output'
  entry.update(adaptation_error=str(ex),adapted_output=adapted,adaptation={'policy':'author-malformed-output-path','reason':str(ex)})
 with (run/'api.jsonl').open('a') as f:f.write(json.dumps(entry,ensure_ascii=False)+'\n')
 (run/'run.json').write_text(json.dumps(config,indent=2))
 return adapted
try:
 os.chdir(u);sys.path.insert(0,str(u))
 if a.task in ('hotpotqa','fever'):
  import wikienv
  from react_logging import safe_wikipedia_cleaner
  wikienv.clean_str=safe_wikipedia_cleaner(wikienv.clean_str)
 ns={'llm':llm,'requests':requests,'sys':sys};exec(compile(source,str(u/f'{name}.ipynb'),'exec'),ns)
 from react_logging import trace_environment
 ns['env']=trace_environment(ns['env'],run/'environment.jsonl')
 (run/'status.json').write_text(json.dumps({'state':'running'}))
 if a.task=='webshop':
  ns['WEBSHOP_URL']=os.getenv('REACT_WEBSHOP_URL','http://127.0.0.1:3000').rstrip('/')
 if a.task in ['hotpotqa','fever']:
  pool=len(ns['env'].data)
  if a.sampling=='author-notebook':pool=min(7405,pool)
  idxs=list(range(pool));random.Random(233).shuffle(idxs);vals=[]
  if config['explicit_indices'] is not None:
   idxs=config['explicit_indices']
   if not idxs or len(idxs)!=len(set(idxs)) or any(type(x) is not int or not 0<=x<pool for x in idxs):raise RuntimeError('Invalid explicit question indices')
  config['sampling']={'pool_size':pool,'policy':a.sampling,'dataset_size':len(ns['env'].data),'seed':233,'sample_indices':idxs[:a.limit],'note':'HotpotQA matches author notebook. FEVER author notebook hardcodes 7405 despite 9999 data rows. Default reproduces notebook pool; all-dev is an explicit deviation.'}
  (run/'run.json').write_text(json.dumps(config,indent=2))
  saved=[json.loads(l) for l in (run/'predictions.jsonl').read_text().splitlines()] if (run/'predictions.jsonl').exists() else []
  done={r['index'] for r in saved}
  if len(done)!=len(saved) or done-set(idxs[:a.limit]):raise RuntimeError('Checkpoint IDs mismatch')
  vals=[r['info']['em'] for r in saved]
  for idx in idxs[:a.limit]:
   if idx in done:continue
   score,info=ns['webthink'](idx,to_print=False);vals.append(info.get('em',score))
   with (run/'predictions.jsonl').open('a') as f:f.write(json.dumps({'index':idx,'info':info},ensure_ascii=False)+'\n')
   (run/'status.json').write_text(json.dumps({'state':'running','completed':len(vals),'requested':a.limit,'correct':sum(vals),'api_calls':config['api_calls']}))
   print('Completed',len(vals),'/',a.limit,'correct',sum(vals),flush=True)
  result={'n':len(vals),'accuracy':sum(vals)/len(vals)}
 elif a.task=='webshop':
  from react_logging import trace_webshop_episodes
  trace_webshop_episodes(ns,run/'predictions.jsonl')
  vals=ns['run_episodes'](ns['prompt1'],a.limit)
  result={'n':len(vals),'success_rate':sum(x==1 for x in vals)/len(vals),'rewards':vals}
 else:
  vals=[]
  for _ in range(min(a.limit,134)):
   ob,info=ns['env'].reset();ob='\n'.join(ob[0].split('\n\n')[1:]);game_name='/'.join(info['extra.gamefile'][0].split('/')[-3:-1])
   for k,v in ns['prefixes'].items():
    if game_name.startswith(k):
     prompt='Interact with a household to solve a task. Here are two examples.\n'+ns['d'][f'react_{v}_1']+ns['d'][f'react_{v}_0']+'\nHere is the task.\n'
     reward=ns['alfworld_run'](prompt,ob=ob);vals.append(reward)
     with (run/'predictions.jsonl').open('a') as f:f.write(json.dumps({'episode':len(vals)-1,'game':game_name,'task_type':k,'reward':reward})+'\n')
     break
  result={'n':len(vals),'success_rate':sum(vals)/len(vals),'rewards':vals}
 adaptations=[json.loads(l) for l in (run/'api.jsonl').read_text().splitlines()] if (run/'api.jsonl').exists() else []
 result.update(generated_observations_discarded=sum(bool(x.get('adaptation',{}).get('discarded_generated_observation')) for x in adaptations),api_calls=config['api_calls'],task=a.task,model=a.model,reference_model=a.reference_model,api_mode=a.api_mode,mode='end_to_end' if a.model=='text-davinci-002' and a.reference_model=='text-davinci-002' and a.api_mode=='completion' else 'substitute_backbone_not_exact_reproduction')
 if a.task=='webshop':result['webshop_url']=ns['WEBSHOP_URL']
 (run/'summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
 (run/'status.json').write_text(json.dumps({'state':'complete','episodes':result['n']}))
except Exception as ex:
 (run/'status.json').write_text(json.dumps({'state':'stopped_on_error','error':type(ex).__name__+': '+str(ex),'completed_episodes':len((run/'predictions.jsonl').read_text().splitlines()) if (run/'predictions.jsonl').exists() else 0},indent=2))
 raise
