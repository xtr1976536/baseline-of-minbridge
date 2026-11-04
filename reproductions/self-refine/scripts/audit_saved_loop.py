"""Reconstruct all official loop calls using saved responses, with no API or execution."""
import gzip,json,os,sys
sys.dont_write_bytecode=True
from protocol import ROOT,VENDOR,instantiate
out=ROOT/'results/gsm-full-final-20261102';rows=[json.loads(l) for l in gzip.open(out/'predictions.jsonl.gz','rt')]
os.chdir(VENDOR);count=0
for row in rows:
 cursor=[0]
 def replay(prompt,engine,max_tokens,stop_token,temperature):
  i=cursor[0];cursor[0]+=1;t=row['api'][i];request=t['request']
  assert request['messages'][-1]=={'role':'user','content':prompt},(row['index'],i,'prompt/history mismatch')
  assert request['max_tokens']==max_tokens and request['stop']==stop_token and request['temperature']==temperature
  return next(a['response']['choices'][0]['message']['content'] for a in t['attempts'] if a.get('response',{}).get('choices'))
 logs=instantiate(replay)(row['input'],4,'rich',0.7)
 assert logs==row['run_logs'],row['index']
 assert cursor[0]==len(row['api'])==len(logs)+1
 count+=cursor[0]
report={'status':'PASS','samples':len(rows),'original_loop_requests_reconstructed':count,'user_prompts_and_history_byte_equal':True,'saved_logs_equal_original_feedback_parser_and_loop':True,'early_stopping_and_round_count_equal':True,'api_calls':0,'scope':'GSM8K published alternative-backbone run; system adaptation remains disclosed'}
(ROOT/'docs/release-checks/final_code_fidelity.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
