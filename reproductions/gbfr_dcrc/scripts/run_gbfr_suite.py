"""Run only GBFR over four full public-release datasets, resumably."""
import json,os,subprocess,sys,time
from pathlib import Path
raise SystemExit('Full suite disabled by user on 2026-10-30. Finish audit and bounded checks first.')
R=Path(__file__).resolve().parents[1]
os.environ.update(json.loads((R/'.runtime/graph-env.json').read_text()))
for dataset in ['FinQA','TAT-QA','FinanceReasoning','CFBenchmark']:
 status={'status':'running','dataset':dataset,'actual_model':'gpt-5.6-sol','scope':'full public release, derived graph; not exact paper table replication','updated':time.time()}
 (R/'results/suite_status.json').write_text(json.dumps(status,indent=2))
 process=subprocess.run([sys.executable,str(R/'scripts/run_gbfr.py'),'--dataset',dataset,'--output',str(R/'results'/('gbfr-'+dataset+'-full'))])
 if process.returncode:
  status.update(status='failed',exit_code=process.returncode);(R/'results/suite_status.json').write_text(json.dumps(status,indent=2));sys.exit(process.returncode)
(R/'results/suite_status.json').write_text(json.dumps({'status':'generation_complete','evaluation':'pending protocol reconciliation'},indent=2))
