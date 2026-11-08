from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
import json
import os
from pathlib import Path
import subprocess
from threading import BoundedSemaphore, Lock
import time
from urllib.parse import urlparse,unquote
from .common import *

def config_at(path):
    path = Path(path).resolve()
    c = json.loads(path.read_text(encoding='utf-8'))
    paper=(c.get('scope')=='verifin-v3-table4-only' and set(c['models'])==set(MODELS))
    override=c.get('backbone_override',{})
    requested=(c.get('scope')=='verifin-main-user-backbone' and override.get('source')=='explicit_user_request'
               and len(c.get('models',{}))==1 and
               next(iter(c['models'].values())).get('model')==override.get('requested_model'))
    if not paper and not requested:raise ValueError('unrecognized_paper_or_explicit_user_backbone_profile')
    selected_datasets(c)
    return path.parent.parent, c

def selected_models(config,override=None):
    configured=list(config.get('models',dict.fromkeys(MODELS)))
    selected=configured if override is None else list(override)
    if not selected or len(set(selected))!=len(selected) or not set(selected)<=set(configured):
        raise ValueError('requested_models_outside_configured_experiment_scope')
    return selected

def selected_datasets(config, override=None):
    configured=config.get('datasets',['XBRLFiling','FinanceBench'])
    if (not isinstance(configured,list) or not 1<=len(configured)<=2
            or len(set(configured))!=len(configured) or any(n not in DATASETS for n in configured)):
        raise ValueError('configure_one_or_two_distinct_known_datasets')
    selected=configured if override is None else list(override)
    if not selected or len(set(selected))!=len(selected) or not set(selected)<=set(configured):
        raise ValueError('requested_datasets_outside_configured_experiment_scope')
    return selected

def asset_hashes(root,datasets=None):
    selected=datasets or ['XBRLFiling','FinanceBench']
    main=root/'data/main'
    manifest=json.loads((main/'manifest.json').read_text(encoding='utf-8'))
    refs=json.loads((main/'documents.json').read_text(encoding='utf-8'))
    hashes={}
    for name in selected:
        path=main/(name+'.jsonl')
        hashes[path.relative_to(root).as_posix()]=digest(path)
        docs={r['doc_name'] for r in read_jsonl(path)}
        hashes['data/main/manifest.json#'+name]=fingerprint({
            'dataset':manifest['datasets'][name],
            'policy':{k:v for k,v in manifest.items() if k not in {'datasets','tat_scope_note','tat_revision'}}})
        hashes['data/main/documents.json#'+name]=fingerprint({d:refs[d] for d in sorted(docs)})
        for doc in sorted(docs):
            files=[root/'data/filings'/(doc+'.json')]
            if name=='FinanceBench':files.append(root/'data/corpus'/(doc+'.json'))
            for p in files:
                if p.exists():hashes[p.relative_to(root).as_posix()]=digest(p)
    return hashes

