"""Render source HTML table cells as rows without changing any source values."""
import re
from bs4 import BeautifulSoup,NavigableString
from .common import digest

TITLE=re.compile(r'^(?:consolidated\s+)?(?:statements? of (?:operations|income|cash flows|financial position)|balance sheets?)\s*$',re.I)


def html_table_pages(content):
    soup=BeautifulSoup(content,'lxml');pages=[]
    for index,table in enumerate(soup.find_all('table')):
        rows=[];numeric_rows=0
        for tr in table.find_all('tr'):
            if tr.find_parent('table') is not table or tr.find('table'):continue
            cells=tr.find_all(['td','th'],recursive=False)
            parts=[re.sub(r'\s+',' ',c.get_text(' ',strip=True)).strip() for c in cells]
            parts=[x for x in parts if x]
            if not parts:continue
            row='  '.join(parts)
            if len(row)>1500:continue
            rows.append(row)
            if any(re.search('[A-Za-z]',p) for p in parts) and any(re.fullmatch(r'[$(\s+\-\d,.%)]*\d[\d,.%\s)]*',p) for p in parts):numeric_rows+=1
        if numeric_rows<2:continue
        preceding=[];size=0
        for element in table.previous_elements:
            if not isinstance(element,NavigableString):continue
            text=re.sub(r'\s+',' ',str(element)).strip()
            if not text:continue
            size+=len(text)
            if size>1200:break
            if TITLE.fullmatch(text):preceding.append(text);break
        text='\n'.join([*reversed(preceding),*rows])
        pages.append({'page':1000000+index,'text':text})
    return pages


def augment_pages(root,doc,corpus):
    pages=corpus['pages']
    if corpus.get('source_format')!='same_SEC_filing_HTML_fallback':return pages
    raw=root/'data/raw/documents'/(doc+'.html')
    if digest(raw)!=corpus['source_sha256']:raise ValueError('HTML_table_source_changed')
    return [*pages,*html_table_pages(raw.read_bytes())]
