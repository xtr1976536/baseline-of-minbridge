"""Fresh LogicalDeduction CoT-only full run. Frozen prompts and extractor, four workers."""
import argparse,concurrent.futures,json,sys,time
from pathlib import Path
from logic_final import ROOT,UPSTREAM,build_prompt,atomic_json,digest
from logical_deduction_cot import extract_ld_cot
from run_logic_experiment import load_environment
from api_compat import generate
sys.path.insert(0,str(UPSTREAM/'models'))
from evaluation import evaluate_QA

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--resume',type=Path);args=parser.parse_args()
    load_environment();data=json.loads((UPSTREAM/'data/LogicalDeduction/dev.json').read_text());assert len(data)==300
    cfg={'n':300,'sample_ids':[r['id'] for r in data],'model':'gpt-5.6-sol','temperature':0.,'top_p':1.,'max_tokens':1024,'stop':'------','workers':4,'policy':'ld-explicit-option-v1','scope':'CoT only; no programs/solvers/other datasets','hashes':{str(p.relative_to(ROOT)):digest(p) for p in [UPSTREAM/'data/LogicalDeduction/dev.json',UPSTREAM/'baselines/icl_examples/LogicalDeduction_CoT.txt',ROOT/'scripts/logical_deduction_cot.py',ROOT/'scripts/logic_final.py']}}
    if args.resume:
        run=args.resume.resolve();assert json.loads((run/'plan.json').read_text())==cfg
    else:
        run=ROOT/'results'/f'ld-cot-full-{time.time_ns()}';(run/'records').mkdir(parents=True);atomic_json(run/'plan.json',cfg)
    (ROOT/'logs/ld-cot-full-current.txt').write_text(str(run));print('RUN',run,flush=True)
    records={}
    for path in (run/'records').glob('*.json'):
        record=json.loads(path.read_text());records[record['row']['id']]=record
    jobs=iter(r for r in data if r['id'] not in records);failures=[]
    def task(row):
        prompt=build_prompt('LogicalDeduction','cot',row);raw,response,style,model=generate(prompt,'gpt-4','gpt-5.6-sol','chat',1024,0.,'------',120)
        return {'row':{'id':row['id'],'question':row['question'],'answer':row['answer'],**extract_ld_cot(raw,len(row['options']))},'prompt':prompt,'response':response,'option_count':len(row['options'])}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        pending={}
        def submit():
            row=next(jobs,None)
            if row:pending[pool.submit(task,row)]=row['id']
        for _ in range(4):submit()
        while pending:
            ready,_=concurrent.futures.wait(pending,return_when=concurrent.futures.FIRST_COMPLETED)
            for future in ready:
                id=pending.pop(future)
                try:
                    record=future.result();atomic_json(run/'records'/(id+'.json'),record);records[id]=record
                    atomic_json(run/'status.json',{'state':'generating','cot':len(records),'n':300});print('CoT',len(records),'/300',flush=True)
                except Exception as ex:failures.append({'id':id,'error':type(ex).__name__+': '+str(ex)})
                if not failures:submit()
    if failures:
        atomic_json(run/'failures.json',failures);atomic_json(run/'status.json',{'state':'stopped_on_failure','cot':len(records),'n':300});raise SystemExit('Saved checkpoint; explicit resume required')
    assert set(records)==set(cfg['sample_ids'])
    rows=[]
    for source in data:
        record=records[source['id']];row=record['row'];request=record['response']['_minbridge_request'];assert request['messages']==[{'role':'user','content':build_prompt('LogicalDeduction','cot',source)}]
        for key in ('model','temperature','top_p','max_tokens','stop'):assert request[key]==cfg[key]
        raw=record['response']['choices'][0]['message']['content'].strip();assert raw==row['raw_output'];assert extract_ld_cot(raw,len(source['options']))=={k:v for k,v in row.items() if k not in ('id','question','answer')};rows.append(row)
    old=[dict(r,predicted_answer=r['markdown_only_predicted_answer']) for r in rows]
    summary={'n':300,'correct':round(evaluate_QA(rows)*300),'accuracy':evaluate_QA(rows),'markdown_only_correct':round(evaluate_QA(old)*300),'markdown_only_accuracy':evaluate_QA(old),'paper_gpt4_cot':.7525,'extraction_reasons':{},'requests_verified':300,'errors':[r for r in rows if not evaluate_QA([r])],'note':'Fresh CoT-only run; explicit option extraction is disclosed compatibility change; other results unchanged.'}
    for row in rows:
        key=row['cot_extraction']['reason'];summary['extraction_reasons'][key]=summary['extraction_reasons'].get(key,0)+1
    atomic_json(run/'cot.json',rows);atomic_json(run/'summary.json',summary);atomic_json(run/'status.json',{'state':'complete','cot':300,'n':300});print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
