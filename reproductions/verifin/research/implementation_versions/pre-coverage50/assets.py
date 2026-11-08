"""Pinned dataset preparation and reacquisition of primary-source filing assets."""
from __future__ import annotations
from collections import Counter
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import re
import time
from urllib.parse import urlparse
from urllib.parse import parse_qs
import base64
from datetime import datetime
import threading
from xml.etree import ElementTree as ET
import zipfile
import httpx
from .common import *

_SEC_LOCK=threading.Lock()
_SEC_LAST=0.0

def fetch(url, path, *, sec=False):
    global _SEC_LAST
    path = Path(path)
    if path.exists() and path.stat().st_size: return path
    headers = {'User-Agent':'VeriFin-paper-reproduction/0.1'}
    if sec:
        agent = os.environ.get('SEC_USER_AGENT','').strip()
        if not agent or '@' not in agent:
            raise ValueError('Set SEC_USER_AGENT to project name and monitored contact email before SEC requests')
        headers['User-Agent'] = agent
        with _SEC_LOCK:
            time.sleep(max(0,.27-(time.monotonic()-_SEC_LAST)))
            _SEC_LAST=time.monotonic()
    path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(4):
        try:
            with httpx.Client(follow_redirects=True, timeout=httpx.Timeout(60,connect=20)) as c:
                r = c.get(url, headers=headers)
            r.raise_for_status()
            temp = path.with_suffix(path.suffix+'.part')
            temp.write_bytes(r.content)
            temp.replace(path)
            return path
        except httpx.HTTPError as exc:
            if isinstance(exc,httpx.HTTPStatusError) and exc.response.status_code not in {408,429,500,502,503,504}:raise
            if attempt == 3: raise
            time.sleep(2**attempt)

def scalar(value):
    if value is None:return None
    if isinstance(value,list):
        if len(value) != 1: return None
        value = value[0]
    if isinstance(value,bool): return None
    text = str(value).strip().replace(',','').replace('$','').rstrip('%').strip()
    if text.lower()=='zero': return '0'
    if text.startswith('(') and text.endswith(')'): text = '-'+text[1:-1]
    try:
        d = Decimal(text)
        return str(d) if d.is_finite() else None
    except InvalidOperation: return None

