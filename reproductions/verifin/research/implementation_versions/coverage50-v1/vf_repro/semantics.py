"""Candidate-blind normalization of roles, measures and question definitions."""
from __future__ import annotations
from dataclasses import replace
from functools import lru_cache
import re
from verifiqa.agent.types import RoleSpec
from verifiqa.policy.registry import DEFAULT_POLICY_REGISTRY as REGISTRY


@lru_cache(maxsize=32768)
def words(text):
    text=re.sub(r'([a-z])([A-Z])',r'\1 \2',str(text))
    text=text.lower().replace('%',' percent ').replace('&',' and ')
    return ' '.join(re.findall(r'[a-z0-9]+',text))


def undecorated(name):
    return re.sub(r'(?:_(?:fy)?(?:19|20)\d{2}|_y[1-9]|_(?:start|end|beginning|ending|prior|previous|latest))+$','',name,flags=re.I)


# A semantic refinement, not a value-based substitute for RestructuringCharges.
# The combined measure is explicitly distinct in the US-GAAP taxonomy and the
# filing's own labels. No company, year, sample ID or amount appears in the rule.
COMBINED_RESTRUCTURING={
    'concept_id':'RestructuringAndImpairmentLike',
    'aliases':['restructuring and impairment charges','total restructuring and impairment charges',
               'restructuring costs and asset impairment charges'],
    'xbrl_concepts':['us-gaap:RestructuringCostsAndAssetImpairmentCharges'],
    'unit_kind':'money',
    'source_refs':[{'title':'US GAAP taxonomy: RestructuringCostsAndAssetImpairmentCharges',
                    'url':'https://xbrl.fasb.org/us-gaap/2025/'}],
}


def role_concept(role):
    """Most specific exact semantic alias; values never participate."""
    return _role_concept(undecorated(role.name),tuple(role.aliases))


@lru_cache(maxsize=8192)
def _role_concept(name,aliases):
    candidates=[]
    for text in [name,*aliases]:
        target=words(text)
        for c in REGISTRY.concepts.values():
            if target and any(target==words(a) for a in c.aliases):
                candidates.append((len(target.split()),c.concept_id,c))
        if target and target in {words(a) for a in COMBINED_RESTRUCTURING['aliases']}:
            candidates.append((len(target.split())+1,COMBINED_RESTRUCTURING['concept_id'],COMBINED_RESTRUCTURING))
    if candidates:
        longest=max(x[0] for x in candidates)
        best={cid:c for n,cid,c in candidates if n==longest}
        if len(best)==1:return next(iter(best.values()))
        from .grounding import Unresolved
        raise Unresolved('ambiguous_semantic_concept:'+name)
    found=REGISTRY.infer_concepts(name)
    return REGISTRY.concepts[next(iter(found.values()))] if found else None


def field(concept,name,default=None):
    return concept.get(name,default) if isinstance(concept,dict) else getattr(concept,name,default)


def role_measure(role, output_unit, filing, proposal=None):
    from .grounding import unit,Unresolved
    c=role_concept(role) if not role.concept else None
    kind=field(c,'unit_kind','') if c else ''
    if role.concept:
        measures={f['unit'] for f in filing.data['facts'] if f['concept']==role.concept}
        if len(measures)==1:
            raw=next(iter(measures))
            return output_unit if unit(raw)[0]==unit(output_unit)[0] else raw
    if kind=='money':
        outkind,_=unit(output_unit)
        if outkind not in {'pure','shares'} and '/' not in outkind:return output_unit
        if '/' in outkind:return outkind.split('/')[0].upper()
        qnames=field(c,'xbrl_concepts',[])
        currencies={unit(f['unit'])[0] for f in filing.data['facts'] if f['concept'] in qnames and not f['period'].get('dimensions') and re.fullmatch(r'iso4217:[A-Z]{3}',f['unit'])}
        if not currencies:
            from .grounding import tokens
            required=tokens(role.aliases[0] if role.aliases else undecorated(role.name))
            matches={q for q,labels in filing.data.get('labels',{}).items() if any(required and required<=tokens(label) for label in labels)}
            currencies={unit(f['unit'])[0] for f in filing.data['facts'] if f['concept'] in matches and not f['period'].get('dimensions') and re.fullmatch(r'iso4217:[A-Z]{3}',f['unit'])}
        if not currencies and proposal:
            proposed_kind,_=unit(proposal.unit)
            if proposed_kind not in {'pure','shares'} and '/' not in proposed_kind:return proposed_kind.upper()+' millions'
        if len(currencies)!=1:raise Unresolved('operand_currency_not_established:'+role.name)
        return next(iter(currencies)).upper()+' millions'
    if kind in {'percent','percentage'}:return 'percent'
    if kind in {'ratio','count','pure','number'}:return 'ratio'
    if kind=='shares':return 'shares'
    if kind=='per_share':
        outkind,_=unit(output_unit)
        return (outkind.split('/')[0].upper()+' per share') if outkind not in {'pure','shares'} else 'USD per share'
    if proposal:
        try:unit(proposal.unit);return proposal.unit
        except Unresolved:pass
    return output_unit


