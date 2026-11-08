"""Small, explicitly selected verification pilot on a frozen candidate pool."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import BoundedSemaphore
import json
import os
import time
from .common import read_jsonl,write_json,write_jsonl,digest,fingerprint
from .retrieval import chunks_from_pages
from .grounding import Filing
from .scoring import correctness,summarize


def frozen_evidence(root,config,row,previous):
    """Rebuild exactly the old round-robin top-K, without using gold pages."""
    pages=json.loads((root/'data/corpus'/(row['doc_name']+'.json')).read_text(encoding='utf-8'))['pages']
    c=config['retrieval']
    chunks=chunks_from_pages(row['doc_name'],pages,words=c['chunk_words'],overlap=c['chunk_overlap_words'])
    by_id={x.chunk_id:x for x in chunks}
    rankings=[t['reranked'] for t in previous['retrieval']]
    selected=[]
    for depth in range(max(map(len,rankings),default=0)):
        for ranking in rankings:
            if depth<len(ranking) and ranking[depth] not in selected:selected.append(ranking[depth])
            if len(selected)==c['top_k']:break
        if len(selected)==c['top_k']:break
    if not selected or any(x not in by_id for x in selected):raise ValueError('frozen_retrieval_cannot_be_reconstructed')
    evidence='\n\n'.join(by_id[x].text for x in selected)
    return evidence,{'chunk_ids':selected,'evidence_sha256':fingerprint(evidence),
                     'candidate_sha256':fingerprint(previous['raw_answer'])}


def run_pilot(root,config):
    from .client import Client
    from .pipeline import PaperVerifier
    from .runner import source_hashes,recover,check,selected_models
    if config.get('run_mode')!='diagnostic_pilot':raise ValueError('pilot_profile_required')
    manifest_path=root/config['pilot_manifest']
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    ids=manifest['ids'];n=len(ids)
    if not 1<=n<=20 or len(set(ids))!=n or n!=manifest['N']:raise ValueError('pilot_must_contain_1_to_20_frozen_unique_ids')
    if not check(root,config)['ready']:raise ValueError('assets_not_ready')
    source=root/manifest['frozen_candidate_source']
    baseline={r['id']:r for r in read_jsonl(source)}
    data={r['id']:r for r in read_jsonl(root/'data/main'/('FinanceBench.jsonl'))}
    if any(i not in baseline or i not in data for i in ids):raise ValueError('pilot_unknown_id')
    # Re-score both versions with the same current evaluator, without changing
    # either version's claims, verdicts, labels or numeric tolerances.
    for i in ids:baseline[i]={**baseline[i],'correct':correctness(data[i],baseline[i]['result'])}
    out=root/config['output_dir'];out.mkdir(parents=True,exist_ok=True)
    models=selected_models(config)
    if len(models)!=1:raise ValueError('pilot_single_requested_backbone_required')
    model=models[0];client=Client(config['models'][model],root/'runs/request-cache','FinanceBench')
    if not os.environ.get(config['models'][model]['api_key_env']):raise ValueError('missing_pilot_api_key')
    original_chat=client.chat;slots=BoundedSemaphore(config.get('concurrency',{}).get('api_requests',4))
    def bounded_chat(*args,**kwargs):
        if kwargs.get('stage') not in {'question_decomposition','fact_extraction','claim_value_parse'}:
            raise ValueError('pilot_forbids_answer_regeneration_or_feedback')
        with slots:return original_chat(*args,**kwargs)
    client.chat=bounded_chat
    identity=fingerprint({'config':config,'manifest_sha256':digest(manifest_path),
                          'candidate_source_sha256':digest(source),'asset_lock':digest(root/'data/assets.lock.json'),
                          'source_hashes':source_hashes(root)})
    metadata=out/'run.json'
    if metadata.exists() and json.loads(metadata.read_text(encoding='utf-8'))['identity']!=identity:
        raise ValueError('pilot_identity_changed_use_new_output_directory')
    write_json(metadata,{'identity':identity,'scope':'selected_diagnostic_pilot_not_full_evaluation','N':n,
                         'model':model,'config':config,'manifest':manifest,'source_hashes':source_hashes(root),
                         'candidate_source_sha256':digest(source),'same_candidates_and_retrieval':True})
    path=out/'predictions.jsonl';predictions=recover(path)
    if any(r['id'] not in ids for r in predictions):raise ValueError('pilot_journal_outside_manifest')
    done={r['id'] for r in predictions}
    def process(item_id):
        started=time.monotonic();row,old=data[item_id],baseline[item_id]
        evidence,provenance=frozen_evidence(root,config,row,old)
        try:result=PaperVerifier(client).verify(row['question'],old['raw_answer'],evidence,Filing.load(root/'data/filings'/(row['doc_name']+'.json')))
        except Exception as exc:result={'status':'ERROR','error_type':type(exc).__name__,'reason':str(exc)[:180]}
        # Gold is accessed here, only after the complete verifier returns.
        return {'id':item_id,'raw_answer':old['raw_answer'],'result':result,'correct':correctness(row,result),
                'frozen_input':provenance,'elapsed_seconds':round(time.monotonic()-started,3)}
    old_metrics=summarize([baseline[i] for i in ids],n)
    with ThreadPoolExecutor(max_workers=config.get('concurrency',{}).get('samples',4)) as pool:
        for record in pool.map(process,[i for i in ids if i not in done]):
            with path.open('a',encoding='utf-8') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())
            predictions.append(record)
            if record['result'].get('smtlib'):
                smt=out/'smt'/(record['id']+'.smt2');smt.parent.mkdir(exist_ok=True);smt.write_text(record['result']['smtlib'],encoding='utf-8')
            write_json(out/'metrics.json',{'before':old_metrics,'after':summarize(predictions,n)})
            print('PILOT',record['id'],record['result']['status'],record['result'].get('reason',''),flush=True)
    new_metrics=summarize(predictions,n)
    write_json(out/'metrics.json',{'before':old_metrics,'after':new_metrics})
    transitions=[{'id':r['id'],'before':baseline[r['id']]['result']['status'],'after':r['result']['status'],
                  'before_correct':baseline[r['id']].get('correct'),'after_correct':r['correct'],
                  'candidate_unchanged':r['raw_answer']==baseline[r['id']]['raw_answer']} for r in predictions]
    write_json(out/'transitions.json',transitions)
    lines=['# Frozen-candidate diagnostic pilot','',f'N={n}. Selected known-problem cases and controls; this is not an unbiased full-dataset estimate.',
           'Candidates, retrieval, labels and strict scoring are unchanged. No answer repair or regeneration.','',
           '| Version | TA | FA | TR | FR | Abs | Unresolved | Errors | Missing | Precision | Decision accuracy | Coverage |',
           '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for label,m in [('Before',old_metrics),('After',new_metrics)]:
        lines.append('| '+' | '.join([label,*[str(m[k]) for k in ['TA','FA','TR','FR','Abs','unresolved_decided','errors','missing']],
                         *['—' if m[k] is None else f'{100*m[k]:.2f}%' for k in ['precision','accuracy','coverage']]])+' |')
    lines += ['', 'Full evaluation has not been started. The previous complete run is retained separately.']
    report=out/'pilot_report.md';report.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return report