def prepare(root,selected=None):
    root = Path(root)
    selected=selected or ['XBRLFiling','FinanceBench']
    raw, out = root/'data/raw', root/'data/main'
    raw.mkdir(parents=True, exist_ok=True)
    datasets, refs = {}, {}
    def finish():
        write_json(out/'documents.json',refs)
        manifest={'paper_sha256':PAPER_SHA256,'upstream_commit':UPSTREAM_COMMIT,
            'datasets':datasets,'predictions_used':False,'data_policy':'paper-method-source-reconstruction-v1','gold_changes':[]}
        if 'TAT-DQA' in selected:
            manifest.update(tat_revision=TAT_REVISION,tat_scope_note='Official test split is a disclosed reconstruction assumption; the v3 403 IDs/split are not released.')
        write_json(out/'manifest.json',manifest)
        write_json(root/'research/data_audit.json',manifest)
        return manifest
    for name, file, metadata in [
        ('XBRLFiling','data/multicompany_provable/data/provable_calcrequired.jsonl','datasets/xbrlbench-600/documents.jsonl'),
        ('FinanceBench','data/numerical_questions.jsonl','datasets/financebench-67/documents.jsonl')]:
        if name not in selected:continue
        source = root/'upstream'/file
        rows = read_jsonl(source)
        docs = {d['doc_name']: d for d in read_jsonl(root/'upstream'/metadata)}
        normalized = []
        for r in rows:
            doc = r['doc_name']
            ref = {**docs[doc], 'dataset':name}
            if name=='FinanceBench':
                resolved_path=raw/'financebench/filings.json'
                resolved=json.loads(resolved_path.read_text(encoding='utf-8')) if resolved_path.exists() else {}
                ref.update(resolved.get(doc,{}))
            if name == 'XBRLFiling':
                # Whitelist public filing identifiers; no equation/operands/values.
                provenance = r['ground_truth']['provenance']
                for key in ['cik','accession','fiscal_year','period_end','report_date','ticker']:
                    if key in provenance: ref[key] = provenance[key]
                ref['cik'] = r['cik']
            refs[doc] = ref
            normalized.append({'id':r['financebench_id'], 'dataset':name, 'question':r['question'],
                'doc_name':doc, 'context': '\n\n'.join(e.get('evidence_text_full_page') or e['evidence_text'] for e in r['evidence']),
                'gold': {'answer':r['answer'], 'unit': 'USD millions' if name == 'XBRLFiling' else None},
                'context_kind':'provided_redacted_document' if name == 'XBRLFiling' else 'evaluation_only_oracle_excerpt'})
        write_jsonl(out/(name+'.jsonl'), normalized)
        datasets[name] = {'n':len(normalized),'paper_n':DATASETS[name], 'source_sha256':digest(source),
                          'processed_sha256':digest(out/(name+'.jsonl')),'selection':'exact_public_subset',
                          'ids':[r['id'] for r in normalized]}
    if 'TAT-DQA' not in selected:return finish()
    tat_file = fetch('https://huggingface.co/datasets/next-tat/TAT-DQA/resolve/'+TAT_REVISION+'/tatdqa_dataset_test_gold.json', raw/'tatdqa/tatdqa_dataset_test_gold.json')
    archive = fetch('https://huggingface.co/datasets/next-tat/TAT-DQA/resolve/'+TAT_REVISION+'/tatdqa_docs_test.zip', raw/'tatdqa/tatdqa_docs_test.zip')
    tat = json.loads(tat_file.read_text(encoding='utf-8'))
    mapping_path = raw/'tatdqa/filings.json'
    mapping = json.loads(mapping_path.read_text(encoding='utf-8')) if mapping_path.exists() else {}
    candidates, exclusions, ready_rows, pdf_warnings = [], [], [], []
    with zipfile.ZipFile(archive) as z:
        for d in tat:
            uid, source = d['doc']['uid'], d['doc']['source']
            context_path = raw/'tatdqa/docs'/(uid+'.pdf')
            context_path.parent.mkdir(parents=True,exist_ok=True)
            if not context_path.exists(): context_path.write_bytes(z.read('test/'+uid+'.pdf'))
            import fitz
            fitz.TOOLS.mupdf_warnings(reset=True)
            with fitz.open(context_path) as pdf: text = '\n\n'.join(p.get_text(sort=True) for p in pdf)
            warnings = fitz.TOOLS.mupdf_warnings(reset=True)
            context_kind='full_provided_pdf_document'
            if warnings:
                # Recover all OCR blocks from this official document, never gold-mapped spans.
                ocr=json.loads(z.read('test/'+uid+'.json'))
                recovered='\n\n'.join('\n'.join(b.get('text','') for b in sorted(page.get('blocks',[]),key=lambda b:b.get('order',0))) for page in ocr.get('pages',[]))
                if recovered.strip():text=recovered;context_kind='full_official_document_OCR_due_to_PDF_warning'
                pdf_warnings.append({'document':uid,'source':source,'warnings':warnings,'text_empty':not bool(text.strip()),'context_kind':context_kind})
            for q in d['questions']:
                if not text.strip():
                    exclusions.append({'id':q['uid'],'reason':'provided_PDF_has_no_extractable_document_text','source':source})
                    continue
                value = scalar(q['answer'])
                if value is None:
                    exclusions.append({'id':q['uid'],'reason':'non_scalar_numerical_target','source':source})
                    continue
                doc = 'TATDQA_'+Path(source).stem
                row = {'id':q['uid'],'dataset':'TAT-DQA','question':q['question'],'doc_name':doc,
                    'context':text, 'context_kind':context_kind,'source_document':source,
                    'gold':{'answer':value,'scale':q.get('scale',''),'unit':None}}
                candidates.append(row)
                if source in mapping:
                    filed=root/'data/filings'/(doc+'.json')
                    if filed.exists() and not json.loads(filed.read_text(encoding='utf-8')).get('facts'):
                        exclusions.append({'id':q['uid'],'reason':'matched_filing_has_no_numeric_XBRL_facts','source':source})
                        continue
                    refs[doc] = {**mapping[source], 'doc_name':doc, 'dataset':'TAT-DQA'}
                    ready_rows.append(row)
    write_jsonl(raw/'tatdqa/numeric_candidates.jsonl', candidates)
    if mapping:
        write_jsonl(out/'TAT-DQA.jsonl', ready_rows)
    datasets['TAT-DQA'] = {'n':len(ready_rows),'paper_n':403, 'source_sha256':digest(tat_file),
        'processed_sha256':digest(out/'TAT-DQA.jsonl') if mapping else None,
            'selection':'reconstructed_test_scalar_numeric_and_unambiguous_SEC_filing',
        'exact_403_indices_published':False,'numeric_candidates':len(candidates),
        'unmapped_candidates':len(candidates)-len(ready_rows),'ready':bool(mapping and ready_rows),
        'ids':[r['id'] for r in ready_rows]}
    write_json(raw/'tatdqa/exclusions.json', exclusions)
    write_json(root/'research/tat_pdf_warnings.json', pdf_warnings)
    return finish()

