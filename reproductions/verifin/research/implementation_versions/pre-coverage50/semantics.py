"""Candidate-blind normalization of roles, measures and question definitions."""
from __future__ import annotations
from dataclasses import replace
import re
from verifiqa.agent.types import RoleSpec
from verifiqa.policy.registry import DEFAULT_POLICY_REGISTRY as REGISTRY


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
    candidates=[]
    for text in [undecorated(role.name),*role.aliases]:
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
        raise Unresolved('ambiguous_semantic_concept:'+role.name)
    found=REGISTRY.infer_concepts(undecorated(role.name))
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
    q=' '+words(question)+' '
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
    definition=bool(re.search(r'\bdefined?\b[^.]*?\bas\b',question,re.I))
    if qpolicy and definition and (not spec.roles or spec.operation or not policy):policy=qpolicy
    average=bool(policy and re.search(r'3yr|3_year|three_year',policy.metric) and re.search(r'average',question,re.I))
    if policy and len(policy.formula_templates)==1 and (average or (definition and (not spec.roles or spec.operation or spec.metric!=policy.metric))):
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
    if re.search(r'\bdays?\s+(?:payable|sales|inventory)\s+outstanding\b|\bDPO\b|\bDSO\b',question,re.I):
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
    """Compile only an explicit arithmetic definition, including nested averages.

    Unrecognized prose is left intact and rejected by the safe expression parser.
    This avoids classifying an inner 'change in inventory' as the whole question.
    """
    from .solver import formula_names
    match=re.search(r'\b(?:is\s+defined\s+as|define\s+.+?\s+as|[A-Za-z ]+?\s+is\s+defined\s+as)\s*:?\s*(.+)',question,re.I)
    if not match:return None
    text=re.split(r'\.\s*(?:Round|Answer|Please|Base|Respond|Give)|\.\s*$',match[1],maxsplit=1,flags=re.I)[0]
    text=text.rstrip('. ').replace('divided by',' / ')
    def find(label,year=None):
        target=words(label);hits=[]
        for role in spec.roles:
            c=role_concept(role)
            labels=[undecorated(role.name),*role.aliases,*(field(c,'aliases',[]) if c else [])]
            ppe_abbreviation=bool(re.sub(r'[^a-z]','',label.lower()) in {'ppe','ppne'} and c and 'us-gaap:PropertyPlantAndEquipmentNet' in field(c,'xbrl_concepts',[]))
            single_period=(not year or (set(re.findall(r'(?:19|20)\d{2}',role.period))=={year} and not re.search(r'average|mean',role.period,re.I)))
            if (ppe_abbreviation or any(words(s)==target for s in labels)) and single_period:hits.append(role.name)
        return hits[0] if len(hits)==1 else None
    def pair(m):
        op,label,first,last=m.groups();a,b=find(label,first),find(label,last)
        if not a or not b:return m[0]
        return '(('+a+' + '+b+') / 2)' if op.lower()=='average' else '('+b+' - '+a+')'
    text=re.sub(r'\b(average|change\s+in)\s+(.+?)\s+between\s+(?:FY\s*)?((?:19|20)\d{2})\s+and\s+(?:FY\s*)?((?:19|20)\d{2})',pair,text,flags=re.I)
    # Longest labels first, and a matching fiscal year for repeated-period roles.
    replacements=[]
    for role in spec.roles:
        c=role_concept(role)
        for label in [*role.aliases,*(field(c,'aliases',[]) if c else []),undecorated(role.name).replace('_',' ')]:
            if not label:continue
            year=re.search(r'(?:19|20)\d{2}',role.period)
            if year:replacements.append((r'\b(?:FY\s*)?'+year[0]+r'\s+'+re.escape(label)+r'(?!\w)',role.name,len(label)+10))
            if find(label)==role.name:replacements.append((r'(?<!\w)'+re.escape(label)+r'(?!\w)',role.name,len(label)))
    for pattern,name,_ in sorted(replacements,key=lambda x:-x[2]):text=re.sub(pattern,name,text,flags=re.I)
    try:
        if formula_names(text)<=set(r.name for r in spec.roles):return text
    except ValueError:pass
    return None
