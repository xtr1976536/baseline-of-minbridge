"""Offline release integrity, request/response alignment and metric verification."""
import argparse
import gzip
import hashlib
import json
import re
import sys
from pathlib import Path
from logic_final import ROOT, UPSTREAM, strip_markdown, cot_answer
from logical_deduction_cot import extract_ld_cot
sys.path.insert(0, str(UPSTREAM/'models'))
from evaluation import evaluate_QA


def load(path):
    text = gzip.decompress(path.read_bytes()).decode() if path.suffix == '.gz' else path.read_text()
    return json.loads(text)


def raw_logs(path):
    return [json.loads(line) for line in gzip.decompress(path.read_bytes()).decode().splitlines()]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');args=parser.parse_args()
    base=ROOT/'experiments/final';index=load(base/'index.json');checks=[]
    for dataset, entry in index['datasets'].items():
        folder=ROOT/entry['path'];data=load(UPSTREAM/f'data/{dataset}/dev.json');lookup={row['id']:row for row in data}
        programs=load(folder/'programs.json.gz');cot=load(folder/'cot.json.gz');n=entry['n']
        assert len(programs)==len(cot)==n==len(data)
        ids=set(lookup)
        for stage, rows in [('program',programs),('cot',cot)]:
            assert len({r['id'] for r in rows})==n and {r['id'] for r in rows}==ids
            logs=raw_logs(folder/(stage+'-api.jsonl.gz'));byid={r['id']:r for r in logs};assert len(logs)==len(byid)==n
            for row in rows:
                source=lookup[row['id']];log=byid[row['id']];response=log['response'];request=response['_minbridge_request']
                assert row['answer']==source['answer'] and row['question']==source['question']
                if stage=='program':assert row['context']==source['context'] and row['options']==source['options']
                assert request['model']=='gpt-5.6-sol' and request['temperature']==0 and request['top_p']==1 and request['max_tokens']==1024 and request['stop']=='------'
                assert request['messages']==[{'role':'user','content':log['prompt']}]
                raw=response['choices'][0]['message']['content'].strip()
                assert raw==(row['raw_logic_programs'][0] if stage=='program' else row['raw_output'])
                from logic_final import prompt_files
                program_template,cot_template=prompt_files(dataset)
                if stage=='program':
                    expected=program_template.read_text().replace('[[PROBLEM]]',source['context']).replace('[[QUESTION]]',source['question'].strip())
                    if dataset in ('LogicalDeduction','AR-LSAT'):
                        expected=expected.replace('[[CHOICES]]','\n'.join(f'({x.strip()}' for x in source['options']).strip())
                    assert log['prompt'].endswith(expected)
                else:
                    expected=cot_template.read_text().replace('[[CONTEXT]]',source['context'].strip()).replace('[[QUESTION]]',source['question'].strip()).replace('[[OPTIONS]]','\n'.join(x.strip() for x in source['options']))
                    assert log['prompt']==expected
        summary=load(folder/'summary.json');predictions=load(folder/'predictions.json.gz')
        assert len(predictions)==n and {r['id'] for r in predictions}==ids
        accuracy=evaluate_QA(predictions);exe=[r for r in predictions if r['flag']=='success']
        assert abs(accuracy-summary['accuracy'])<1e-12
        assert len(exe)==summary['executable'] and round(accuracy*n)==summary['correct']
        assert abs(len(exe)/n-summary['executable_rate'])<1e-12
        assert abs(evaluate_QA(exe)-summary['executable_accuracy'])<1e-12
        scored=[]
        for row in cot:
            answer=extract_ld_cot(row['raw_output'],len(lookup[row['id']]['options']))['predicted_answer'] if dataset=='LogicalDeduction' else strip_markdown(row['raw_predicted_answer'] if 'raw_predicted_answer' in row else row['raw_output'].split('The correct option is:')[-1].strip())
            scored.append(dict(row,predicted_answer=answer))
        assert abs(evaluate_QA(scored)-summary['cot_accuracy'])<1e-12
        assert hashlib.sha256((UPSTREAM/f'data/{dataset}/dev.json').read_bytes()).hexdigest()==entry['data_sha256']
        checks.append({'dataset':dataset,'samples':n,'verified_requests':2*n,'correct':summary['correct'],'all_pass':True})
    stand=base/'LogicalDeduction/standalone-cot';rows=load(stand/'cot.json.gz');summary=load(stand/'summary.json');logs=raw_logs(stand/'cot-api.jsonl.gz');assert len(logs)==len(rows)==300
    byid={r['row']['id']:r for r in logs};assert len(byid)==300
    for row in rows:
        record=byid[row['id']];assert row['raw_output']==record['response']['choices'][0]['message']['content'].strip()
        result=extract_ld_cot(row['raw_output'],record['option_count']);assert row['predicted_answer']==result['predicted_answer']
        request=record['response']['_minbridge_request'];assert request['messages']==[{'role':'user','content':record['prompt']}]
        assert all(request[k]==v for k,v in {'model':'gpt-5.6-sol','temperature':0,'top_p':1,'max_tokens':1024,'stop':'------'}.items())
    assert round(evaluate_QA(rows)*300)==summary['correct']==295
    # Scan every published payload, including decompressed logs, for credential material.
    for path in base.rglob('*'):
        if path.is_file():
            content=gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes()
            assert not re.search(rb'\b(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9_]{20,})\b',content),path
            assert b'Bearer sk-' not in content,path
    report={'all_pass':True,'main_runs':checks,'standalone_cot':{'n':300,'correct':295,'verified_requests':300},'total_requests':sum(c['verified_requests'] for c in checks)+300,'no_network_calls':True,'sensitive_data_scan':'passed'}
    if args.write:(ROOT/'reports/final-integrity.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
