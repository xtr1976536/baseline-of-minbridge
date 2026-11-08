"""Reverify the fixed 50 candidates and exact selected evidence; never generate."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import BoundedSemaphore
from copy import deepcopy
import json
import os
import time
from provider_credential import load
from vf_repro.common import read_jsonl,write_json,digest,fingerprint,dumps
from vf_repro.runner import check,source_hashes,recover,report
from vf_repro.client import Client
from vf_repro.pipeline import PaperVerifier
from vf_repro.grounding import Filing
from vf_repro.retrieval import chunks_from_pages
from vf_repro.scoring import correctness,summarize


def main():
    root=Path(__file__).resolve().parent.parent
    cfg_path=root/'configs/coverage50-v3.json';cfg=json.loads(cfg_path.read_text(encoding='utf-8'))
    manifest_path=root/cfg['validation_manifest'];manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    ids=manifest['ids'];assert 50<=len(ids)<67 and len(set(ids))==len(ids)
    assert cfg['run_mode']=='coverage_validation' and cfg['datasets']==['FinanceBench']
    assert list(cfg['models'])==['GPT-5.6-Sol'] and check(root,cfg)['ready']
    assert digest(root/'data/main/FinanceBench.jsonl')==manifest['dataset_sha256']
    lock=json.loads((root/cfg['validation_inputs_lock']).read_text(encoding='utf-8'))
    assert all(digest(root/k)==v for k,v in lock['files'].items())
    assert not any((root/k).exists() for k in lock['absent'])
    frozen=root/cfg['frozen_candidate_source'];assert digest(frozen)==cfg['frozen_candidate_sha256']
    previous=read_jsonl(frozen);assert [r['id'] for r in previous]==ids
    old={r['id']:r for r in previous};data={r['id']:r for r in read_jsonl(root/'data/main/FinanceBench.jsonl')}
    plan=json.loads((root/'research/coverage50_v3_run_plan.json').read_text(encoding='utf-8'))
    assert source_hashes(root)==plan['source_hashes'] and digest(cfg_path)==plan['config_sha256']
    assert digest(Path(__file__))==plan['validation_script_sha256']
    model='GPT-5.6-Sol';base=root/cfg['output_dir']/model/'FinanceBench';base.mkdir(parents=True,exist_ok=True)
    identity=fingerprint({'config':cfg,'manifest':digest(manifest_path),'sources':source_hashes(root),'frozen':digest(frozen)})
    metadata=base/'run.json'
    if metadata.exists():assert json.loads(metadata.read_text(encoding='utf-8'))['identity']==identity
    write_json(metadata,{'identity':identity,'N':len(ids),'paper_N':67,'model':model,'config':cfg,
        'same_candidates_and_evidence':True,'frozen_candidate_source_sha256':digest(frozen)})
    mc=cfg['models'][model]
    if not os.environ.get(mc['api_key_env']):os.environ[mc['api_key_env']]=load()
    client=Client(mc,root/'runs/request-cache','FinanceBench');original=client.chat
    slots=BoundedSemaphore(cfg['concurrency']['api_requests'])
    def bounded(messages,*args,**kwargs):
        assert kwargs.get('stage') in {'question_decomposition','fact_extraction','claim_value_parse'}
        with slots:return original(messages,*args,**kwargs)
    client.chat=bounded
    path=base/'predictions.jsonl';rows=recover(path);done={r['id'] for r in rows}
    assert done<=set(ids)
    def process(sid):
        started=time.monotonic();row=data[sid];prior=old[sid];c=cfg['retrieval']
        pages=json.loads((root/'data/corpus'/(row['doc_name']+'.json')).read_text(encoding='utf-8'))['pages']
        chunks=chunks_from_pages(row['doc_name'],pages,words=c['chunk_words'],overlap=c['chunk_overlap_words'],table_aware=c.get('table_aware',False))
        by_id={x.chunk_id:x for x in chunks};selected=prior['retrieval'][0]['selection']['ids']
        assert selected and len(selected)<=c['top_k'] and len(set(selected))==len(selected)
        evidence='\n\n'.join(by_id[k].text for k in selected)
        frozen_input={'chunk_ids':selected,'evidence_sha256':fingerprint(evidence),'candidate_sha256':fingerprint(prior['raw_answer'])}
        try:
            if not prior['raw_answer']:
                assert prior['result']['status']=='ABSTAIN';result=deepcopy(prior['result'])
            else:result=PaperVerifier(client).verify(row['question'],prior['raw_answer'],evidence,Filing.load(root/'data/filings'/(row['doc_name']+'.json'),source_rows=cfg['source_rows']))
        except Exception as exc:result={'status':'ERROR','error_type':type(exc).__name__,'reason':str(exc)[:180]}
        return {'id':sid,'raw_answer':prior['raw_answer'],'result':result,'correct':correctness(row,result),
            'retrieval':prior['retrieval'],'retrieval_plan':prior['retrieval_plan'],'frozen_input':frozen_input,
            'elapsed_seconds':round(time.monotonic()-started,3)}
    with ThreadPoolExecutor(max_workers=cfg['concurrency']['samples']) as pool:
        for r in pool.map(process,[i for i in ids if i not in done]):
            with path.open('a',encoding='utf-8') as f:f.write(dumps(r)+'\n');f.flush();os.fsync(f.fileno())
            rows.append(r)
            if r['result'].get('smtlib'):
                smt=base/'smt'/(r['id']+'.smt2');smt.parent.mkdir(exist_ok=True);smt.write_text(r['result']['smtlib'],encoding='utf-8')
            write_json(base/'metrics.json',summarize(rows,len(ids)))
            print('FROZEN50',r['id'],r['result']['status'],flush=True)
    assert [r['id'] for r in rows]==ids and all(r['raw_answer']==old[r['id']]['raw_answer'] for r in rows)
    report(root,cfg)


if __name__=='__main__':main()
