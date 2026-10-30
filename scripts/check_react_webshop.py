"""无 LLM 的 WebShop 路由和作者 ReAct action/parser 验收；不是模型结果。"""
import argparse, ast, json, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:3000')
p.add_argument('--demo',action='store_true');a=p.parse_args()
nb=json.loads((ROOT/'upstream/ReAct/WebShop.ipynb').read_text())
nodes=[]
for cell in nb['cells']:
    if cell['cell_type']!='code':continue
    for n in ast.parse(''.join(cell['source'])).body:
        if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef,ast.ClassDef)):
            if not isinstance(n,ast.FunctionDef) or n.name!='llm':nodes.append(n)
        elif isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ACTION_TO_TEMPLATE' for t in n.targets):nodes.append(n)
ns={};exec(compile(ast.Module(body=nodes,type_ignores=[]),'author-WebShop','exec'),ns)
ns['WEBSHOP_URL']=a.url.rstrip('/')
env=ns['webshopEnv']();checks=[];coverage=[]
if not a.demo:
    for idx in range(500):
        obs,_,done=env.step(f'fixed_{idx}','reset')
        assert 'Instruction:' in obs and '[Search]' in obs and not done,(idx,obs)
        coverage.append({'session':f'fixed_{idx}','observation':obs})
    (ROOT/'manifests/webshop-500-tasks.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2))
for idx in ([0,1,2] if a.demo else [0,1,499]):
    session=f'fixed_{idx}'
    obs,reward,done=env.step(session,'reset')
    assert 'Instruction:' in obs and '[Search]' in obs,(session,obs)
    initial=obs
    obs,reward,done=env.step(session,'search[shoes]')
    asins=env.sessions[session].get('asins',[])
    assert asins,(session,obs)
    obs,reward,done=env.step(session,f'click[{asins[0]}]')
    assert '[Buy Now]' in obs,obs
    item_obs=obs
    obs,_,_=env.step(session,'click[Description]')
    assert obs.strip()
    env.step(session,'click[< Prev]')
    env.step(session,'think[environment smoke test]')
    obs,reward,done=env.step(session,'click[Buy Now]')
    assert done and 0<=reward<=1,(obs,reward,done)
    checks.append({'session':session,'initial_observation':initial,'item_observation':item_obs,
                   'purchase_observation':obs,'reward':reward,'done':done})
out=ROOT/'logs'/('react-webshop-demo-check.json' if a.demo else 'react-webshop-full-check.json')
out.write_text(json.dumps({'url':a.url,'api_calls':0,'demo_only':a.demo,'covered_sessions':len(coverage),
    'note':'scripted actions only; rewards are environment checks, not model performance',
    'checks':checks},ensure_ascii=False,indent=2))
print(out)
