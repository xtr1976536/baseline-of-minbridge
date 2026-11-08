"""Recover auditable source spans without requiring byte-identical typography.

Only explicitly printed numbers are accepted. Tables are anchored by their
actual row/column headers; financial formulas are never evaluated here.
"""
from __future__ import annotations
import html
import math
import re
import unicodedata
from decimal import Decimal
from .types import EvidenceError,ProtocolError

def text(s):return html.unescape(unicodedata.normalize('NFKC',str(s))).replace('’',"'").replace('−','-')
def key(s):return re.sub(r'[^a-z0-9\u3400-\u9fff]+','',text(s).casefold())
def tokens(s):
    source=text(s)
    masked=re.sub(r'<[^>]+>',lambda m:' '*len(m[0]),source)
    result=[]
    for m in re.finditer(r'\(\s*[$£€]?\s*\d[\d,]*(?:\.\d+)?\s*\)|[A-Za-z\u3400-\u9fff]+|[+-]?(?:\d[\d,]*(?:\.\d+)?|\.\d+)',masked):
        if m[0][0].isalpha() or '\u3400'<=m[0][0]<='\u9fff':
            result.extend((char.casefold(),m.start()+i,m.start()+i+1) for i,char in enumerate(m[0]))
        else:
            raw=re.sub(r'[$£€,\s()]','',m[0])
            if m[0].startswith('('):raw='-'+raw
            result.append(('#'+str(Decimal(raw).normalize()),m.start(),m.end()))
    return result

def copied_span(quote,context):
    if not isinstance(quote,str) or not quote.strip():return None
    source=text(context);qs=tokens(quote);cs=tokens(source)
    wanted=[m[0] for m in qs];actual=[m[0] for m in cs]
    if not wanted:return None
    needle='\x00'+'\x00'.join(wanted)+'\x00';haystack='\x00'+'\x00'.join(actual)+'\x00'
    at=haystack.find(needle)
    if at>=0:
        i=haystack[:at].count('\x00')
        return source[cs[i][1]:cs[i+len(wanted)-1][2]]
    return None

def projected_table_span(quote,context):
    """Recover a table quote which omitted intervening cells, without new tokens.

    OES may print ``Revenue | 2022 | 40`` for a row and a separate period
    header. We retain the actual source block; support() must still validate
    the requested value's row/column. This is never a source for a new number.
    """
    wanted=[t[0] for t in tokens(quote)]
    if not wanted:return None
    blocks=re.findall(r'(?:^[^\n]*\|[^\n]*\n?)+',text(context),re.M)
    for block in blocks:
        ts=tokens(block)
        for start,tok in enumerate(ts):
            if tok[0]!=wanted[0]:continue
            j=0
            for end in range(start,len(ts)):
                if ts[end][0]==wanted[j]:
                    j+=1
                    if j==len(wanted):return block[ts[start][1]:ts[end][2]]
    return None

def printed(value,s):
    s=re.sub(r'([+-])\s*([$£€¥￥])\s*(?=\d)',r'\2\1',text(s))
    for m in re.finditer(r'(?<![\d.])[+-]?(?:\d[\d,]*(?:\.\d+)?|\.\d+)(?![\d.])',text(s)):
        n=float(m[0].replace(',',''))
        before=text(s)[:m.start()].rstrip();after=text(s)[m.end():].lstrip()
        if before.endswith('(') and after.startswith(')'):n=-abs(n)
        if math.isclose(float(value),n,rel_tol=1e-12,abs_tol=1e-12):return True
    return False

def interval_numbers(s):
    quantity=r'[$£€¥￥]?\s*\(?[+-]?[\d,]+(?:\.\d+)?\)?\s*(?:%|x|million|thousand|billion)?'
    m=re.fullmatch(r'\s*('+quantity+r')\s*(?:–|—|-|to)\s*('+quantity+r')\s*',text(s),re.I)
    if not m:return None
    values=[]
    for part in m.groups():
        number=re.search(r'[+-]?[\d,]+(?:\.\d+)?',part)
        value=float(number[0].replace(',',''))
        if '(' in part and ')' in part:value=-abs(value)
        values.append(value)
    return values

def bound_role(metric):
    name=text(metric).casefold()
    if re.search(r'\b(?:lower|minimum|min|lowest)\b',name):return 0
    if re.search(r'\b(?:upper|maximum|max|highest)\b',name):return 1
    return None

