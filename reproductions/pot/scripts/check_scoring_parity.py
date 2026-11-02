"""Offline official-executor and metric parity, including booleans and TAT-QA scale."""
import json,sys,subprocess
sys.dont_write_bytecode=True
from protocol import ROOT,VENDOR
sys.path.insert(0,str(VENDOR))
from tool import safe_execute,floatify_ans,finqa_equal
from eval_tatqa.tatqa_metric import TaTQAEmAndF1
cases=[('finqa','ans = 0',0.0),('finqa','ans = False',False),('finqa','ans = True',True),('finqa','ans = {"answer": 0.25}',0.25),('finqa','ans = [4]',4.0),('convfinqa','ans = True',1.0),('convfinqa','ans = (2,3)',2.0),('tatqa',"ans = ['2018','2019']\nunits = ''",[['2018','2019'],'']),('tatqa',"ans = 12.5\nunits = 'percent'",[12.5,'percent'])]
for task,code,expected in cases:
 child=subprocess.run([sys.executable,str(ROOT/'scripts/execute_worker.py')],input=json.dumps({'task':task,'code':code}),capture_output=True,text=True,timeout=20)
 x=json.loads(child.stdout);assert x['value']==expected,(task,code,x)
 if task=='finqa':assert floatify_ans(safe_execute(code))==x['value']
assert finqa_equal(1.424025457438345,1.42403,False)
assert not finqa_equal(25,0.25,False) # No added percent relaxation.
assert finqa_equal('yes','yes',False) and not finqa_equal('no','yes',False)
metric=TaTQAEmAndF1();metric({'answer':12.5,'scale':'percent','answer_type':'arithmetic','derivation':'','question_id':'fixture'},prediction=12.5,pred_scale='percent');assert metric.get_overall_metric()[0]==1
metric=TaTQAEmAndF1();metric({'answer':12.5,'scale':'percent','answer_type':'arithmetic','derivation':'','question_id':'fixture'},prediction=12.5,pred_scale='million');assert metric.get_overall_metric()[0]==0
(ROOT/'results/scoring_parity.json').write_text(json.dumps({'worker_cases':len(cases),'official_finqa_comparison':'PASS','tatqa_correct_and_wrong_scale':'PASS','no_extra_percent_tolerance':'PASS','known_upstream_behavior':'ConvFinQA casts boolean output to float before scoring; retained instead of silently fixing algorithm behavior.'},indent=2))
print('Executor and official score parity PASS')
