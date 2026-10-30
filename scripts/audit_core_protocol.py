"""离线核心协议审计：不调用 API。"""
import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; u=ROOT/'upstream/Logic-LLM'
checks=[]
def ok(name, condition, detail):
    checks.append({'check':name,'pass':bool(condition),'detail':detail})
for d in ['ProntoQA','ProofWriter','FOLIO','LogicalDeduction','AR-LSAT']:
    p=u/'models/prompts'/f'{d}.txt'; ok(f'{d} official prompt',p.exists(),str(p))
    p=u/'data'/d/'dev.json'; ok(f'{d} official dev data',p.exists(),str(p))
txt=Path('scripts/run_logic_inference.py').read_text()
ok('Logic-LM solver map',all(x in txt for x in ['FOL_Prover9_Program','Pyke_Program','CSP_Program','LSAT_Z3_Program']),'all five official solver classes referenced')
txt=Path('scripts/run_logic_refinement.py').read_text()
ok('Self-refinement scope',"choices=['AR-LSAT','FOLIO']" in txt and 'self-correct-' in txt,'only official AR-LSAT/FOLIO correction prompts')
txt=Path('scripts/run_logic_cot.py').read_text()
ok('CoT official examples','baselines/icl_examples' in txt and "mode='CoT'" in txt,'official CoT demonstrations')
txt=Path('scripts/run_react.py').read_text()
ok('ReAct notebook source','ipynb' in txt and 'webthink' in txt and 'alfworld_run' in txt,'official notebook functions')
tracked=subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines()
ok('No secret tracked',not any(x == '.env' or x.startswith('.env.') and x != '.env.example' for x in tracked), 'git index excludes secret environment; example template allowed')
result={'checks':checks,'all_pass':all(x['pass'] for x in checks)}
(ROOT/'manifests/core-protocol-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False))
