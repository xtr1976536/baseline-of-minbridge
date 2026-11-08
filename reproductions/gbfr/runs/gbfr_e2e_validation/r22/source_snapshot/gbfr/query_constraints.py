"""Bind an unambiguous, explicitly named query entity before evidence search.

This is constraint propagation, not an evidence judgement. No values are filled
and an unresolved entity must still pass through OES normally.
"""
from dataclasses import replace
import json
import re

from .types import Goal

_name=r"[A-Z][A-Za-z0-9&.'’()-]*"
_suffix=r'(?i:Corporation|Incorporated|Corp\.?|Inc\.?|Limited|Ltd\.?|PLC)'
_company=re.compile(r'\b(?!(?i:what|which|compare|find|compute|calculate|please|how|in|for|at|by|from|to)\b)'
    +_name+r'(?:(?:\s+(?:'+_name+r'|of|the|and|&)){0,6}?)\s+'+_suffix+r'(?!\w)')
_legal=re.compile(r'\s+'+_suffix+r'$',re.I)
_reporting_units=re.compile(
    r'\b(?:in|amounts?\s+(?:are\s+)?(?:in\s+)?)\s+(?:(?:USD|GBP|EUR|SGD|US\$|S\$|\$|£|€)\s*)?'
    r'(?:thousands?|millions?|billions?|trillions?)\b'
    r'|(?:\bUSD|\bGBP|\bEUR|\bSGD|US\$|S\$|HK\$|A\$|\$|£|€)\s*'
    r'(?:thousands?|millions?|billions?|trillions?|mil|mn|mm|bn|000s?)\b',re.I)


def explicit_companies(text):
    return [(m.group().strip(),m.span()) for m in _company.finditer(text)]


def reporting_declarations(context):
    """Quote reporting-unit declarations, never infer them from inline amounts.

    Keep the complete source line, including exceptions such as per-share
    data. These are optional reading aids, not global unit assignments.
    """
    found=[];seen=set()
    for m in _reporting_units.finditer(context):
        start=context.rfind('\n',0,m.start())+1
        end=context.find('\n',m.end())
        if end<0:end=len(context)
        # Very long narrative lines are still quoted exactly, with local
        # context; there is no numeric extraction or annotation in this aid.
        if end-start>400:start=max(start,m.start()-140);end=min(end,m.end()+140)
        key=(start,end)
        if key in seen:continue
        seen.add(key)
        found.append({'text':context[start:end],'span':[start,end]})
    return found


