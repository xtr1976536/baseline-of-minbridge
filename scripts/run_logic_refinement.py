"""Logic-LM 官方 AR-LSAT/FOLIO 自我修正流程，最多三轮。"""
import argparse, json, os, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from api_compat import generate

p = argparse.ArgumentParser()
p.add_argument('--dataset',required=True,choices=['AR-LSAT','FOLIO'])
p.add_argument('--split',choices=['dev','test'],default='test')
p.add_argument('--programs',type=Path,required=True,help='首轮原始逻辑程序 JSON')
p.add_argument('--model',default='gpt-4',help='作者参考模型标签；选择原始 prompt 与输出命名')
p.add_argument('--api-model',help='API 实际模型 ID')
p.add_argument('--api-style',choices=['auto','completion','chat'],default='auto')
p.add_argument('--rounds',type=int,default=3,choices=[1,2,3])
p.add_argument('--max-tokens',type=int,default=1024)
p.add_argument('--tag',default='main')
a=p.parse_args()
if not os.getenv('OPENAI_API_KEY'):
    raise SystemExit('缺少 OPENAI_API_KEY；未发出请求。')
u=ROOT/'upstream/Logic-LLM'
os.chdir(u)
sys.path.insert(0,str(u/'models'))
os.environ['PATH']=str(ROOT/'.venv/bin')+os.pathsep+os.environ.get('PATH','')
prover9_env=ROOT/'.local/prover9.env'
if prover9_env.exists():
    os.environ['PROVER9_BIN']=prover9_env.read_text().strip().split('=',1)[1]
from symbolic_solvers.z3_solver.sat_problem_solver import LSAT_Z3_Program
from symbolic_solvers.fol_solver.prover9_solver import FOL_Prover9_Program
Solver={'AR-LSAT':LSAT_Z3_Program,'FOLIO':FOL_Prover9_Program}[a.dataset]
prompt_file=u/f'models/prompts/self-correct-{a.dataset}.txt'
template=prompt_file.read_text()
current=json.loads(a.programs.read_text())
run=ROOT/'results'/f'logic-refinement-{a.dataset}-{a.split}-{a.tag}-{int(time.time())}'
run.mkdir(parents=True)
(run/'round-0-programs.json').write_text(json.dumps(current,ensure_ascii=False,indent=2))
for rnd in range(1,a.rounds+1):
    refined=[]
    for ex in current:
        logic=ex['raw_logic_programs'][0].strip()
        prog=Solver(logic,a.dataset)
        if not prog.flag:
            status='parsing_error'; message='Parsing Error'
        else:
            answer,message=prog.execute_program()
            if answer is None:
                status='execution_error'
            else:
                status='success'
        if status=='execution_error' and message=='No Output':
            refined.append(ex)
            continue
        if status=='success':
            refined.append(ex)
            continue
        prompt=template.replace('[[PROGRAM]]',logic).replace('[[ERROR MESSAGE]]',str(message).strip())
        revised,response,style,wire_model=generate(prompt,a.model,a.api_model,a.api_style,
            a.max_tokens,0.0,'------',120)
        refined.append({k:ex[k] for k in ('id','context','question','answer','options')}
                       | {'raw_logic_programs':[revised.strip()]})
        with (run/f'round-{rnd}-api.jsonl').open('a') as f:
            f.write(json.dumps({'id':ex['id'],'prompt':prompt,'response':response,
                'previous_program':logic,'revised_program':revised,
                'reference_model':a.model,'api_model':wire_model,'api_style':style,
                'solver_status':status,'solver_error':str(message)},ensure_ascii=False)+'\n')
    current=refined
    (run/f'round-{rnd}-programs.json').write_text(json.dumps(current,ensure_ascii=False,indent=2))
    print(f'完成 self-refinement 第 {rnd} 轮：{len(current)} 条程序')
(run/'run.json').write_text(json.dumps({'dataset':a.dataset,'split':a.split,'rounds':a.rounds,
    'reference_model':a.model,'api_model':a.api_model or a.model,'api_style':a.api_style,
    'max_tokens':a.max_tokens,'temperature':0,'top_p':1.0,'stop':'------',
    'prompt_file':str(prompt_file),'source_programs':str(a.programs.resolve())},ensure_ascii=False,indent=2))
print('各轮结果目录：',run)
