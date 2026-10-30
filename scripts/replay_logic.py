"""重放作者公开的 GPT-4 逻辑程序，不调用模型 API。"""
import argparse,json,os,sys,time,random,traceback,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--dataset',required=True,choices=['LogicalDeduction','AR-LSAT','FOLIO','ProntoQA','ProofWriter']);p.add_argument('--limit',type=int);p.add_argument('--programs',type=Path);p.add_argument('--tag',default='author-replay');a=p.parse_args()
if a.programs:a.programs=a.programs.resolve()
u=ROOT/'upstream/Logic-LLM';os.chdir(u);sys.path.insert(0,str(u/'models'))
if a.dataset=='LogicalDeduction':
 from symbolic_solvers.csp_solver.csp_solver import CSP_Program as Solver
elif a.dataset=='AR-LSAT':
 from symbolic_solvers.z3_solver.sat_problem_solver import LSAT_Z3_Program as Solver
elif a.dataset=='FOLIO':
 from symbolic_solvers.fol_solver.prover9_solver import FOL_Prover9_Program as Solver
else:
 from symbolic_solvers.pyke_solver.pyke_solver import Pyke_Program as Solver
rows=json.loads((a.programs.resolve() if a.programs else u/f'outputs/logic_programs/{a.dataset}_dev_gpt-4.json').read_text());rows=rows[:a.limit] if a.limit else rows
rng=random.Random(0);out=ROOT/f'results/logic-lm-{a.dataset}-{a.tag}.jsonl';correct=errors=0;t=time.time()
with out.open('w') as f:
 for i,e in enumerate(rows):
  if a.dataset in ['ProntoQA','ProofWriter']:
   shutil.rmtree(u/'models/compiled_krb',ignore_errors=True)
   for mod in list(sys.modules):
    if mod=='compiled_krb' or mod.startswith('compiled_krb.'):sys.modules.pop(mod,None)
  pred=None;status='success';err=''
  try:
   s=Solver(e['raw_logic_programs'][0].strip(),a.dataset)
   if not s.flag:status='parsing_error'
   else:
    ans,msg=s.execute_program()
    if ans is None:status='execution_error';err=str(msg)
    else:pred=s.answer_mapping(ans)
  except Exception as ex:status='exception';err=f'{type(ex).__name__}: {ex}'
  if pred is None:
   errors+=1
   opts=['A','B'] if a.dataset=='ProntoQA' else ['A','B','C'] if a.dataset in ['FOLIO','ProofWriter'] else ['A','B','C','D','E'] if a.dataset=='AR-LSAT' else [chr(65+j) for j in range(len(e['options']))]
   pred=rng.choice(opts)
  gold=e['answer'].replace('(','').replace(')','').strip();ok=pred==gold;correct+=ok
  f.write(json.dumps({'id':e['id'],'gold':gold,'prediction':pred,'correct':ok,'status':status,'error':err},ensure_ascii=False)+'\n');f.flush()
  if (i+1)%25==0:print(a.dataset,i+1,correct,errors,flush=True)
summary={'dataset':a.dataset,'mode':'api_generated_program_solver_run' if a.programs else 'author_program_replay_not_end_to_end','model_source':'author gpt-4 cached programs','n':len(rows),'correct':correct,'accuracy':correct/len(rows),'solver_failures':errors,'fallback':'seeded random, seed=0; LogicalDeduction uses actual option count (upstream fallback lacks support)','seconds':time.time()-t}
(ROOT/f'results/logic-lm-{a.dataset}-{a.tag}-summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary),flush=True)
