"""Verify coverage and recompute official scores; optional complete program replay."""
import argparse,concurrent.futures as cf,json,os,subprocess,sys
sys.dont_write_bytecode=True
from protocol import ROOT,VENDOR,official
sys.path.insert(0,str(VENDOR))
from tool import finqa_equal
OUT=ROOT/'results/finqa-full-greedy-20261102'
def main():
 p=argparse.ArgumentParser();p.add_argument('--replay',action='store_true');args=p.parse_args()
 _,_,data,_=official('finqa')
 paths=sorted((OUT/'samples').glob('*.json'))
 records=[json.loads(p.read_text()) for p in paths] if paths else [json.loads(line) for line in (OUT/'predictions.jsonl').read_text().splitlines()]
 assert len(records)==len(data)==1147
 assert {r['index'] for r in records}==set(range(1147));assert len({r['id'] for r in records})==1147
 for r in records:
  assert r['id']==data[r['index']]['id'];assert r['gold']==data[r['index']]['answer']
  assert r['correct']==finqa_equal(r.get('executed'),r['gold'],False)
 def replay(r):
  if 'code' not in r:return {'id':r['id'],'skip':'no generated code'}
  child=subprocess.run([sys.executable,str(ROOT/'scripts/execute_worker.py')],input=json.dumps({'task':'finqa','code':r['code']}),text=True,capture_output=True,timeout=20,cwd='/tmp',env={'PATH':os.environ.get('PATH',''),'PYTHONDONTWRITEBYTECODE':'1','OPENBLAS_NUM_THREADS':'1'})
  assert child.returncode==0,(r['id'],child.stderr)
  execution=json.loads(child.stdout);value=execution['value']
  if isinstance(value,bool):value='yes' if value else 'no'
  return {'id':r['id'],'score_matches':bool(finqa_equal(value,r['gold'],False))==bool(r['correct']),'value_matches':value==r.get('executed'),'replayed_status':execution['status']}
 replays=[]
 if args.replay:
  with cf.ThreadPoolExecutor(max_workers=8) as pool:replays=list(pool.map(replay,records))
 mismatches=[r for r in replays if r.get('score_matches') is False or r.get('value_matches') is False]
 report={'expected':1147,'count':len(records),'unique_ids':1147,'index_and_gold_alignment':'PASS','all_stored_scores_match_official_comparator':True,'full_program_replay_count':sum('skip' not in r for r in replays),'replay_mismatches':mismatches,'status':'PASS' if not mismatches else 'FAIL'}
 (OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report))
 if mismatches:raise SystemExit(1)
if __name__=='__main__':main()