def check(root, config, datasets=None, *, require_lock=True):
    selected = selected_datasets(config,datasets)
    report = {'scope':config['scope'],'paper_snapshot_equivalence_claimed':False,'datasets':{},'issues':[]}
    path = root/'data/main/manifest.json'
    if not path.exists():
        return {**report,'ready':False,'issues':['run_prepare_first']}
    manifest = json.loads(path.read_text(encoding='utf-8'))
    if manifest.get('predictions_used') is not False: report['issues'].append('invalid_selection_manifest')
    refs = json.loads((root/'data/main/documents.json').read_text(encoding='utf-8'))
    import verifiqa
    if not Path(verifiqa.__file__).resolve().is_relative_to((root/'upstream/src').resolve()):
        report['issues'].append('imported_upstream_package_from_wrong_location')
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root/'upstream',text=True).strip()
    if revision!=UPSTREAM_COMMIT:report['issues'].append('upstream_revision_changed')
    for name in selected:
        p = root/'data/main'/(name+'.jsonl')
        if not p.exists():
            report['datasets'][name]={'ready':False,'issues':['final_subset_not_prepared'],'paper_n':DATASETS[name]}; continue
        rows = read_jsonl(p)
        issues, missing_filings, missing_corpus, unavailable, source_gaps = [], [], [], [], []
        item = manifest['datasets'][name]
        if digest(p) != item['processed_sha256']: issues.append('dataset_hash_changed')
        if len({r['id'] for r in rows})!=len(rows) or [r['id'] for r in rows]!=item['ids']: issues.append('dataset_identity_changed')
        if any(not r.get('question') or not isinstance(r.get('context'),str) or not r['context'].strip() for r in rows):issues.append('invalid_question_or_document_text')
        if name != 'TAT-DQA' and len(rows)!=DATASETS[name]: issues.append('unexpected_exact_subset_size')
        for doc in sorted({r['doc_name'] for r in rows}):
            if doc not in refs: issues.append('missing_filing_reference:'+doc)
            if not (root/'data/filings'/(doc+'.json')).exists(): missing_filings.append(doc)
            else:
                filing=json.loads((root/'data/filings'/(doc+'.json')).read_text(encoding='utf-8'))
                if filing.get('missing_optional_sources'):source_gaps.append({'doc_name':doc,'sources':filing['missing_optional_sources']})
                if filing.get('status')=='source_has_no_XBRL':unavailable.append(doc)
                elif filing.get('instance_sha256'):
                    raw=root/'data/raw/filings'/doc/unquote(Path(urlparse(filing['source_url']).path).name)
                    if not raw.exists() or digest(raw)!=filing['instance_sha256']:issues.append('raw_XBRL_provenance_changed:'+doc)
            if name=='FinanceBench' and not (root/'data/corpus'/(doc+'.json')).exists(): missing_corpus.append(doc)
            elif name=='FinanceBench':
                corpus=json.loads((root/'data/corpus'/(doc+'.json')).read_text(encoding='utf-8'))
                raw=root/'data/raw/documents'/(doc+('.html' if corpus.get('source_format')=='same_SEC_filing_HTML_fallback' else '.pdf'))
                if not raw.exists() or digest(raw)!=corpus['source_sha256']:issues.append('raw_document_provenance_changed:'+doc)
        if missing_filings: issues.append('primary_XBRL_files_pending')
        if missing_corpus: issues.append('source_documents_pending')
        report['datasets'][name]={'ready':not issues,'n':len(rows),'paper_n':DATASETS[name],
            'same_count_as_paper':len(rows)==DATASETS[name], 'selection':item['selection'],
            'issues':issues,'missing_filings':missing_filings,'missing_corpus':missing_corpus,
            'documented_without_XBRL':unavailable,'optional_source_gaps':source_gaps}
    if require_lock:
        lock = root/'data/assets.lock.json'
        if not lock.exists(): report['issues'].append('assets_not_frozen')
        else:
            frozen=json.loads(lock.read_text(encoding='utf-8'))
            if frozen.get('schema_version')!=2 or not set(selected)<=set(frozen.get('datasets',[])):
                report['issues'].append('asset_lock_scope_changed')
            elif any(frozen['files'].get(k)!=v for k,v in asset_hashes(root,selected).items()):
                report['issues'].append('frozen_assets_changed')
    report['ready'] = not report['issues'] and all(x['ready'] for x in report['datasets'].values())
    return report

def recover(path):
    if not path.exists(): return []
    raw = path.read_bytes()
    lines = raw.splitlines(keepends=True)
    rows = []
    for i, line in enumerate(lines):
        if not line.strip(): continue
        try: rows.append(json.loads(line))
        except (json.JSONDecodeError,UnicodeDecodeError):
            if i==len(lines)-1 and not line.endswith(b'\n'):
                path.write_bytes(b''.join(lines[:i])); break
            raise ValueError('corrupt_prediction_journal') from None
    if rows and not path.read_bytes().endswith(b'\n'):
        with path.open('ab') as f: f.write(b'\n')
    if len({r['id'] for r in rows})!=len(rows): raise ValueError('duplicate_prediction_journal_id')
    return rows

def source_hashes(root):
    return {p.relative_to(root).as_posix():digest(p) for directory in ['src','upstream/src']
            for p in sorted((root/directory).rglob('*')) if p.suffix in {'.py','.json','.txt'} and p.is_file()}