def table_structure_hints(context,*,max_tables=6,max_row_labels=48,max_header_rows=6,max_columns=24,max_hint_chars=12000):
    """Quote Markdown table structure without selecting financial values.

    Column indices and source spans preserve empty cells, nested year headers,
    HTML footnote markers, and multi-year change labels. A period label is not
    an instruction to replace the query's constraint or split a range.
    """
    if any(type(n) is not int or n<1 for n in [max_tables,max_row_labels,max_header_rows,max_columns]):
        raise ValueError('Table hint limits must be positive integers')
    if type(max_hint_chars) is not int or max_hint_chars<2000:raise ValueError('Table hint character budget must be at least 2000')
    lines=[];offset=0
    for line in context.splitlines(keepends=True):
        text=line.rstrip('\r\n')
        lines.append((text,offset,offset+len(text)));offset+=len(line)
    tables=[];i=0
    year=r'(?<!\d)(?:19|20)\d{2}(?!\d)'
    numeric=re.compile(r'^\s*(?:US\$|S\$|HK\$|A\$|\$|£|€|¥)?\s*\(?[+−–-]?\s*(?:\d[\d,.]*|\.\d+)\)?\s*%?\s*$')
    def is_table(text):return text.lstrip().startswith('|') and text.rstrip().endswith('|')
    def cells(text):return [s.strip() for s in re.split(r'(?<!\\)\|',text.strip()[1:-1])]
    while i<len(lines):
        if not is_table(lines[i][0]):i+=1;continue
        start=i
        while i<len(lines) and is_table(lines[i][0]):i+=1
        block=lines[start:i];parsed=[cells(t) for t,_,_ in block]
        separators=[j for j,cc in enumerate(parsed) if cc and all(re.fullmatch(r':?-{3,}:?',c) for c in cc)]
        # Pipe-containing prose is not a Markdown table without a separator.
        if not separators:continue
        separator=separators[0];headers=[];labels=[];periods=[];body=False
        for row_index,((text,a,b),cc) in enumerate(zip(block,parsed)):
            if row_index in separators:continue
            data_numbers=any(numeric.fullmatch(c) and not re.fullmatch(year,c) for c in cc[1:])
            first=cc[0] if cc else ''
            unit_or_header=bool(re.search(r'\bin\s+(?:thousands?|millions?|billions?)\b',first,re.I)
                or re.fullmatch(r'(?:year|period|date|fiscal year|calendar year)',first,re.I))
            repeated_period_header=bool(body and re.fullmatch(year,first) and not data_numbers and cc[1:]
                and any(re.fullmatch(year,h['cells'][0]['text'])
                    and [c['text'].casefold() for c in h['cells'][1:]]==[c.casefold() for c in cc[1:]] for h in headers))
            header=row_index<separator or (not body and not data_numbers and (not first or unit_or_header)) or repeated_period_header
            if header:
                headers.append({'row_index':row_index,'text':text,'span':[a,b],
                    'cells':[{'column_index':j,'text':c} for j,c in enumerate(cc)],
                    'repeated_period_header':repeated_period_header})
                for col,c in enumerate(cc):
                    yy=re.findall(year,c)
                    if yy:periods.append({'header_row_index':row_index,'column_index':col,'text':c,'years':yy})
            else:
                body=True
                # Use column zero, never the first non-empty cell: an empty
                # subtotal label must not turn its amount into a metric label.
                opening=text.index('|')+1
                boundary=re.search(r'(?<!\\)\|',text[opening:])
                raw_first=text[opening:opening+boundary.start()] if boundary else text[opening:]
                label_start=a+opening+len(raw_first)-len(raw_first.lstrip())
                numeric_first=bool(numeric.fullmatch(first) and not re.fullmatch(year,first))
                label='' if numeric_first else first
                labels.append({'row_index':row_index,'text':label,'span':[label_start,label_start+len(label)],
                    'row_span':[a,b],'years':re.findall(year,label),'numeric_first_column':numeric_first})
        markers=set(re.findall(r'\(\s*([0-9]+|[a-z])\s*\)', '\n'.join(t for t,_,_ in block),re.I))
        notes=[]
        if markers:
            for text,a,b in lines[max(0,start-3):min(len(lines),i+4)]:
                note=re.match(r'^\s*\(\s*([0-9]+|[a-z])\s*\)\s*',text,re.I)
                if note and note[1] in markers:notes.append({'text':text,'span':[a,b]})
        period_headers=[h for h in headers if h['cells'] and re.fullmatch(year,h['cells'][0]['text'])]
        period_groups=[]
        if len(period_headers)>1:
            for pos,h in enumerate(period_headers):
                end_row=period_headers[pos+1]['row_index'] if pos+1<len(period_headers) else len(block)
                period_groups.append({'header_row_index':h['row_index'],'period_label':h['cells'][0]['text'],
                    'header_span':h['span'][:],'table_row_start':h['row_index']+1,'table_row_end_exclusive':end_row})
        header_count=len(headers);row_label_count=len(labels)
        shown=headers[:max_header_rows]
        shown_rows={r['row_index'] for r in shown}
        eligible_periods=[p for p in periods if p['header_row_index'] in shown_rows and p['column_index']<max_columns]
        for row in shown:
            row['columns_truncated']=len(row['cells'])>max_columns
            row['cells']=row['cells'][:max_columns]
            if len(row['text'])>800:
                row['full_row_span']=row['span'][:];row['text']=row['text'][:800];row['span'][1]=row['span'][0]+800;row['text_truncated']=True
            for c in row['cells']:
                if len(c['text'])>160:c['text']=c['text'][:160];c['text_truncated']=True
        labels=labels[:max_row_labels]
        for label in labels:
            if len(label['text'])>160:
                label['full_label_span']=label['span'][:];label['text']=label['text'][:160];label['span'][1]=label['span'][0]+160;label['text_truncated']=True
        for note in notes:
            if len(note['text'])>800:
                note['full_note_span']=note['span'][:];note['text']=note['text'][:800];note['span'][1]=note['span'][0]+800;note['text_truncated']=True
        for period in eligible_periods:
            if len(period['text'])>160:period['text']=period['text'][:160];period['text_truncated']=True
        tables.append({'table_index':len(tables),'span':[block[0][1],block[-1][2]],
            'column_count':max(map(len,parsed)),'header_rows':shown,'period_columns':eligible_periods[:96],'row_labels':labels,'footnotes':notes,
            'period_groups':period_groups[:max_header_rows],
            'source_header_row_count':header_count,'source_body_row_count':row_label_count,
            'truncated':{'header_rows':header_count>len(shown),'row_labels':row_label_count>len(labels),
                'columns':any(len(cc)>max_columns for cc in parsed),'period_columns':len(eligible_periods)>96,
                'period_groups':len(period_groups)>max_header_rows}})
    shown=tables[:max_tables]
    if shown:
        shown[-1]['following_tables_omitted']=max(0,len(tables)-max_tables)
        shown[-1]['source_table_count']=len(tables)
    # Bound the optional aid separately from the original document. Trim
    # structural entries in source order only, without consulting query,
    # financial values, labels, or expected answers.
    while shown and len(json.dumps(shown,ensure_ascii=False))>max_hint_chars:
        row_table=next((t for t in reversed(shown) if t['row_labels']),None)
        if row_table:
            row_table['row_labels'].pop();row_table['truncated']['row_labels']=True
        elif len(shown)>1:
            shown.pop();shown[-1]['following_tables_omitted']=len(tables)-len(shown);shown[-1]['source_table_count']=len(tables)
        elif shown[0]['footnotes']:
            shown[0]['footnotes'].pop();shown[0]['truncated']['footnotes']=True
        elif shown[0]['period_columns']:
            shown[0]['period_columns'].pop();shown[0]['truncated']['period_columns']=True
        elif shown[0]['period_groups']:
            shown[0]['period_groups'].pop();shown[0]['truncated']['period_groups']=True
        elif len(shown[0]['header_rows'])>1:
            shown[0]['header_rows'].pop();shown[0]['truncated']['header_rows']=True
        else:
            row=shown[0]['header_rows'][0]
            if len(row['cells'])>1:row['cells'].pop();row['columns_truncated']=True
            else:break
        shown[-1]['hint_budget_truncated']=True
    return shown


