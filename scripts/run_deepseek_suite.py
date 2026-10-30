"""DeepSeek 替代底座全量实验；逐阶段记录日志，失败不伪造结果。"""
import os,sys,subprocess,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT)
for line in (ROOT/'.env').read_text().splitlines():
 if line and not line.startswith('#'):
  k,v=line.split('=',1);os.environ[k]=v
os.environ['PATH']=str(ROOT/'.venv/bin')+os.pathsep+os.environ['PATH']
run=ROOT/'logs'/f'deepseek-suite-{int(time.time())}';run.mkdir()
status=[]
def call(name,args):
 with (run/f'{name}.log').open('w') as f:
  p=subprocess.run([sys.executable,*args],stdout=f,stderr=subprocess.STDOUT)
 status.append({'stage':name,'exit_code':p.returncode})
 (run/'status.json').write_text(json.dumps(status,indent=2))
 if p.returncode:raise RuntimeError(name)
def newest(pattern):return max(ROOT.glob(pattern),key=lambda p:p.stat().st_mtime)
for d in ['ProntoQA','ProofWriter','LogicalDeduction','FOLIO','AR-LSAT']:
 try:
  common=['--dataset',d,'--model','gpt-4','--api-model','deepseek-flash','--api-style','chat']
  call(d+'-generate',['scripts/run_logic.py',*common]);program=newest(f'results/logic-{d}-dev-deepseek-flash-*/programs.json')
  call(d+'-cot',['scripts/run_logic_cot.py',*common]);cot=newest(f'results/logic-cot-{d}-dev-deepseek-flash-*/cot.json')
  call(d+'-inference',['scripts/run_logic_inference.py','--dataset',d,'--split','dev','--programs',str(program),'--cot',str(cot),'--tag','deepseek-flash-main'])
  if d in ['FOLIO','AR-LSAT']:
   call(d+'-refine',['scripts/run_logic_refinement.py',*common,'--split','dev','--programs',str(program),'--tag','deepseek-flash'])
   refined=newest(f'results/logic-refinement-{d}-dev-deepseek-flash-*')
   for n in range(1,4):call(d+f'-refined-{n}',['scripts/run_logic_inference.py','--dataset',d,'--split','dev','--programs',str(refined/f'round-{n}-programs.json'),'--cot',str(cot),'--tag',f'deepseek-flash-refined-{n}'])
 except Exception as e:print(d,str(e),flush=True)
for task in ['alfworld','hotpotqa','fever','webshop']:
 try:call('react-'+task,['scripts/run_react.py','--task',task,'--model','deepseek-flash','--api-mode','chat','--limit','134' if task=='alfworld' else '500'])
 except Exception as e:print(task,str(e),flush=True)