def run_cell(root,cfg,name,model,retriever,*,retry_errors=False):
    from .client import Client,ApiError
    from .pipeline import PaperVerifier
    from .grounding import Filing
    from .retrieval import chunks_from_pages,plan_retrieval
    from .scoring import correctness,summarize
    from verifiqa.generation.answer_generator import AnswerGenerator
    if cfg.get('generation',{}).get('preserve_precision'):
        from .generation import AnswerGenerator
    rows = read_jsonl(root/'data/main'/(name+'.jsonl'))
    validation_identity={}
    if cfg.get('run_mode')=='coverage_validation':
        manifest_path=root/cfg['validation_manifest']
        manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
        wanted=manifest['ids']
        requested_size=cfg.get('validation_sample_size',50)
        if requested_size not in {35,50}:raise ValueError('unsupported_validation_sample_size')
        valid_size=(len(wanted)==35) if requested_size==35 else 50<=len(wanted)<len(rows)
        if name!='FinanceBench' or not valid_size or len(set(wanted))!=len(wanted):
            if requested_size==35:raise ValueError('coverage_validation_requires_exactly_35_unique_ids')
            raise ValueError('coverage_validation_requires_50_or_more_unique_ids_below_full_dataset')
        if digest(root/'data/main'/(name+'.jsonl'))!=manifest['dataset_sha256']:raise ValueError('validation_dataset_changed')
        lookup={r['id']:r for r in rows}
        if any(i not in lookup for i in wanted):raise ValueError('unknown_validation_id')
        rows=[lookup[i] for i in wanted]
        lock_path=root/cfg['validation_inputs_lock'];lock=json.loads(lock_path.read_text(encoding='utf-8'))
        if any(digest(root/k)!=v for k,v in lock['files'].items()):raise ValueError('validation_extra_sources_changed')
        if any((root/k).exists() for k in lock.get('absent',[])):raise ValueError('validation_previously_absent_source_appeared')
        validation_identity={'manifest_sha256':digest(manifest_path),'extra_inputs_lock_sha256':digest(lock_path)}
    out = root/cfg['output_dir']/model/name
    out.mkdir(parents=True,exist_ok=True)
    effective = dict(cfg['models'][model])
    effective['effective_base_url'] = os.environ.get(effective.get('base_url_env',''),effective.get('base_url',''))
    identity = fingerprint({'config':cfg,'endpoint':effective,'dataset':name,'model':model,
        'sources':source_hashes(root),'assets':digest(root/'data/assets.lock.json'),'validation':validation_identity})
    metadata = out/'run.json'
    if metadata.exists() and json.loads(metadata.read_text(encoding='utf-8'))['identity']!=identity:
        raise ValueError('run_identity_changed_use_a_new_output_directory')
    write_json(metadata,{'identity':identity,'dataset':name,'model':model,'N':len(rows),'paper_N':DATASETS[name],
                         'paper_snapshot_equivalence_claimed':False,'config':cfg,'effective_endpoint':effective['effective_base_url']})
    path = out/'predictions.jsonl'
    predictions = recover(path)
    ids = {r['id'] for r in rows}
    if any(p['id'] not in ids for p in predictions): raise ValueError('journal_contains_unknown_sample')
    if retry_errors:
        predictions = [p for p in predictions if p['result']['status']!='ERROR']
        write_jsonl(path,predictions)
    done = {r['id'] for r in predictions}
    client = Client(cfg['models'][model],root/'runs/request-cache',name)
    concurrency = cfg.get('concurrency', {})
    workers, api_requests = concurrency.get('samples', 1), concurrency.get('api_requests', 4)
    if type(workers) is not int or not 1 <= workers <= 8 or type(api_requests) is not int or not 1 <= api_requests <= 8:
        raise ValueError('concurrency_must_be_integer_between_1_and_8')
    # A shared cap includes operand-extraction requests spawned inside each row.
    slots, retrieval_lock = BoundedSemaphore(api_requests), Lock()
    original_chat = client.chat
    def limited_chat(*args, **kwargs):
        with slots:
            return original_chat(*args, **kwargs)
    client.chat = limited_chat
    answerer, verifier = AnswerGenerator(client), PaperVerifier(client)
    def process(row):
        started = time.monotonic()
        answer, traces, chunks, plan = '', [], [], None
        try:
            # Runtime explicitly selects inputs; never passes gold/proofs/derivations.
            question, doc = row['question'],row['doc_name']
            if name=='FinanceBench':
                corpus=json.loads((root/'data/corpus'/(doc+'.json')).read_text(encoding='utf-8'))
                if cfg['retrieval'].get('html_table_rows'):
                    from .document_tables import augment_pages
                    pages=augment_pages(root,doc,corpus)
                else:pages=corpus['pages']
            else: pages=[{'page':0,'text':row['context']}]
            chunks=chunks_from_pages(doc,pages,words=cfg['retrieval']['chunk_words'],overlap=cfg['retrieval']['chunk_overlap_words'],table_aware=cfg['retrieval'].get('table_aware',False))
            plan=plan_retrieval(question,client,expand=cfg['retrieval'].get('expand_registry_roles',False))
            # One local encoder/reranker is shared; its caches and native model
            # execution remain serial while independent network requests overlap.
            with retrieval_lock:
                selected,traces=retriever.retrieve(question,plan,chunks,doc)
            if not selected: result={'status':'ABSTAIN','reason':'no_document_local_evidence'}
            else:
                # No formula context is supplied to the answer generator.
                try:answer=answerer.generate(question,selected,retrieval_plan=plan)
                except ValueError:
                    result={'status':'ABSTAIN','reason':'candidate_generation_produced_no_usable_answer'}
                except ApiError as exc:
                    if str(exc)!='truncated_response':raise
                    result={'status':'ABSTAIN','reason':'candidate_generation_token_budget_exhausted'}
                else:
                    evidence='\n\n'.join(x.text for x in selected)
                    result=verifier.verify(question,answer,evidence,Filing.load(root/'data/filings'/(doc+'.json'),source_rows=cfg.get('source_rows',False)))
        except Exception as exc:
            # Infrastructure/parsing errors are never reported as successful abstentions.
            result={'status':'ERROR','error_type':type(exc).__name__,'reason':str(exc)[:180]}
        record={'id':row['id'],'raw_answer':answer,'result':result,'correct':correctness(row,result),
                'retrieval_plan':asdict(plan) if plan else None,'retrieval':traces,
                'elapsed_seconds':round(time.monotonic()-started,3)}
        if cfg.get('evaluation',{}).get('secondary_financebench_rounding'):
            record['correct_legacy_display_precision']=record['correct']
            record['correct_financebench_rounding']=correctness(row,result,policy='financebench_currency_padding_v1')
            if cfg['evaluation'].get('primary_scoring_policy')=='financebench_currency_padding_v1':record['correct']=record['correct_financebench_rounding']
        return record
    pending = [row for row in rows if row['id'] not in done]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        # map yields in input order: workers never write the journal or metrics.
        for record in pool.map(process, pending):
            result = record['result']
            with path.open('a',encoding='utf-8') as f:
                f.write(dumps(record)+'\n');f.flush();os.fsync(f.fileno())
            if result.get('smtlib'):
                p=out/'smt'/(record['id']+'.smt2');p.parent.mkdir(exist_ok=True);p.write_text(result['smtlib'],encoding='utf-8')
            predictions.append(record)
            write_json(out/'metrics.json',summarize(predictions,len(rows)))
            if cfg.get('evaluation',{}).get('secondary_financebench_rounding'):
                write_json(out/'metrics_legacy_display_precision.json',summarize([{**r,'correct':r['correct_legacy_display_precision']} for r in predictions],len(rows)))
                write_json(out/'metrics_financebench_rounding.json',summarize([{**r,'correct':r['correct_financebench_rounding']} for r in predictions],len(rows)))
            print(model,name,record['id'],result['status'],flush=True)
    return summarize(predictions,len(rows))