def parse_filing(ref, instance, calculation=None, label=None):
    # Reuse the source XML/taxonomy parsers. Keep individual facts and IDs instead
    # of silently overwriting duplicates at concept/context keys.
    from verifiqa.verification.xbrl_linkbase import _namespace_map, _parse_contexts, _parse_units, _split_tag, _qname, _parse_calculation_linkbase, _parse_label_linkbase
    from dataclasses import asdict
    tree = ET.parse(instance).getroot()
    ns = _namespace_map(instance)
    contexts, units = _parse_contexts(tree), _parse_units(tree)
    # Preserve simple divided measures, especially USD per share.
    for el in tree.findall('{http://www.xbrl.org/2003/instance}unit'):
        if el.find('{http://www.xbrl.org/2003/instance}divide') is not None:
            if len(units.get(el.get('id'),()))==2:
                a,b=units[el.get('id')];units[el.get('id')]=(a+'/'+b,)
    facts = []
    for i, el in enumerate(tree.iter()):
        cid, uid = el.get('contextRef'), el.get('unitRef')
        if not cid or not uid or cid not in contexts: continue
        try: value = Decimal((el.text or '').strip())
        except InvalidOperation: continue
        if not value.is_finite(): continue
        measures = units.get(uid,())
        if len(measures) != 1: continue
        namespace, local = _split_tag(el.tag)
        c = asdict(contexts[cid])
        facts.append({'id':el.get('id') or 'xml_element_'+str(i),'concept':_qname(ns,namespace,local),
            'period':{k:v for k,v in c.items() if k != 'context_id'}, 'unit':measures[0],
            'value':str(value),'decimals':el.get('decimals')})
    groups = []
    if calculation:
        parsed, _ = _parse_calculation_linkbase(calculation)
        for g in parsed:
            groups.append({'parent':g.parent_concept,'role':g.role,
                           'children':[{'concept':c.concept,'weight':str(c.weight)} for c in g.children]})
    labels = _parse_label_linkbase(label) if label else {}
    return {**ref,'schema_version':1,'source_url':ref.get('source_url') or ref.get('doc_link'),'facts':facts,
        'instance_sha256':digest(instance),'calculation_sha256':digest(calculation) if calculation else None,
        'calculations':groups,'labels':labels}

def accession_url(ref):
    cik, acc = str(ref.get('cik','')), str(ref.get('accession',''))
    link = ref.get('doc_link') or ref.get('source_url','')
    m = re.search(r'/data/(\d+)/(\d{18})/', link)
    if m: cik, acc = m.groups()
    if not cik or not acc: return None
    return 'https://www.sec.gov/Archives/edgar/data/'+str(int(cik))+'/'+acc.replace('-','')

def recover_xbrl_bundle(base,directory,index):
    names=[x['name'] for x in index['directory']['item'] if x['name'].endswith('-xbrl.zip')]
    if len(names)!=1:raise ValueError('no_unique_official_XBRL_bundle')
    archive=fetch(base+'/'+names[0],directory/names[0],sec=True)
    recovered=[]
    with zipfile.ZipFile(archive) as z:
        for item in index['directory']['item']:
            name=item['name']
            if not name.endswith('.xml') or (directory/name).exists():continue
            members=[n for n in z.namelist() if Path(n).name==name]
            if len(members)==1:
                (directory/name).write_bytes(z.read(members[0]));recovered.append(name)
    write_json(directory/'bundle_recovery.json',{'source_url':base+'/'+names[0],
        'sha256':digest(archive),'recovered_files':recovered})
    return recovered

