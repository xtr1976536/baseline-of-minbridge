"""Offline verification of final HotpotQA release. No API calls."""
import gzip,json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'upstream/ReAct'))
from wrappers import normalize_answer,f1_score

def lines(path):return [json.loads(l) for l in gzip.decompress(path.read_bytes()).decode().splitlines()]
def main():
 base=ROOT/'experiments/react/hotpotqa';rows=lines(base/'predictions.jsonl.gz');s=json.loads((base/'summary.json').read_text());plan=json.loads((base/'plan.json').read_text());data=json.loads((ROOT/'upstream/ReAct/data/hotpot_dev_v1_simplified.json').read_text());ids=list(range(7405));random.Random(233).shuffle(ids)
 assert len(rows)==len({r['index'] for r in rows})==500 and [r['index'] for r in rows]==ids[:500]==plan['sample_indices']
 for r in rows:
  info=r['info'];gold=data[r['index']]['answer'];assert info['gt_answer']==gold
  assert bool(info['em'])==(normalize_answer(info['answer'])==normalize_answer(gold))
  assert abs(info['f1']-f1_score(info['answer'],gold)[0])<1e-12
 parts=lines(base/'initial-34/predictions.jsonl.gz')
 lookup={r['index']:r for r in rows}
 for r in parts:assert lookup[r['index']]==r
 for i in range(4):
  batch=lines(base/f'worker-{i}/predictions.jsonl.gz');assert set(r['index'] for r in batch)==set(plan['shards'][i]);parts+=batch
 assert len(parts)==500 and len({r['index'] for r in parts})==500
 calls=0
 for folder in ['initial-34']+[f'worker-{i}' for i in range(4)]:
  for call in lines(base/folder/'api.jsonl.gz'):
   req=call['response']['_minbridge_request'];assert req['model']=='gpt-5.6-sol' and req['temperature']==0 and req['max_tokens']==100
   assert req['messages']==[{'role':'user','content':call['prompt']}];assert call['prompt'].endswith(call['original_author_prompt']);calls+=1
 assert sum(bool(r['info']['em']) for r in rows)==s['correct']==246
 assert abs(sum(r['info']['f1'] for r in rows)/500-s['f1'])<1e-12
 print(json.dumps({'all_pass':True,'n':500,'correct':246,'em':.492,'f1':s['f1'],'preserved':34,'verified_saved_api_calls':calls,'model_calls':0},indent=2))
if __name__=='__main__':main()
