"""Compile explicit question equations and nested definitions without a claim."""
from __future__ import annotations
import ast
import re
from functools import lru_cache
from verifiqa.policy.registry import DEFAULT_POLICY_REGISTRY as REGISTRY
from .semantics import words,undecorated,role_concept,field
from .solver import formula_names


def definitions(question):
    pattern=re.compile(r'(?:(?P<n>[A-Za-z][A-Za-z0-9 &_-]{0,65}?)\s+is\s+defined\s+as|\bdefine\s+(?P<v>[A-Za-z][A-Za-z0-9 &_-]{0,65}?)\s+as)\s*:?\s*',re.I)
    matches=list(pattern.finditer(question));out=[]
    for i,m in enumerate(matches):
        name=(m['n'] or m['v']).strip();name=re.sub(r'\s+here$','',name,flags=re.I)
        body=question[m.end():matches[i+1].start() if i+1<len(matches) else len(question)]
        body=re.split(r'\.\s*(?:Round|Answer|Please|Base|Respond|Give|Calculate|Address)|\.\s*$',body,maxsplit=1,flags=re.I)[0].rstrip('. ')
        out.append((name,body))
    return out


def compile_definition(body,spec,*,default_year=None):
    text=body
    # Remove only grammatical source annotations; the full original question is
    # retained as authority and is still supplied to the planner/grounder.
    text=re.sub(r'[\[(]\s*from\s+(?:the\s+)?[^\])]*(?:statement|sheet)\s*[\])]','',text,flags=re.I)
    text=re.sub(r'\s+from\s+the\s+(?:cash flow|income|P&L|balance)[^+*/-]*?(?:statement|sheet)\s*$','',text,flags=re.I)
    text=re.sub(r'\bunadjusted\s+(?=operating\s+(?:income|profit)\b)','',text,flags=re.I)
    for phrase,operator in [('divided by','/'),('multiplied by','*'),('plus','+'),('less','-'),('minus','-')]:
        text=re.sub(r'\b'+phrase+r'\b',' '+operator+' ',text,flags=re.I)
    @lru_cache(maxsize=1024)
    def find(label,year=None):
        target=words(label);year=year or default_year;hits=[]
        for r in spec.roles:
            c=role_concept(r);aliases=[undecorated(r.name),*r.aliases,*field(c,'aliases',[])] if c else [undecorated(r.name),*r.aliases]
            ppe=re.sub('[^a-z]','',label.lower()) in {'ppe','ppne'} and c and 'us-gaap:PropertyPlantAndEquipmentNet' in field(c,'xbrl_concepts',[])
            period=not year or (set(re.findall(r'(?:19|20)\d{2}',r.period))=={year} and not re.search(r'average|mean',r.period,re.I))
            if period and (ppe or any(words(a)==target for a in aliases)):hits.append(r.name)
        return hits[0] if len(hits)==1 else None
    def pair(m):
        op,label,first,last=m.groups();a,b=find(label,first),find(label,last)
        if not a or not b:return m[0]
        return '(('+a+' + '+b+') / 2)' if op.lower()=='average' else '('+b+' - '+a+')'
    text=re.sub(r'\b(average|change\s+in)\s+(.+?)\s+between\s+(?:FY\s*)?((?:19|20)\d{2})\s+and\s+(?:FY\s*)?((?:19|20)\d{2})',pair,text,flags=re.I)
    replacements=[]
    for r in spec.roles:
        c=role_concept(r);aliases=[*r.aliases,*field(c,'aliases',[]),undecorated(r.name).replace('_',' ')] if c else [*r.aliases,undecorated(r.name).replace('_',' ')]
        for label in aliases:
            if not label:continue
            year=re.search(r'(?:19|20)\d{2}',r.period)
            if year and not re.search(r'average|mean',r.period,re.I):replacements.append((r'\b(?:FY\s*)?'+year[0]+r'\s+'+re.escape(label)+r'(?!\w)',r.name,len(label)+10))
            if find(label)==r.name:replacements.append((r'(?<!\w)'+re.escape(label)+r'(?!\w)',r.name,len(label)))
    for pattern,name,_ in sorted(replacements,key=lambda x:-x[2]):text=re.sub(pattern,name,text,flags=re.I)
    try:
        if formula_names(text)<=set(r.name for r in spec.roles):return text
    except ValueError:pass
    return None


def expanded_definitions(question,spec):
    defs=definitions(question);mapping={name:body for name,body in defs};cache={}
    def expand(name,stack):
        if name in stack:return None
        if name in cache:return cache[name]
        body=mapping[name]
        for other in sorted(mapping,key=len,reverse=True):
            if other==name or not re.search(r'\b'+re.escape(other)+r'\b',body,re.I):continue
            inner=expand(other,stack|{name})
            if inner is None:return None
            body=re.sub(r'\b'+re.escape(other)+r'\b','('+inner+')',body,flags=re.I)
        cache[name]=compile_definition(body,spec)
        return cache[name]
    for name,_ in defs:expand(name,set())
    return defs,cache


def target_definition(question,spec):
    defs,cache=expanded_definitions(question,spec)
    p=REGISTRY.find_policy(spec.metric);targets={words(undecorated(spec.metric)),*(words(a) for a in p.metric_aliases if p)} if p else {words(undecorated(spec.metric))}
    # Acronyms are expanded only when the question explicitly defines the name.
    for name,_ in defs:
        variants={words(name)}
        for m in re.finditer(r'([A-Za-z][A-Za-z -]{2,60})\s*\('+re.escape(name)+r'\)',question,re.I):variants.add(words(m[1]))
        if variants & targets:return cache[name]
    return None


def checked_subdefinitions(question,spec):
    """A disclosed inner definition may support a registry's outer composition."""
    from .authority import signature
    p=REGISTRY.find_policy(spec.metric)
    if not p or not re.search(r'ebitda|margin|average|less_capex',spec.metric):return []
    defs=definitions(question)
    if not defs:return []
    tree=ast.parse(spec.formula,mode='eval')
    subtrees=set()
    for node in ast.walk(tree):
        if isinstance(node,(ast.BinOp,ast.UnaryOp)):
            try:subtrees.add(signature(ast.unparse(node)))
            except ValueError:pass
    years=sorted({year for r in spec.roles for year in re.findall(r'(?:19|20)\d{2}',r.period)})
    checked=[]
    for name,body in defs:
        expressions=[]
        for year in years or [None]:
            expr=compile_definition(body,spec,default_year=year)
            if expr is None or signature(expr) not in subtrees:return []
            expressions.append(expr)
        checked.append({'name':name,'question_definition':body,'expressions':expressions})
    return checked
