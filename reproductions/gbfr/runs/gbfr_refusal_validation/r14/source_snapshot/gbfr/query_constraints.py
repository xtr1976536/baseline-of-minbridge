"""Bind an unambiguous, explicitly named query entity before evidence search.

This is constraint propagation, not an evidence judgement. No values are filled
and an unresolved entity must still pass through OES normally.
"""
from dataclasses import replace
import re

from .types import Goal

_name=r"[A-Z][A-Za-z0-9&.'’()-]*"
_suffix=r'(?i:Corporation|Incorporated|Corp\.?|Inc\.?|Limited|Ltd\.?|PLC)'
_company=re.compile(r'\b'+_name+r'(?:(?:\s+(?:'+_name+r'|of|the|and|&)){0,6})\s+'+_suffix+r'(?!\w)')
_legal=re.compile(r'\s+'+_suffix+r'$',re.I)


def explicit_companies(text):
    return [(m.group().strip(),m.span()) for m in _company.finditer(text)]


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