def bind_query_entity(question,goals):
    """Repair uniform source-entity substitution for one named query company.

    Deliberately conservative: multiple query companies, multiple planned
    companies, an entity not named as a company, or a shared company name stem
    are left to the semantic operators. Category/period constraints are kept.
    """
    found=explicit_companies(question)
    unique={n.casefold():n for n,_ in found}
    if len(unique)!=1:return goals,[]
    target=next(iter(unique.values()))
    planned=[]
    for g in goals:
        names=explicit_companies(str(g.constraints.entity_scope or ''))
        if len(names)!=1:return goals,[]
        planned.append(names[0])
    if not planned or len({n.casefold() for n,_ in planned})!=1:return goals,[]
    old=planned[0][0]
    stem=lambda n:re.sub(r'[^a-z0-9]','',_legal.sub('',n).casefold())
    if stem(target) in stem(old) or stem(old) in stem(target):return goals,[]
    # If both names were actually requested, this is a comparison, not a
    # substitution. Also keep an explicit query alias such as Foo (Bar Inc.).
    if old.casefold() in question.casefold():return goals,[]
    rebound=[];audit=[]
    for g,(name,(start,end)) in zip(goals,planned):
        scope=str(g.constraints.entity_scope)
        entity=scope[:start]+target+scope[end:]
        rebound.append(Goal(g.metric,replace(g.constraints,entity_scope=entity)))
        audit.append({'metric':g.metric,'before':scope,'after':entity,
                      'query_span':next(list(span) for n,span in found if n.casefold()==target.casefold()),
                      'reason':'Preserve the one explicitly named query company; OQA uniformly substituted a different company.'})
    return rebound,audit
