"""Print one explicit final run summary. Never guesses the latest file or overwrites docs."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);a=p.parse_args()
s=json.loads((a.run/'summary.json').read_text())
print(json.dumps({k:s[k] for k in ('dataset','n','accuracy','executable_rate','executable_accuracy','cot_accuracy','fallback_count')},ensure_ascii=False,indent=2))
