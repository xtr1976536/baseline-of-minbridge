"""运行 Logic-LM 官方 solver + CoT 回退，并调用官方 evaluator。"""
import argparse, json, os, random, shutil, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument('--dataset', required=True, choices=['ProntoQA','ProofWriter','FOLIO','LogicalDeduction','AR-LSAT'])
p.add_argument('--split',choices=['dev','test'],default='test')
p.add_argument('--model', default='gpt-4', help='逻辑程序文件所用作者参考模型标签')
p.add_argument('--programs', type=Path, required=True)
p.add_argument('--cot', type=Path, required=True, help='作者 CoT 回退答案 JSON')
p.add_argument('--tag', default='main')
a = p.parse_args()
u = ROOT/'upstream/Logic-LLM'
a.programs=a.programs.resolve();a.cot=a.cot.resolve()
os.chdir(u)
sys.path.insert(0,str(u/'models'))
os.environ['PATH'] = str(ROOT/'.venv/bin') + os.pathsep + os.environ.get('PATH','')
prover9_env=ROOT/'.local/prover9.env'
if prover9_env.exists():
    os.environ['PROVER9_BIN']=prover9_env.read_text().strip().split('=',1)[1]
from backup_answer_generation import Backup_Answer_Generator
from symbolic_solvers.fol_solver.prover9_solver import FOL_Prover9_Program
from symbolic_solvers.pyke_solver.pyke_solver import Pyke_Program
from symbolic_solvers.csp_solver.csp_solver import CSP_Program
from symbolic_solvers.z3_solver.sat_problem_solver import LSAT_Z3_Program
from evaluation import full_evaluation

solver_map = {'FOLIO':FOL_Prover9_Program,'ProntoQA':Pyke_Program,'ProofWriter':Pyke_Program,
              'LogicalDeduction':CSP_Program,'AR-LSAT':LSAT_Z3_Program}
rows = json.loads(a.programs.read_text())
cot = json.loads(a.cot.read_text())
if len({x['id'] for x in cot}) != len(cot):
    raise SystemExit('CoT 回退文件存在重复样本 ID。')
if set(x['id'] for x in rows) - set(x['id'] for x in cot):
    raise SystemExit('CoT 回退结果缺少逻辑程序数据中的样本 ID。')
cot_path = {x['id']:x for x in cot}
backup = Backup_Answer_Generator(a.dataset,'LLM',str(a.cot.resolve()))
solver = solver_map[a.dataset]
out = ROOT/'results'/f'logic-lm-{a.dataset}-{a.tag}.json'
out.parent.mkdir(exist_ok=True)
errors = 0
t0 = time.time()
results = []
for i,e in enumerate(rows):
    if a.dataset in ('ProntoQA','ProofWriter'):
        shutil.rmtree(u/'models/compiled_krb',ignore_errors=True)
        for mod in list(sys.modules):
            if mod == 'compiled_krb' or mod.startswith('compiled_krb.'):
                sys.modules.pop(mod,None)
    status, error = 'success', ''
    program = solver(e['raw_logic_programs'][0].strip(),a.dataset)
    if not program.flag:
        status = 'parsing error'
        pred = backup.get_backup_answer(e['id'])
    else:
        value, error = program.execute_program()
        if value is None:
            status = 'execution error'
            pred = backup.get_backup_answer(e['id'])
        else:
            pred = program.answer_mapping(value)
    if status != 'success':
        errors += 1
    results.append({'id':e['id'],'context':e['context'],'question':e['question'],
        'answer':e['answer'],'flag':status,'predicted_answer':pred,
        'error_message':str(error),'fallback_source':'CoT' if status != 'success' else None})
    if (i+1)%25 == 0:
        out.write_text(json.dumps(results,ensure_ascii=False,indent=2))
out.write_text(json.dumps(results,ensure_ascii=False,indent=2))
full_evaluation(str(out))
summary={'dataset':a.dataset,'split':a.split,'reference_model':a.model,'n':len(results),
         'solver_failures_with_cot_fallback':errors,'seconds':time.time()-t0,
         'cot_fallback':'used per sample ID for all non-success solver statuses',
         'programs_file':str(a.programs),'cot_fallback_file':str(a.cot),'result_file':str(out)}
out.with_name(out.stem+'-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print(json.dumps(summary,ensure_ascii=False))