def contains_label(s,label):
    a,b=key(s),key(label)
    if not b:return False
    pos=a.find(b)
    if pos<0:return False
    if pos and (a[:pos].endswith('non') or a[:pos].endswith('非')) and not b.startswith(('non','非')):return False
    return True

def semantic_conflict(metric,label):
    a,b=key(metric),key(label)
    for left,right in [('gross','net'),('adjusted','unadjusted')]:
        if left in a and right in b and right not in a:return True
        if left in b and right in a and right not in b:return True
    if ('noncurrent' in a)!=('noncurrent' in b) and 'current' in a and 'current' in b:return True
    if ('非流动' in a)!=('非流动' in b) and '流动' in a and '流动' in b:return True
    profit=lambda x:any(w in x for w in ('profit','netincome','grossincome','利润'))
    revenue=lambda x:any(w in x for w in ('revenue','sales','收入'))
    if profit(a) and revenue(b) and not profit(b):return True
    if profit(b) and revenue(a) and not profit(a):return True
    return False

def verified_quotes(binding,context):
    extra=binding.get('context_spans') or []
    if not isinstance(extra,list) or any(not isinstance(s,str) or not s.strip() for s in extra):
        raise ProtocolError('Invalid evidence span list')
    spans=[]
    for quote in extra:
        found=copied_span(quote,context) or projected_table_span(quote,context)
        if found is None:raise EvidenceError('OES supplied a non-verbatim evidence span')
        spans.append(found)
    snippet=binding.get('context')
    if not isinstance(snippet,str) or not snippet.strip():raise ProtocolError('OES omitted the evidence snippet')
    found=copied_span(snippet,context)
    if found:spans.append(found)
    else:
        for part in re.split(r'\n|(?<=[.!?。！？])\s+',snippet):
            found=copied_span(part,context)
            if found:spans.append(found)
    return list(dict.fromkeys(spans))

def years(value):return set(re.findall(r'(?<!\d)(?:19|20)\d{2}(?!\d)',str(value or '')))

def table_support(context,labels,value,constraints):
    groups=[];group=[]
    for line in [*context.splitlines(),'']:
        if line.count('|')>=2:group.append(line)
        elif group:groups.append(group);group=[]
    matches=[];wanted=years(constraints.temporal_scope)
    scope=key(constraints.entity_scope or '')
    time_labels={'year','fiscalyear','date','period','年份','年度','日期','时间','报告期'}
    entity_labels={'company','entity','name','plancategory','category','rating','creditrating','公司','公司名称','企业','主体','姓名','类别','评级'}
    for table in groups:
        rows=[[html.unescape(re.sub(r'<[^>]+>','',c)).strip() for c in line.strip().strip('|').split('|')] for line in table]
        for ri,row in enumerate(rows):
            if all(not c or re.fullmatch(r':?-+:?',c) for c in row):continue
            def is_header(r):
                for cell in r:
                    # Dates such as December 31 and names such as S&P 500
                    # are text headers, not numeric observations.
                    if re.fullmatch(r'[$£€¥￥]?\s*\(?[+-]?[\d,]+(?:\.\d+)?\)?\s*%?',cell):
                        if not re.fullmatch(r'(?:19|20)\d{2}',cell):return False
                return True
            preceding=[(i,r) for i,r in enumerate(rows[:ri]) if len(r)==len(row) and is_header(r)]
            row_metric=any(contains_label(c,label) for c in row for label in labels if label)
            timecols={i for _,r in preceding for i,c in enumerate(r) if key(c) in time_labels}
            entitycols={i for _,r in preceding for i,c in enumerate(r) if key(c) in entity_labels}
            if wanted and timecols and any(years(row[i]) and not wanted&years(row[i]) for i in timecols):continue
            def entity_match(cell):
                k=key(cell)
                return k==scope or len(k)>3 and k in scope
            explicit_entities=[i for i in entitycols if any(entity_match(r[i]) for r in rows if len(r)==len(row))]
            if any(not entity_match(row[i]) for i in explicit_entities):continue
            row_years=years(row[0]) if row else set()
            if row_years and wanted and not row_years&wanted:continue
            for col,cell in enumerate(row):
                interval=interval_numbers(cell)
                if interval:
                    role=bound_role(labels[0])
                    if role is None or not math.isclose(float(value),interval[role],rel_tol=1e-12,abs_tol=1e-12):continue
                elif not printed(value,cell):continue
                scalar=re.sub(r'\([a-z]\)|[*†‡]','',cell,flags=re.I).strip()
                if not interval and not re.fullmatch(r'[$£€¥￥]?\s*\(?[+-]?[\d,]+(?:\.\d+)?\)?\s*(?:%|x|times|million|billion|thousand)?',scalar,re.I):continue
                if col in timecols and not any(key(label) in time_labels for label in labels):continue
                column_metric=any(contains_label(r[col],label) for _,r in preceding for label in labels if label)
                if not row_metric and not column_metric:continue
                header=None
                for hi,h in reversed(preceding):
                    all_years=set().union(*(years(c) for c in h))
                    if wanted and all_years:
                        if not years(h[col])&wanted:header=False
                        else:header=table[hi]
                        break
                if header is False:continue
                # Entity columns in comparison tables have the same status as
                # year columns when the requested scope names one explicitly.
                entity_header=next((r for _,r in reversed(preceding) if scope not in {'','company','thecompany','group'} and any(key(c)==scope for c in r)),None)
                if entity_header and key(entity_header[col])!=scope and not any(key(c)==scope for c in row):continue
                matches.append({'kind':'table','header':header or (table[preceding[-1][0]] if preceding else ''),
                    'row':table[ri],'column_index':col,'value':value})
    unique={(m['header'],m['row'],m['column_index']):m for m in matches}
    return next(iter(unique.values())) if len(unique)==1 else None

