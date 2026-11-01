"""Final offline fidelity audit. Does not call model APIs or expose credentials."""
import json
import subprocess
from pathlib import Path
from logic_final import ROOT, UPSTREAM, DATASETS, FORMAT_FILE, digest

def main():
    checks=[]
    def add(name,passed,detail):checks.append({'check':name,'pass':bool(passed),'detail':detail})
    sizes={'ProntoQA':500,'ProofWriter':600,'FOLIO':204,'LogicalDeduction':300,'AR-LSAT':231}
    for dataset in DATASETS:
        from logic_final import prompt_files
        files=[UPSTREAM/f'data/{dataset}/dev.json',*prompt_files(dataset)]
        for path in files:
            rel=str(path.relative_to(UPSTREAM))
            add(rel,path.read_bytes()==subprocess.check_output(['git','show','HEAD:'+rel],cwd=UPSTREAM),'unchanged author source')
        rows=json.loads(files[0].read_text())
        add(dataset+' size',len(rows)==sizes[dataset] and len({r['id'] for r in rows})==len(rows),{'n':len(rows)})
    for rel in ['models/evaluation.py','models/symbolic_solvers/pyke_solver/pyke_solver.py','models/symbolic_solvers/csp_solver/csp_solver.py','models/symbolic_solvers/z3_solver/sat_problem_solver.py']:
        add(rel,(UPSTREAM/rel).read_bytes()==subprocess.check_output(['git','show','HEAD:'+rel],cwd=UPSTREAM),'author code unchanged')
    add('approved format prefix',len(FORMAT_FILE.read_text().split())==26,FORMAT_FILE.read_text().strip())
    entry=(ROOT/'scripts/evaluate_logic_experiment.py').read_text()
    add('author interpreters only','PaperPykeProgram' not in entry and '--interpreter' not in entry,'no alternative interpreter option')
    tracked=subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines()
    add('no credential tracked','.env' not in tracked,'local .env excluded')
    result={'checks':checks,'all_pass':all(c['pass'] for c in checks),'limitations':['26-word prefix and Markdown cleanup are declared compatibility changes.','Other datasets have not completed fresh full end-to-end runs.','AR-LSAT paper appendix/README says 230; released dataset has 231.','Prover9 runtime path patch only; no inference-logic edits.']}
    out=ROOT/'manifests/final-protocol-audit.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
    if not result['all_pass']:raise SystemExit(1)
if __name__=='__main__':main()
