"""Compare PoT release with pinned-source ConvFinQA zip without renaming dev as test."""
import hashlib,json,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];path=R.parents[1]/'.local/pot-source-audit/convfinqa.zip'
z=zipfile.ZipFile(path);dev=json.loads(z.read('data/dev.json'));private=json.loads(z.read('data/test_private.json'));pot=json.loads((R/'vendor/data/convfinqa_dev.json').read_text())
by_id={r['id']:r for r in dev};private_ids={r['id'] for r in private}
checks=[]
for row in pot:
 original=by_id[row['id']];annotation=original['annotation']
 checks.append({'id':row['id'],'dialogue_match':row['questions']==annotation['dialogue_break'],'last_answer_match':row['answer']==annotation['exe_ans_list'][-1]})
assert all(r['dialogue_match'] and r['last_answer_match'] for r in checks)
report={'source_url':'https://raw.githubusercontent.com/czyssrs/ConvFinQA/main/data.zip','archive_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'pot_count':len(pot),'source_dev_count':len(dev),'private_test_count':len(private),'matching_dev_ids':len(set(by_id)&{r['id'] for r in pot}),'matching_test_ids':len(private_ids&{r['id'] for r in pot}),'all_dialogues_and_final_gold_answers_match':True,'decision':'Use original PoT code dev-421; explicitly label dev-final-question. Paper Test label cannot be reproduced literally using released gold. Do not silently substitute private test or claim identical split.','per_id':checks}
(R/'results/convfinqa_split_audit.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='per_id'})
