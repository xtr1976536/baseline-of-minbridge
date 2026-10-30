import json,os,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
os.environ.update(json.loads((R/'.runtime/graph-env.json').read_text()))
subprocess.run([sys.executable,str(R/'scripts/run_gbfr.py'),'--dataset','FinQA','--limit','1','--output',str(R/'results/gbfr-finqa-smoke')],check=True)