def _acquire_one_filing(root,doc,ref):
    audit=[]
    output = root/'data/filings'/(doc+'.json')
    if output.exists() and json.loads(output.read_text(encoding='utf-8')).get('schema_version')==1: return {'doc_name':doc,'status':'cached'}
    try:
        if ref.get('xbrl_unavailable_reason'):
            write_json(output,{**ref,'schema_version':1,'status':'source_has_no_XBRL',
                'source_url':ref['doc_link'],'facts':[],'calculations':[],'labels':{},
                'source_sha256':ref.get('source_document_sha256'), 'instance_sha256':None})
            audit.append({'doc_name':doc,'status':'documented_unavailable','reason':ref['xbrl_unavailable_reason']})
            return audit[-1]
        base = accession_url(ref)
        if not base: raise ValueError('missing_SEC_filing_identity')
        directory = root/'data/raw/filings'/doc
        index = json.loads(fetch(base+'/index.json',directory/'index.json',sec=True).read_text())
        names = [x['name'] for x in index['directory']['item']]
        instances = [n for n in names if n.endswith('_htm.xml') or n.endswith('_html.xml')]
        if not instances:
            instances = [n for n in names if n.endswith('.xml') and not re.search(r'_(?:cal|def|lab|pre|schema)\.xml$|FilingSummary|MetaLinks',n,re.I)]
        if not instances:
            write_json(output,{**ref,'schema_version':1,'status':'source_has_no_XBRL',
                'source_url':base+'/index.json','source_index_sha256':digest(directory/'index.json'),
                'facts':[],'calculations':[],'labels':{},'instance_sha256':None,
                'xbrl_unavailable_reason':'SEC_filing_directory_contains_no_XBRL_instance'})
            return {'doc_name':doc,'status':'documented_unavailable'}
        if len(instances) != 1: raise ValueError('ambiguous_XBRL_instance')
        instance = fetch(base+'/'+instances[0],directory/instances[0],sec=True)
        calc_names, label_names = [n for n in names if n.endswith('_cal.xml')], [n for n in names if n.endswith('_lab.xml')]
        optional_gaps=[]
        try:
            calc = fetch(base+'/'+calc_names[0],directory/calc_names[0],sec=True) if len(calc_names)==1 else None
            label = fetch(base+'/'+label_names[0],directory/label_names[0],sec=True) if len(label_names)==1 else None
        except httpx.HTTPError as failed:
            try:recover_xbrl_bundle(base,directory,index)
            except (httpx.HTTPError,ValueError,zipfile.BadZipFile):pass
            calc=directory/calc_names[0] if len(calc_names)==1 and (directory/calc_names[0]).exists() else None
            label=directory/label_names[0] if len(label_names)==1 and (directory/label_names[0]).exists() else None
            if len(calc_names)==1 and calc is None:optional_gaps.append({'source_url':base+'/'+calc_names[0],'kind':'calculation_linkbase','reason':str(failed)[:150]})
            if len(label_names)==1 and label is None:optional_gaps.append({'source_url':base+'/'+label_names[0],'kind':'label_linkbase','reason':'not_recovered_after_linkbase_download_failure'})
        enriched = dict(ref)
        enriched['source_url']=base+'/'+instances[0]
        if optional_gaps:enriched['missing_optional_sources']=optional_gaps
        enriched.setdefault('accession',base.rsplit('/',1)[-1])
        # DocumentPeriodEndDate and fiscal-year label are source metadata.
        tree = ET.parse(instance).getroot()
        tags = {e.tag.split('}')[-1]:(e.text or '').strip() for e in tree.iter() if e.tag.split('}')[-1] in {'DocumentPeriodEndDate','DocumentFiscalYearFocus'}}
        enriched.setdefault('period_end', tags.get('DocumentPeriodEndDate'))
        enriched.setdefault('fiscal_year', tags.get('DocumentFiscalYearFocus'))
        write_json(output, parse_filing(enriched,instance,calc,label))
        audit.append({'doc_name':doc,'status':'downloaded','sha256':digest(output)})
    except (ValueError,httpx.HTTPError,ET.ParseError) as exc:
        audit.append({'doc_name':doc,'status':'pending','reason':str(exc)[:150]})
    return audit[-1]

