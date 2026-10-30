"""运行作者 ReAct 主模型 notebook；不运行 Act/CoT 基线。"""
import argparse,ast,json,os,sys,time,random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--task',choices=['hotpotqa','fever','alfworld','webshop'],required=True);p.add_argument('--model',default='text-davinci-002',help='API 实际模型 ID');p.add_argument('--reference-model',default='text-davinci-002',help='作者代码中的参考模型');p.add_argument('--api-mode',choices=['completion','chat'],default='completion');p.add_argument('--limit',type=int,default=500);p.add_argument('--prepare-only',action='store_true');a=p.parse_args()
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
if not os.getenv('OPENAI_API_KEY'):raise SystemExit('缺少 OPENAI_API_KEY；请先配置环境变量。')
import openai,requests
openai.api_key=os.environ['OPENAI_API_KEY'];openai.api_base=os.getenv('OPENAI_BASE_URL','https://api.openai.com/v1')
run=ROOT/'results'/f'react-{a.task}-{a.model.replace("/","_")}-{int(time.time())}';run.mkdir()
def llm(prompt,stop=['\n']):
 kw=dict(model=a.model,temperature=0,max_tokens=100,top_p=1,stop=stop,request_timeout=90)
 for attempt in range(3):
  try:
   if a.api_mode=='completion':r=openai.Completion.create(prompt=prompt,**kw);out=r['choices'][0]['text']
   else:r=openai.ChatCompletion.create(messages=[{'role':'user','content':prompt}],**kw);out=r['choices'][0]['message']['content']
   with (run/'api.jsonl').open('a') as f:f.write(json.dumps({'prompt':prompt,'stop':stop,'response':r,'reference_model':a.reference_model,'api_model':a.model,'api_mode':a.api_mode},ensure_ascii=False)+'\n')
   return out
  except Exception:
   if attempt==2:raise
   time.sleep(2**attempt)
os.chdir(u);sys.path.insert(0,str(u));ns={'llm':llm,'requests':requests};exec(compile(source,str(u/f'{name}.ipynb'),'exec'),ns)
if a.task=='webshop':
 ns['WEBSHOP_URL']=os.getenv('REACT_WEBSHOP_URL','http://127.0.0.1:3000').rstrip('/')
if a.task in ['hotpotqa','fever']:
 idxs=list(range(len(ns['env'].data)));random.Random(233).shuffle(idxs);vals=[]
 for idx in idxs[:a.limit]:
  score,info=ns['webthink'](idx,to_print=False);vals.append(info.get('em',score))
  with (run/'predictions.jsonl').open('a') as f:f.write(json.dumps({'index':idx,'info':info},ensure_ascii=False)+'\n')
 result={'n':len(vals),'accuracy':sum(vals)/len(vals)}
elif a.task=='webshop':
 vals=ns['run_episodes'](ns['prompt1'],a.limit);result={'n':len(vals),'success_rate':sum(x==1 for x in vals)/len(vals),'rewards':vals}
else:
 vals=[]
 for _ in range(min(a.limit,134)):
  ob,info=ns['env'].reset();ob='\n'.join(ob[0].split('\n\n')[1:]);name='/'.join(info['extra.gamefile'][0].split('/')[-3:-1])
  for k,v in ns['prefixes'].items():
   if name.startswith(k):
    prompt='Interact with a household to solve a task. Here are two examples.\n'+ns['d'][f'react_{v}_1']+ns['d'][f'react_{v}_0']+'\nHere is the task.\n';vals.append(ns['alfworld_run'](prompt,ob=ob));break
 result={'n':len(vals),'success_rate':sum(vals)/len(vals),'rewards':vals}
result.update(task=a.task,model=a.model,reference_model=a.reference_model,api_mode=a.api_mode,mode='end_to_end' if a.model=='text-davinci-002' and a.reference_model=='text-davinci-002' and a.api_mode=='completion' else 'substitute_backbone_not_exact_reproduction')
if a.task=='webshop':result['webshop_url']=ns['WEBSHOP_URL']
(run/'summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
