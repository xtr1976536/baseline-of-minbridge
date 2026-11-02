"""Validate full GSM IDs, gold, call protocol, and transport-only resumption offline."""
import json,hashlib
from protocol import ROOT,VENDOR,check_corr
R=ROOT/'results/gsm-full-final-20261102';old=ROOT/'results/gsm-full-20261102'
import gzip
raw=(R/'predictions.jsonl').read_text() if (R/'predictions.jsonl').exists() else gzip.open(R/'predictions.jsonl.gz','rt').read()
rows=[json.loads(s) for s in raw.splitlines()];source=[json.loads(s) for s in (VENDOR/'data/tasks/gsm/gsm.jsonl').read_text().splitlines()];before={r['index']:r for r in map(json.loads,(old/'predictions.jsonl').read_text().splitlines())} if (old/'predictions.jsonl').exists() else {r['index']:r for r in map(json.loads,gzip.open(R/'transport_failure_records.jsonl.gz','rt'))}
success_hashes=json.loads((R/'first_pass_success_hashes.json').read_text())
assert len(rows)==len(source)==1319 and {r['index'] for r in rows}==set(range(1319))
reused=0;preserved=0;resumed=0;usage={k:0 for k in ['prompt_tokens','completion_tokens','total_tokens']}
for r in rows:
 assert r['input']==source[r['index']]['input'] and r['target']==source[r['index']]['target'] and r['status']=='generated'
 previous=before.get(r['index'])
 if previous is None:
  assert hashlib.sha256(json.dumps(r,ensure_ascii=False,sort_keys=True).encode()).hexdigest()==success_hashes[str(r['index'])]
  previous=r
 if previous['status']=='generated':assert r==previous;preserved+=1
 else:
  resumed+=1
  for i,t in enumerate(previous['api']):
   success=next((a['response'] for a in t['attempts'] if a.get('response',{}).get('choices')),None)
   if success:
    assert r['api'][i]['request']==t['request'];assert any(a.get('response')==success for a in r['api'][i]['attempts']);reused+=1
 assert 1<=len(r['run_logs'])<=4
 for i,t in enumerate(r['api']):
  req=t['request'];assert req['temperature']==0.7 and req['model']=='gpt-5.6-sol'
  assert req['max_tokens']==(300 if i==0 else 600);assert req['stop']== ('\n\n' if i==0 else '### END')
  for a in t['attempts']:
   if 'response' not in a:continue
   assert a['response']['choices'][0]['finish_reason']!='length'
   for k in usage:usage[k]+=a['response'].get('usage',{}).get(k,0) or 0
report={'status':'PASS','n':1319,'id_and_gold_alignment':True,'successful_first_pass_records_preserved':preserved,'transport_failure_samples_resumed':resumed,'successful_stage_responses_reused':reused,'all_round_caps_and_parameters_match':True,'usage_final_traces':usage,'note':'Usage counts final successful trace history once; failed transport attempts are separately archived. No model rerun for wrong answers.'}
(R/'release_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