def acquire_filings(root,datasets=None):
    from concurrent.futures import ThreadPoolExecutor,as_completed
    root=Path(root)
    refs=json.loads((root/'data/main/documents.json').read_text(encoding='utf-8'))
    selected=[(doc,ref) for doc,ref in refs.items() if not datasets or ref['dataset'] in datasets]
    audit=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        tasks=[pool.submit(_acquire_one_filing,root,doc,ref) for doc,ref in selected]
        for task in as_completed(tasks):
            row=task.result();audit.append(row)
            write_json(root/'research/filing_acquisition.json',audit)
            print(row['doc_name'],row['status'],flush=True)
    return audit

def acquire_documents(root):
    root = Path(root)
    refs = json.loads((root/'data/main/documents.json').read_text(encoding='utf-8'))
    rows = []
    for doc, ref in refs.items():
        if ref['dataset'] != 'FinanceBench': continue
        path = root/'data/raw/documents'/(doc+'.pdf')
        corpus=root/'data/corpus'/(doc+'.json')
        if corpus.exists():
            old=json.loads(corpus.read_text(encoding='utf-8'))
            if old.get('source_format')=='same_SEC_filing_HTML_fallback' or (path.exists() and b'%PDF-' in path.read_bytes()[:1024]):
                rows.append({'doc_name':doc,'status':'ready','cached':True});continue
            corpus.replace(corpus.with_suffix('.invalid-response.json'))
        try:
            url = ref['doc_link']
            targets=parse_qs(urlparse(url).query).get('pdfTarget')
            if targets:
                decoded=base64.b64decode(targets[0]).decode('utf-8')
                if urlparse(decoded).hostname==urlparse(url).hostname and decoded.endswith('.pdf'):
                    url=decoded
                    if path.exists() and not path.read_bytes().startswith(b'%PDF'):
                        path.rename(path.with_suffix('.viewer.html'))
            fetch(url,path,sec='sec.gov' in urlparse(url).netloc)
            if b'%PDF-' not in path.read_bytes()[:1024]:raise ValueError('publisher_returned_HTML_instead_of_PDF')
            import fitz
            with fitz.open(path) as pdf:
                pages = [{'page':i, 'text':p.get_text(sort=True)} for i,p in enumerate(pdf)]
            if not any(p['text'].strip() for p in pages): raise ValueError('document_has_no_extractable_text')
            write_json(root/'data/corpus'/(doc+'.json'),{'doc_name':doc,'source_url':url,'source_sha256':digest(path),'pages':pages})
            rows.append({'doc_name':doc,'status':'ready'})
        except (ValueError,httpx.HTTPError,RuntimeError) as exc:
            try:
                # Reacquire the same filing from SEC when an issuer PDF moved.
                # No benchmark evidence is substituted for a missing document.
                alternative=ref.get('xbrl_doc_link')
                if not alternative:raise ValueError('no_verified_SEC_document_fallback')
                html=fetch(alternative,path.with_suffix('.html'),sec=True)
                from verifiqa.corpus_builder import _extract_html_text_pages
                texts=_extract_html_text_pages(html)
                if not texts:raise ValueError('empty_SEC_document_fallback')
                write_json(corpus,{'doc_name':doc,'source_url':alternative,'original_source_url':ref['doc_link'],
                    'source_sha256':digest(html),'source_format':'same_SEC_filing_HTML_fallback',
                    'pages':[{'page':i,'text':t} for i,t in enumerate(texts)]})
                rows.append({'doc_name':doc,'status':'ready','adaptation':'same_SEC_filing_HTML_fallback'})
            except (ValueError,httpx.HTTPError,RuntimeError) as fallback:
                rows.append({'doc_name':doc,'status':'pending','reason':str(exc)[:150],'fallback':str(fallback)[:150]})
        write_json(root/'research/document_acquisition.json',rows)
        print(doc,rows[-1]['status'],flush=True)
    write_json(root/'research/document_acquisition.json',rows)
    return rows

def normalized_company(text):
    words = re.findall(r'[a-z0-9]+', text.lower().replace('&',' '))
    stop = {'inc','corp','corporation','company','co','ltd','limited','plc','the','holdings','group','ag','se','nv','sa'}
    return tuple(sorted(w for w in words if w not in stop))