def report(root,cfg):
    lines=['# VeriFin main experiment','', 'Only new local runs are shown. Published/archived author outputs are not local measurements.','',
           '| Model | Dataset | N | TA | FA | TR | FR | Abs | Unresolved | Errors | Missing | Precision [95% CI] | Decision accuracy [95% CI] | Coverage [95% CI] | Status |',
           '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    for model in selected_models(cfg):
        for name in selected_datasets(cfg):
            p=root/cfg['output_dir']/model/name/'metrics.json'
            if not p.exists(): lines.append('| '+' | '.join([model,name,'—',*['']*11,'not run'])+' |');continue
            m=json.loads(p.read_text(encoding='utf-8'))
            vals=[model,name,str(m['N']),*[str(m[k]) for k in ['TA','FA','TR','FR','Abs','unresolved_decided','errors','missing']],
                *['—' if m[k] is None else f'{100*m[k]:.2f}% [{100*m[k+"_ci95"][0]:.2f}, {100*m[k+"_ci95"][1]:.2f}]' for k in ['precision','accuracy','coverage']],
                'complete' if m['complete'] else 'incomplete/errors']
            lines.append('| '+' | '.join(vals)+' |')
    lines += ['', 'Intervals are exact 95% Clopper–Pearson intervals. Unresolved correctness is excluded from precision and decision accuracy, and retained in coverage. Errors and missing rows are reported separately from abstentions.',
              '', 'TA/FA: correct/incorrect accepted claims. TR/FR: incorrect/correct rejected claims. Precision = TA/(TA+FA); decision accuracy = (TA+TR)/(TA+FA+TR+FR); coverage includes every non-abstaining decision.']
    if cfg.get('scope')=='verifin-main-user-backbone':
        lines += ['', 'The backbone is an explicit user override. This is a method reproduction with documented public-asset differences, not a claim of numerical equivalence to the paper’s original backbone runs.']
    path=root/cfg['output_dir']/'main_results.md';path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return path

def main():
    p=argparse.ArgumentParser(description='VeriFin v3 main model/main experiment only')
    p.add_argument('command',choices=['prepare','discover-tat','discover-financebench','download-filings','download-documents','check','lock','run','validate','pilot','report'])
    p.add_argument('--config',type=Path,default=Path('configs/main.json'))
    p.add_argument('--models',nargs='+')
    p.add_argument('--datasets',nargs='+',choices=tuple(DATASETS))
    p.add_argument('--retry-errors',action='store_true')
    args=p.parse_args()
    root,cfg=config_at(args.config)
    try:
        if args.command in {'prepare','discover-tat','discover-financebench','download-filings','download-documents'}:
            from .assets import prepare,discover_tat,discover_financebench,acquire_filings,acquire_documents
            operation={'prepare':prepare,'discover-tat':discover_tat,'discover-financebench':discover_financebench,'download-filings':acquire_filings,'download-documents':acquire_documents}[args.command]
            result=operation(root,selected_datasets(cfg,args.datasets)) if args.command in {'prepare','download-filings'} else operation(root)
            print(dumps({'command':args.command,'items':len(result)}));return
        if args.command=='check':
            result=check(root,cfg,args.datasets)
            write_json(root/'research/readiness.json',result)
            print(json.dumps(result,ensure_ascii=False,indent=2));return
        if args.command=='lock':
            status=check(root,cfg,require_lock=False)
            if not status['ready']: raise ValueError('assets_not_ready_run_check')
            selected=selected_datasets(cfg)
            write_json(root/'data/assets.lock.json',{'schema_version':2,'datasets':selected,
                       'paper_sha256':PAPER_SHA256,'files':asset_hashes(root,selected),'predictions_used':False})
            print('Assets frozen');return
        if args.command in {'run','validate'}:
            if cfg.get('run_mode')=='diagnostic_pilot':raise ValueError('pilot_profile_cannot_start_a_full_run_use_pilot_command')
            if (args.command=='validate')!=(cfg.get('run_mode')=='coverage_validation'):
                raise ValueError('validation_profile_and_validate_command_must_be_used_together')
            status=check(root,cfg,args.datasets)
            if not status['ready']: raise ValueError('assets_not_ready_run_check')
            # Validate all requested endpoints/credentials BEFORE loading models/calling any API.
            for name in selected_models(cfg,args.models):
                c=cfg['models'][name]
                if not os.environ.get(c.get('base_url_env',''),c.get('base_url','')): raise ValueError('missing_endpoint:'+name)
                if not os.environ.get(c['api_key_env']) and not c.get('allow_empty_key'): raise ValueError('missing_api_key_env:'+c['api_key_env'])
            from .retrieval import Retriever
            retriever=Retriever(cfg['retrieval'],root/'runs/embeddings')
            for model in selected_models(cfg,args.models):
                for name in selected_datasets(cfg,args.datasets):run_cell(root,cfg,name,model,retriever,retry_errors=args.retry_errors)
        if args.command=='pilot':
            from .pilot import run_pilot
            print(run_pilot(root,cfg));return
        print(report(root,cfg))
    except (ValueError,FileNotFoundError) as exc:
        p.exit(2,'Experiment not ready: '+str(exc)+'\n')

if __name__=='__main__': main()
