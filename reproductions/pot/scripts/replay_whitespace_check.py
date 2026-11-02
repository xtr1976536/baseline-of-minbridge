"""Diagnose Chat-only leading whitespace without another API request."""
import json,subprocess,sys
sys.dont_write_bytecode=True
from protocol import ROOT,VENDOR
sys.path.insert(0,str(VENDOR))
from eval_tatqa.tatqa_metric import TaTQAEmAndF1
source=ROOT/'results/smoke-chat-continuation/predictions.jsonl'
rows=[]
for line in source.read_text().splitlines():
 r=json.loads(line)
 if r['task']!='tatqa':continue
 raw=r['code'];code=raw.lstrip()
 result=subprocess.run([sys.executable,str(ROOT/'scripts/execute_worker.py')],input=json.dumps({'task':'tatqa','code':code}),text=True,capture_output=True,timeout=20)
 execution=json.loads(result.stdout);ans,units=execution['value']
 pred=[ans] if isinstance(ans,str) else ans
 metric=TaTQAEmAndF1();metric(r['example'],prediction=pred,pred_scale=units)
 em,f1,*_=metric.get_overall_metric()
 rows.append({'source_id':r['id'],'mode':'diagnostic replay of same API response; not a new generated sample','adaptation':'lstrip outer leading whitespace only; raw response retained','raw_code':raw,'executed_code':code,'execution':execution,'em':em,'f1':f1})
(ROOT/'results/whitespace_replay.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));print(json.dumps(rows,ensure_ascii=False))
