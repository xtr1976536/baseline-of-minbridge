"""Inventory the pinned official release without sampling or changing its data."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def audit():
 rows=[]
 for p in sorted((ROOT/'vendor/gbfr/data').rglob('*.json')):
  data=json.loads(p.read_text()); rows.append(dict(file=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),count=len(data),fields=sorted(data[0])))
 report={'files':rows,'paper_table4':{'FinQA':[1002,97],'TAT-QA':[1119,151],'FinanceReasoning':[2238,412],'CFBenchmark':[140,11]},'status':'data_version_mismatch_FinQA_and_TATQA; no exact-main-table claim'}
 (ROOT/'results/data_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 return report
if __name__=='__main__': print(json.dumps(audit(),ensure_ascii=False,indent=2))
