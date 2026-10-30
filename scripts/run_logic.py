"""官方提示生成逻辑程序，调用官方求解器；不运行其他 baseline。"""
import argparse,os,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--dataset',required=True,choices=['ProntoQA','ProofWriter','FOLIO','LogicalDeduction','AR-LSAT']);p.add_argument('--model',default='gpt-4',help='作者模型标签；用于选择官方 prompt');p.add_argument('--api-model',help='API 实际模型 ID；默认与 --model 相同');p.add_argument('--api-style',choices=['auto','completion','chat'],default='auto');p.add_argument('--limit',type=int);p.add_argument('--max-tokens',type=int,default=1024);p.add_argument('--split',choices=['dev','test'],default='dev');a=p.parse_args()
if not os.getenv('OPENAI_API_KEY'):raise SystemExit('缺少 OPENAI_API_KEY；未发出请求。')
u=ROOT/'upstream/Logic-LLM';os.chdir(u);sys.path.insert(0,str(u/'models'));os.environ['PATH']=str(ROOT/'.venv/bin')+os.pathsep+os.environ['PATH']
from api_compat import generate
from logic_program import LogicProgramGenerator
from types import SimpleNamespace
args=SimpleNamespace(data_path=str(u/'data'),dataset_name=a.dataset,split=a.split,model_name=a.model,save_path='',api_key=os.environ['OPENAI_API_KEY'],stop_words=None,max_new_tokens=a.max_tokens)
g=LogicProgramGenerator(args);rows=g.load_raw_dataset(a.split);rows=rows[:a.limit] if a.limit else rows
prompt_path=u/'models'/'prompts'/('AR-LSAT-long.txt' if a.dataset=='AR-LSAT' and a.model=='gpt-4' else f'{a.dataset}.txt')
g.prompt_template=prompt_path.read_text()
run=ROOT/'results'/f'logic-{a.dataset}-{a.split}-{(a.api_model or a.model).replace("/","_")}-{int(time.time())}';run.mkdir()
previous=sorted(ROOT.glob(f'results/logic-{a.dataset}-{a.split}-{(a.api_model or a.model).replace("/","_")}-*/programs.json'),key=lambda p:p.stat().st_mtime)
outputs=json.loads(previous[-1].read_text()) if previous else []
done={e['id'] for e in outputs}
if len(done)!=len(outputs) or done-set(e['id'] for e in rows):raise SystemExit('续跑 ID 与当前数据不匹配')
if previous:
 old=previous[-1].parent/'run.json'
 if old.exists():
  cfg=json.loads(old.read_text())
  if cfg.get('max_tokens')!=a.max_tokens or cfg.get('reference_model')!=a.model:raise SystemExit('已有运行参数不一致，拒绝复用')
api_log=(run/'api.jsonl').open('a')
for e in rows:
 if e['id'] in done:continue
 prompt=g.prompt_creator[a.dataset](e)
 text,r,style,wire_model=generate(prompt,a.model,a.api_model,a.api_style,a.max_tokens,0.0,'------',120)
 outputs.append({**e,'raw_logic_programs':[text]})
 api_log.write(json.dumps({'id':e['id'],'prompt':prompt,'response':r,'reference_model':a.model,'api_model':wire_model,'api_style':style},ensure_ascii=False)+'\n');api_log.flush()
 tmp=run/'programs.json.tmp';tmp.write_text(json.dumps(outputs,ensure_ascii=False,indent=2));tmp.replace(run/'programs.json')
api_log.close()
(run/'run.json').write_text(json.dumps({'dataset':a.dataset,'split':a.split,'n_requested':len(rows),'reference_model':a.model,'api_model':a.api_model or a.model,'api_style':a.api_style,'temperature':0,'max_tokens':a.max_tokens,'top_p':1.0,'stop':'------','prompt_file':str(prompt_path),'result_class':'reference_model' if a.model==(a.api_model or a.model) else 'substitute_backbone'},ensure_ascii=False,indent=2))
print('程序已生成：',run/'programs.json')
# Keep API-generated artifacts distinct from the authors' cached files.
print('下一步调用 replay_logic.py --programs 此文件 --tag 独立运行名。')
