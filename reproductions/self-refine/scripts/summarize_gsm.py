"""Recompute initial/final/any-correct from frozen per-step executions; no API."""
import argparse,collections,json
from pathlib import Path
from protocol import ROOT,check_corr
p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();out=ROOT/'results'/a.output
rows=[json.loads(s) for s in (out/'predictions.jsonl').read_text().splitlines()]
for r in rows:
 for e in r['evaluations']:
  assert e['correct']==(bool(check_corr(e['value'],r['target'])) if e.get('value') is not None else False)
 assert r['initial_correct']==bool(r['evaluations'] and r['evaluations'][0]['correct'])
 assert r['final_correct']==bool(r['evaluations'] and r['evaluations'][-1]['correct'])
 assert r['any_correct']==any(e['correct'] for e in r['evaluations'])
n=len(rows);report={'n':n,'initial_correct':sum(r['initial_correct'] for r in rows),'final_correct':sum(r['final_correct'] for r in rows),'any_correct':sum(r['any_correct'] for r in rows),'run_errors':sum(r['status']!='generated' for r in rows),'status':'PASS','gains':sum(not r['initial_correct'] and r['final_correct'] for r in rows),'regressions':sum(r['initial_correct'] and not r['final_correct'] for r in rows),'round_counts':dict(collections.Counter(len(r.get('run_logs',[])) for r in rows))}
(out/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
