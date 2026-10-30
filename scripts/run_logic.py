"""官方提示生成逻辑程序，调用官方求解器；不运行其他 baseline。"""
import argparse,os,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--dataset',required=True,choices=['ProntoQA','ProofWriter','FOLIO','LogicalDeduction','AR-LSAT']);p.add_argument('--model',default='gpt-4');p.add_argument('--limit',type=int);p.add_argument('--max-tokens',type=int,default=1024);a=p.parse_args()
if not os.getenv('OPENAI_API_KEY'):raise SystemExit('缺少 OPENAI_API_KEY；未发出请求。')
u=ROOT/'upstream/Logic-LLM';os.chdir(u);sys.path.insert(0,str(u/'models'));os.environ['PATH']=str(ROOT/'.venv/bin')+os.pathsep+os.environ['PATH']
import openai
openai.api_key=os.environ['OPENAI_API_KEY'];openai.api_base=os.getenv('OPENAI_BASE_URL','https://api.openai.com/v1')
from logic_program import LogicProgramGenerator
from types import SimpleNamespace
args=SimpleNamespace(data_path=str(u/'data'),dataset_name=a.dataset,split='dev',model_name=a.model,save_path='',api_key=openai.api_key,stop_words=None,max_new_tokens=a.max_tokens)
g=LogicProgramGenerator(args);rows=g.load_raw_dataset('dev');rows=rows[:a.limit] if a.limit else rows
run=ROOT/'results'/f'logic-{a.dataset}-{a.model.replace("/","_")}-{int(time.time())}';run.mkdir()
outputs=[]
for e in rows:
 prompt=g.prompt_creator[a.dataset](e)
 kw=dict(model=a.model,temperature=0,max_tokens=a.max_tokens,request_timeout=120)
 if a.model.startswith('text-'):r=openai.Completion.create(prompt=prompt,**kw);text=r['choices'][0]['text']
 else:r=openai.ChatCompletion.create(messages=[{'role':'user','content':prompt}],**kw);text=r['choices'][0]['message']['content']
 outputs.append({**e,'raw_logic_programs':[text]})
 with (run/'api.jsonl').open('a') as f:f.write(json.dumps({'id':e['id'],'prompt':prompt,'response':r},ensure_ascii=False)+'\n')
 (run/'programs.json').write_text(json.dumps(outputs,ensure_ascii=False,indent=2))
print('程序已生成：',run/'programs.json')
# Keep API-generated artifacts distinct from the authors' cached files.
print('下一步调用 replay_logic.py --programs 此文件 --tag 独立运行名。')