def support(binding,goal,context,aliases,notes=None):
    value=binding['value'];spans=verified_quotes(binding,context)
    alignment=binding.get('label_alignment') or {}
    if not isinstance(alignment,dict):raise ProtocolError('Invalid label alignment')
    label=binding.get('source_label') or alignment.get('source_label')
    explanation=notes or alignment.get('explanation')
    names=[goal.metric,*aliases]
    if label:
        if not isinstance(label,str) or copied_span(label,context) is None:
            raise EvidenceError('Alias requires an explicit quoted source label')
        if semantic_conflict(goal.metric,label):raise EvidenceError('Source label is a different financial metric')
        if any(key(label)==key(n) for n in names):names.append(label)
        elif table_support(context,names,value,goal.constraints):
            # source_label is an optional adapter field, not an Appendix F
            # requirement. A category row label is not an alias of the
            # metric's independently matched column header.
            pass
        elif not isinstance(explanation,str) or not explanation.strip():
            raise EvidenceError('An unregistered alias needs its explanation in notes')
        else:names.append(label)
    if not spans and not label:raise EvidenceError('OES snippet is not a verbatim context span')
    if not label and not any(printed(value,s) for s in spans):
        raise EvidenceError('OES returned a computed or unquoted number')
    # The source label can also be supplied by the paper's notes field.
    if explanation and not label:
        for candidate in re.findall(r'["“](.*?)["”]|\bvia\s+(?:the\s+)?alias\s+([^.;]+)',str(explanation),re.I):
            candidate=next((v.strip() for v in candidate if v.strip()),'')
            if candidate and copied_span(candidate,context) and not semantic_conflict(goal.metric,candidate):names.append(candidate)
    proof=table_support(context,names,value,goal.constraints)
    if proof:
        return {'spans':list(dict.fromkeys([*spans,proof['header'],proof['row']])),'table_coordinate_support':proof}
    wanted=years(goal.constraints.temporal_scope)
    candidates=[*spans,*re.split(r'\n|(?<=[.!?。！？])\s+',context)]
    for span in candidates:
        if '|' in span:continue  # Table cells need a matching coordinate.
        if not printed(value,span):continue
        if wanted and years(span) and not wanted&years(span):continue
        matched=[n for n in names if n and contains_label(span,n)]
        if not matched:continue
        # Do not take Debt's number from "Revenue: 10; Debt: 20".
        contradicted=False
        for n in matched:
            literal=re.search(re.escape(n)+r'\s*[:=]\s*[$£€¥￥]?\s*([+-]?[\d,]+(?:\.\d+)?)',span,re.I)
            if literal and not printed(value,literal[1]):contradicted=True
        if contradicted:continue
        actual=copied_span(span,context)
        if actual:return {'spans':list(dict.fromkeys([*spans,actual])),'table_coordinate_support':None}
    if not any(any(contains_label(s,n) for n in names if n) for s in spans):
        raise EvidenceError('Evidence snippet has no metric label or registered alias')
    raise EvidenceError('OES returned a computed or unquoted number')
