"""无模型 API 的 Wikipedia Search/Lookup/Finish 和评测验收。"""
import argparse, json, os, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'logs/react-wikipedia-check.json');args=parser.parse_args();args.output=args.output.resolve()
u=ROOT/'upstream/ReAct'
sys.path.insert(0,str(u)); os.chdir(u)
from wikienv import WikiEnv
from wrappers import HotPotQAWrapper, FeverWrapper

checks=[]
for entity, keyword in [('Albert Einstein','physicist'),('Apple','fruit'),
                        ('Colorado orogeny','orogeny'),('Milhouse','Simpsons')]:
    env=WikiEnv();env.reset();start=time.time()
    obs,_,done,_=env.step(f'search[{entity}]')
    assert obs.strip() and not done, (entity,obs)
    lookup,_,_,_=env.step(f'lookup[{keyword}]')
    _,_,done,info=env.step('finish[smoke-test]')
    assert done and info['answer']=='smoke-test'
    checks.append({'entity':entity,'search':obs,'lookup':lookup,'seconds':time.time()-start})
for cls in (HotPotQAWrapper,FeverWrapper):
    env=cls(WikiEnv(),split='dev');env.reset(idx=0)
    gold=env.data[0][1]
    _,reward,done,info=env.step(f'finish[{gold}]')
    assert done and reward==1
    checks.append({'wrapper':cls.__name__,'n':len(env),'gold_finish_reward':reward})
out=args.output;out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps({'checks':checks,'api_calls':0,'protocol':'author HTML search/parser, identified User-Agent'},ensure_ascii=False,indent=2))
print(out)