def discover_tat(root):
    """Exact normalized issuer-name match only; freeze all unresolved sources."""
    root = Path(root)
    raw = root/'data/raw/tatdqa'
    tickers = json.loads(fetch('https://www.sec.gov/files/company_tickers.json',raw/'company_tickers.json',sec=True).read_text())
    by_name = {}
    for company in tickers.values():
        by_name.setdefault(normalized_company(company['title']),set()).add(str(company['cik_str']))
    docs = json.loads((raw/'tatdqa_dataset_test_gold.json').read_text(encoding='utf-8'))
    mapping, unresolved = {}, []
    for source in sorted({d['doc']['source'] for d in docs}):
        stem, year = Path(source).stem.rsplit('_',1)
        ciks = by_name.get(normalized_company(stem), set())
        if len(ciks) != 1:
            unresolved.append({'source':source,'reason':'issuer_name_not_unambiguous_in_SEC_registry'}); continue
        cik = next(iter(ciks))
        try:
            s = json.loads(fetch('https://data.sec.gov/submissions/CIK'+cik.zfill(10)+'.json',raw/'submissions'/(cik+'.json'),sec=True).read_text())
            blocks = [s['filings']['recent']]
            for f in s['filings'].get('files',[]):
                # Fetch only historical blocks that could contain the source year.
                if int(f['filingFrom'][:4]) <= int(year)+1 and int(f['filingTo'][:4]) >= int(year):
                    blocks.append(json.loads(fetch('https://data.sec.gov/submissions/'+f['name'],raw/'submissions'/f['name'],sec=True).read_text()))
            matches = {}
            for b in blocks:
                for i, form in enumerate(b['form']):
                    report = b.get('reportDate',['']*len(b['form']))[i]
                    if form not in {'10-K','20-F','40-F'} or not report.startswith(year): continue
                    acc = b['accessionNumber'][i]
                    matches[acc] = {'cik':cik,'accession':acc,'period_end':report,'fiscal_year':year,
                        'doc_link':'https://www.sec.gov/Archives/edgar/data/'+str(int(cik))+'/'+acc.replace('-','')+'/'+b['primaryDocument'][i],
                        'matching_rule':'exact_normalized_issuer_name_and_annual_filing_report_year','form':form}
            if len(matches) == 1: mapping[source] = next(iter(matches.values()))
            else: unresolved.append({'source':source,'reason':'missing_or_ambiguous_annual_filing'})
        except httpx.HTTPError:
            unresolved.append({'source':source,'reason':'SEC_request_failed'})
    write_json(raw/'filings.json',mapping)
    write_json(root/'research/tat_filing_mapping.json',{'matches':mapping,'unresolved':unresolved,'predictions_used':False})
    return mapping

