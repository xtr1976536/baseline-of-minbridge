"""Recover issuer row labels from the same accession's tagged primary filing.

Only text-to-qname presentation links are added. Values still come exclusively
from the previously frozen XBRL instance; no benchmark annotations are read.
"""
from __future__ import annotations
from pathlib import Path
import json
import os
import re
import warnings
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup,XMLParsedAsHTMLWarning
from .common import digest,write_json


def tagged_row_labels(content):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',XMLParsedAsHTMLWarning)
        soup=BeautifulSoup(content,'lxml')
    labels={}
    for tag in soup.find_all(lambda t:t.name and t.name.lower().split(':')[-1]=='nonfraction'):
        qname=tag.get('name','')
        if ':' not in qname:continue
        row=tag.find_parent('tr');cell=tag.find_parent(['td','th'])
        if row is None or cell is None:continue
        cells=row.find_all(['td','th'],recursive=False)
        try:index=next(i for i,c in enumerate(cells) if c is cell or cell in c.descendants)
        except StopIteration:continue
        parts=[c.get_text(' ',strip=True) for c in cells[:index]]
        label=' '.join(x for x in parts if re.search('[A-Za-z]',x))
        label=re.sub(r'\s+',' ',label).strip()
        label=re.sub(r'\s*\([a-z0-9]{1,3}\)\s*$','',label).strip()
        if not 2<=len(label)<=240 or not re.search('[A-Za-z]{2}',label):continue
        if label not in labels.setdefault(qname,[]):labels[qname].append(label)
    return labels


def acquire(root,docs):
    contact=os.environ.get('SEC_USER_AGENT')
    if not contact:raise ValueError('SEC_USER_AGENT required for primary filing downloads')
    results=[]
    with httpx.Client(headers={'User-Agent':contact},follow_redirects=True,timeout=45) as http:
        for doc in docs:
            output=root/'data/source_rows'/(doc+'.json')
            filing=json.loads((root/'data/filings'/(doc+'.json')).read_text(encoding='utf-8'))
            if output.exists():
                results.append(json.loads(output.read_text(encoding='utf-8')));continue
            if not filing.get('instance_sha256'):
                results.append({'doc_name':doc,'status':'no_XBRL_instance'});continue
            directory=root/'data/raw/filings'/doc
            index=json.loads((directory/'index.json').read_text(encoding='utf-8'))
            stem=Path(urlparse(filing['source_url']).path).name.replace('_htm.xml','.htm').replace('_xml.xml','.htm')
            names=[x['name'] for x in index['directory']['item']]
            candidates=[stem] if stem in names and stem.endswith(('.htm','.html')) else [n for n in names if n.endswith(('.htm','.html')) and not re.search(r'exhibit|ex\d|index',n,re.I)]
            if len(candidates)!=1:
                results.append({'doc_name':doc,'status':'primary_document_ambiguous'});continue
            url=filing['source_url'].rsplit('/',1)[0]+'/'+candidates[0]
            raw=root/'data/raw/filing-html'/(doc+'.html');raw.parent.mkdir(parents=True,exist_ok=True)
            try:
                if not raw.exists():
                    response=http.get(url);response.raise_for_status();raw.write_bytes(response.content)
                labels=tagged_row_labels(raw.read_bytes())
                if not labels:raise ValueError('primary_document_has_no_tagged_table_rows')
                result={'doc_name':doc,'status':'ready','source_url':url,'raw_path':raw.relative_to(root).as_posix(),
                    'raw_sha256':digest(raw),'instance_sha256':filing['instance_sha256'],'labels':labels}
                write_json(output,result);results.append(result)
                print('SOURCE_LABELS',doc,len(labels),flush=True)
            except (httpx.HTTPError,ValueError) as exc:
                results.append({'doc_name':doc,'status':'unavailable','error_type':type(exc).__name__})
    return results