def question_policy(question):
    # Definition operands are not the requested target (e.g. AP inside CCC).
    target=re.split(r'\?|\bdefine\b|\bis\s+defined\s+as\b',question,maxsplit=1,flags=re.I)[0]
    q=' '+words(target)+' '
    matches=[]
    for p in REGISTRY.policies:
        aliases=[p.metric,*p.metric_aliases]
        score=max([len(words(a).split()) for a in aliases if len(words(a))>=3 and ' '+words(a)+' ' in q] or [0])
        if score:matches.append((score,p))
    if not matches:return None
    best=max(n for n,_ in matches);policies={p.policy_id:p for n,p in matches if n==best}
    return next(iter(policies.values())) if len(policies)==1 else None


def question_years(question):
    years=sorted(set(re.findall(r'(?:19|20)\d{2}',question)))
    if len(years)==2 and re.search(r'3\s*year|three.year',question,re.I) and int(years[1])-int(years[0])==2:
        return [str(y) for y in range(int(years[0]),int(years[-1])+1)]
    return years


def normalize_plan(spec,question,evidence,filing):
    """Validate planner structure with explicit question text and public policies."""
    from .grounding import unit,Unresolved
    from .solver import formula_names
    adjustments=[]
    qpolicy=question_policy(question)
    policy=REGISTRY.find_policy(spec.metric)
    years=question_years(question)
    if policy and len(years)==3 and re.search(r'average',question,re.I):
        for candidate in REGISTRY.policies:
            if candidate.metric.startswith(policy.metric+'_') and re.search(r'3yr|3_year|three_year',candidate.metric):
                policy=candidate;break
    definition=bool(re.search(r'\bdefined?\b[^.]*?\bas\b',question,re.I))
    if qpolicy and definition and (not spec.roles or spec.operation or not policy):policy=qpolicy
    average=bool(policy and re.search(r'3yr|3_year|three_year',policy.metric) and re.search(r'average',question,re.I))
    derived_operands=bool(policy and any(REGISTRY.find_policy(undecorated(r.name)) and
        REGISTRY.find_policy(undecorated(r.name)).formula_templates!=[undecorated(r.name)] for r in spec.roles))
    if policy and len(policy.formula_templates)==1 and (average or derived_operands or (definition and (not spec.roles or spec.operation or spec.metric!=policy.metric))):
        template=policy.formula_templates[0];names=sorted(formula_names(template));years=question_years(question)
        old={r.name:r for r in spec.roles};roles=[]
        for name in names:
            r=old.get(name);suffix=re.search(r'_y([1-9])$',name)
            if suffix:
                index=int(suffix[1])-1
                if index>=len(years):raise Unresolved('question_period_count_does_not_match_registry')
                period=years[index]
            elif years:
                period=years[0] if re.search(r'_(?:start|beginning|prior|previous)$',name) else years[-1]
            else:period=r.period if r else spec.period
            aliases=list(r.aliases) if r else []
            for cid in policy.roles.get(name,{}).get('concept_ids',[]):
                aliases += REGISTRY.concepts[cid].aliases
            roles.append(RoleSpec(name,list(dict.fromkeys(aliases)),period))
        spec=replace(spec,metric=policy.metric,formula=template,roles=roles,formula_source='policy_registry')
        adjustments.append('question_and_registry_role_structure')
    claim_unit=spec.claim_unit
    if re.search(r'\bdays?\s+(?:payable|sales|inventory)\s+outstanding\b|\bDPO\b|\bDSO\b|\bcash conversion cycle\b|\bCCC\b',question,re.I):
        claim_unit='days'
    else:
        try:unit(claim_unit)
        except Unresolved:
            explicit=re.search(r'\b(USD|EUR|GBP|CAD|AUD|JPY|CNY)\s*(billions?|millions?|thousands?)?\b',question,re.I)
            if explicit:claim_unit=explicit[1].upper()+(' '+explicit[2] if explicit[2] else '')
            elif re.search(r'\bpercent(?:s|age)?\b|%',question,re.I):claim_unit='percent'
            elif policy and ('ratio' in policy.metric or 'turnover' in policy.metric):claim_unit='ratio'
    if claim_unit!=spec.claim_unit:adjustments.append('question_measure')
    spec=replace(spec,claim_unit=claim_unit)
    return spec,adjustments


def question_equation(question,spec):
    """Compile the explicit target, including nested question definitions."""
    from .question_math import target_definition
    return target_definition(question,spec)