def discover_financebench(root):
    """Resolve public document identities before any model inference."""
    root=Path(root)
    raw=root/'data/raw/financebench'
    ticker_file=fetch('https://www.sec.gov/files/company_tickers.json',root/'data/raw/tatdqa/company_tickers.json',sec=True)
    companies=list(json.loads(ticker_file.read_text()).values())
    docs=read_jsonl(root/'upstream/datasets/financebench-67/documents.jsonl')
    known={'Activision Blizzard':{'cik':'718877','accession':'0000718877-20-000003','period_end':'2019-12-31','fiscal_year':2019,
        'xbrl_doc_link':'https://www.sec.gov/Archives/edgar/data/718877/000071887720000003/atvi-12312019x10xk.htm',
        'identity_source':'https://www.sec.gov/Archives/edgar/data/718877/0000718877-20-000003-index.html'}}
    mapped,audit={},[]
    for d in docs:
        doc=d['doc_name'];url=d['doc_link']
        if doc=='PEPSICO_2023Q1_EARNINGS':
            mapped[doc]={**d,'cik':'77476','accession':'0000077476-23-000025',
                'period_end':'2023-03-25','fiscal_year':2023,
                'xbrl_doc_link':'https://www.sec.gov/Archives/edgar/data/77476/000007747623000025/q120238-kxexhibit991.htm',
                'identity_source':'https://www.sec.gov/Archives/edgar/data/77476/000007747623000025/q120238-kxexhibit991.htm'}
            continue
        if '_EARNINGS' in doc:
            pdf=root/'data/raw/documents'/(doc+'.pdf')
            if pdf.exists() and pdf.read_bytes().lstrip().startswith(b'%PDF'):
                mapped[doc]={**d,'xbrl_unavailable_reason':'standalone_issuer_earnings_PDF_without_XBRL_instance_in_released_source',
                             'source_document_sha256':digest(pdf),'identity_source':url}
                continue
        if d['company'] in known and d.get('doc_period')==2019:
            mapped[doc]={**d,**known[d['company']]};continue
        direct=re.search(r'CIK[-/](\d+)',url,re.I)
        cik=direct[1] if direct else None
        if not cik:
            want=set(normalized_company(d['company']))
            candidates=[x for x in companies if set(normalized_company(x['title']))==want or x['ticker'].lower()==d['company'].lower()]
            if not candidates:
                candidates=[x for x in companies if want and want<=set(normalized_company(x['title']))]
                if candidates:
                    best=min(len(normalized_company(x['title'])) for x in candidates)
                    candidates=[x for x in candidates if len(normalized_company(x['title']))==best]
            ids={str(x['cik_str']) for x in candidates}
            if len(ids)==1:cik=next(iter(ids))
        if not cik:
            audit.append({'doc_name':doc,'reason':'issuer_not_unambiguous'});continue
        year=int(re.search(r'(20\d{2})',doc)[1])
        acc=re.search(r'\d{10}-\d{2}-\d{6}',url)
        target_end=None
        corpus=root/'data/corpus'/(doc+'.json')
        if corpus.exists():
            pages=json.loads(corpus.read_text(encoding='utf-8'))['pages']
            cover=' '.join(p['text'] for p in pages[:3])
            m=re.search(r'for the (?:fiscal year|quarterly period|quarter) ended\s+([A-Za-z]+\s+\d{1,2},?\s+20\d{2})',cover,re.I)
            if m:
                try:target_end=datetime.strptime(m[1].replace(',',''),'%B %d %Y').date().isoformat()
                except ValueError:pass
        try:
            s=json.loads(fetch('https://data.sec.gov/submissions/CIK'+cik.zfill(10)+'.json',raw/'submissions'/(cik+'.json'),sec=True).read_text())
            blocks=[s['filings']['recent']]
            for f in s['filings'].get('files',[]):
                if int(f['filingFrom'][:4])<=year+1 and int(f['filingTo'][:4])>=year:
                    blocks.append(json.loads(fetch('https://data.sec.gov/submissions/'+f['name'],raw/'submissions'/f['name'],sec=True).read_text()))
            matches={}
            quarter=re.search(r'20\d{2}Q([1-4])',doc)
            dated=re.search(r'dated-(\d{4}-\d{2}-\d{2})',doc)
            for block in blocks:
                for i,form in enumerate(block['form']):
                    a=block['accessionNumber'][i];end=block.get('reportDate',['']*len(block['form']))[i]
                    if acc:
                        if a!=acc[0]:continue
                    elif dated:
                        if form!='8-K' or block['filingDate'][i]!=dated[1]:continue
                    elif '_10K' in doc:
                        if form!='10-K' or not end.startswith(str(year)):continue
                    elif '_10Q' in doc:
                        if form!='10-Q' or not quarter:continue
                        if target_end:
                            if end!=target_end:continue
                        elif not end.startswith(str(year)) or (int(end[5:7])-1)//3+1!=int(quarter[1]):continue
                    else:continue
                    matches[a]={'cik':cik,'accession':a,'period_end':end,'fiscal_year':year,
                        'xbrl_doc_link':'https://www.sec.gov/Archives/edgar/data/'+str(int(cik))+'/'+a.replace('-','')+'/'+block['primaryDocument'][i],
                        'identity_source':'SEC_submissions','form':form}
            if len(matches)==1:mapped[doc]={**d,**next(iter(matches.values()))}
            else:audit.append({'doc_name':doc,'reason':'missing_or_ambiguous_source_filing','candidates':list(matches)})
        except httpx.HTTPError as exc:audit.append({'doc_name':doc,'reason':str(exc)[:120]})
        write_json(raw/'filings.json',mapped)
        write_json(root/'research/financebench_filing_mapping.json',{'matches':mapped,'pending':audit})
        print(doc,'matched' if doc in mapped else 'pending',flush=True)
    write_json(raw/'filings.json',mapped)
    write_json(root/'research/financebench_filing_mapping.json',{'matches':mapped,'pending':audit})
    return mapped
