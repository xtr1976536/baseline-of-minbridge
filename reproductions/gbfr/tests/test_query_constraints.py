import asyncio
from dataclasses import asdict
import json

from gbfr.engine import GBFR
from gbfr.graph import Metric,MetricGraph
from gbfr.query_constraints import bind_query_entity,explicit_companies,reporting_declarations
from gbfr.types import Constraints,Goal
from .helpers import ScriptedClient


def goal(entity):return Goal('Revenue',Constraints('2024',entity,{'currency':'$','scale':'million','unit':None}))


def test_uniform_source_company_cannot_replace_the_explicit_query_company():
    old=[goal('Vega Incorporated - domestic segment'),goal('Vega Incorporated - domestic segment')]
    q='What was revenue for Orion Corporation in 2024?'
    rebound,audit=bind_query_entity(q,old)
    assert all(g.constraints.entity_scope=='Orion Corporation - domestic segment' for g in rebound)
    assert all(g.constraints.temporal_scope=='2024' and g.constraints.meta==old[0].constraints.meta for g in rebound)
    assert len(audit)==2 and q[slice(*audit[0]['query_span'])]=='Orion Corporation'
    assert old[0].constraints.entity_scope=='Vega Incorporated - domestic segment'


def test_entity_binding_keeps_multi_entity_comparisons_and_name_variants():
    for q,gg in [
        ('Compare Orion Corporation and Vega Incorporated.',[goal('Orion Corporation'),goal('Vega Incorporated')]),
        ('Find Revenue for Orion Corporation.',[goal('Orion Inc.')]),
        ('Find Revenue for Orion Corporation.',[goal('Orion Corporation'),goal('Vega Incorporated')]),
        ('Find Revenue for Orion Corporation.',[goal('the company')]),
        ('Find Revenue for Orion.',[goal('Vega Incorporated')]),
    ]:
        rebound,audit=bind_query_entity(q,gg)
        assert rebound==gg and audit==[]


def test_bound_entity_still_requires_an_evidence_operator_decision():
    c=asdict(goal('Vega Incorporated').constraints)
    plan={'reasoning_type':'DirectRetrieval','operator':'sum','precision':'unknown','subgoals':[{'metric':'Revenue','constraints':c}]}
    class Client(ScriptedClient):
        async def json(self,task,prompt):
            if task=='OES':
                var=prompt.data['var_list'][0]
                assert var['constraints']['entity_scope']=='Orion Corporation'
            return await super().json(task,prompt)
    client=Client(c,{},plan=plan)
    p=asyncio.run(GBFR(MetricGraph([Metric('Revenue',[],'','atomic',[])]),client).predict(
        'Find Revenue for Orion Corporation.','Vega Incorporated Revenue: 80.'))
    assert p.status=='abstained'
    assert [e['operator'] for e in p.trace['events']]==['OQA','query_constraint_binding','OES']
    assert p.trace['events'][0]['response']['subgoals'][0]['constraints']['entity_scope']=='Vega Incorporated'
    assert len([t for t,_ in client.calls if t=='OES'])==1


def test_company_spans_do_not_swallow_query_verbs_or_another_company():
    q='Compare Orion Corporation and Vega Incorporated.'
    assert [n for n,_ in explicit_companies(q)]==['Orion Corporation','Vega Incorporated']
    gg=[goal('Vega Incorporated'),goal('Vega Incorporated')]
    assert bind_query_entity(q,gg)==(gg,[])
    assert [n for n,_ in explicit_companies('Find Revenue for Bank of Orion Corporation.')]==['Bank of Orion Corporation']


def test_reporting_hints_quote_sections_and_exceptions_without_assigning_values():
    doc='Amounts in USD millions, except per-share data.\n| Tax assets | S$ Mil | S$ Mil |\n| Balance | 3 | 5 |'
    hints=reporting_declarations(doc)
    assert len(hints)==2
    assert hints[0]['text']=='Amounts in USD millions, except per-share data.'
    assert hints[1]['text']=='| Tax assets | S$ Mil | S$ Mil |'
    assert all(doc[slice(*h['span'])]==h['text'] for h in hints)
    assert all(set(h)=={'text','span'} for h in hints)


def test_an_inline_amount_does_not_become_a_whole_table_reporting_scale():
    doc='Settlements: (70). A separate future exposure was USD 140 million. Shares repurchased: 1.2 million shares.'
    assert reporting_declarations(doc)==[]
    assert reporting_declarations('All figures are in thousands.')[0]['text']=='All figures are in thousands.'
