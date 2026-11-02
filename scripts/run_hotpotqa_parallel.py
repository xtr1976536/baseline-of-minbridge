"""Finish frozen 500-question HotpotQA plan with isolated per-process environments."""
import argparse,concurrent.futures,json,subprocess,sys,time,hashlib,random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def split_pending(ids,done):
 assert len(ids)==len(set(ids)) and set(done)<=set(ids)
 pending=[i for i in ids if i not in done]
 return [pending[i::4] for i in range(4)]

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path);p.add_argument('--resume',type=Path);a=p.parse_args()
 if a.resume:
  run=a.resume.resolve();plan=json.loads((run/'plan.json').read_text());source=Path(plan['source'])
 else:
  run=ROOT/'results'/f'react-hotpotqa-parallel-{time.time_ns()}';run.mkdir()
  if a.source:
   source=a.source.resolve();cfg=json.loads((source/'run.json').read_text());saved=[json.loads(l) for l in (source/'predictions.jsonl').read_text().splitlines()];ids=cfg['sampling']['sample_indices']
  else:
   source=run/'initial';source.mkdir();ids=list(range(7405));random.Random(233).shuffle(ids);ids=ids[:500];saved=[]
   (source/'predictions.jsonl').write_text('');(source/'run.json').write_text(json.dumps({'sampling':{'sample_indices':ids}}))
  done={r['index'] for r in saved};assert len(ids)==500 and len(done)==len(saved)
  shards=split_pending(ids,done)
  plan={'source':str(source),'source_predictions_sha256':hashlib.sha256((source/'predictions.jsonl').read_bytes()).hexdigest(),'sample_indices':ids,'completed_preserved':len(saved),'workers':4,'shards':shards,'adapter_sha256':hashlib.sha256((ROOT/'scripts/react_adapter.py').read_bytes()).hexdigest(),'note':'Frozen author seed233 500 IDs; preserve all completed answers including incorrect ones. Per-worker process/environment; steps sequential within a question. Interrupted questions restart, completed questions never regenerate.'}
  (run/'plan.json').write_text(json.dumps(plan,indent=2))
  for i,shard in enumerate(shards):(run/f'indices-{i}.json').write_text(json.dumps(shard))
 (ROOT/'logs/react-hotpotqa-parallel-current.txt').write_text(str(run));print('RUN',run,flush=True)
 def worker(i):
  if not plan['shards'][i]:return 0
  folder=run/f'worker-{i}';cmd=[sys.executable,str(ROOT/'scripts/run_react.py'),'--task','hotpotqa','--limit',str(len(plan['shards'][i])),'--sample-indices',str(run/f'indices-{i}.json')]
  cmd+=['--resume',str(folder)] if folder.exists() else ['--run-dir',str(folder)]
  with (run/f'worker-{i}.log').open('a') as log:return subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT).returncode
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  futures={pool.submit(worker,i):i for i in range(4)}
  for f in concurrent.futures.as_completed(futures):print('worker',futures[f],'exit',f.result(),flush=True)
 rows=[json.loads(l) for l in (source/'predictions.jsonl').read_text().splitlines()]
 assert hashlib.sha256((source/'predictions.jsonl').read_bytes()).hexdigest()==plan['source_predictions_sha256']
 for i in range(4):
  path=run/f'worker-{i}/predictions.jsonl'
  if path.exists():rows += [json.loads(l) for l in path.read_text().splitlines()]
 lookup={r['index']:r for r in rows};assert len(rows)==len(lookup) and set(lookup)<=set(plan['sample_indices'])
 ordered=[lookup[i] for i in plan['sample_indices'] if i in lookup]
 (run/'predictions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in ordered))
 report={'state':'complete' if len(rows)==500 else 'incomplete','n':len(rows),'requested':500,'correct':sum(bool(r['info']['em']) for r in rows),'accuracy':sum(bool(r['info']['em']) for r in rows)/len(rows),'preserved_previous':plan['completed_preserved'],'paper_hotpotqa_gpt3_appendix_em':.308,'paper_palm_main_em':.274,'note':'GPT-5.6 Chat substitute with disclosed formatting adapter; only completed episodes counted; incomplete report is not a full benchmark.'}
 (run/'summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
if __name__=='__main__':main()
