import asyncio
from dataclasses import asdict

import pytest

from gbfr.engine import GBFR,grounded
from gbfr.graph import Metric,MetricGraph
from gbfr.types import Constraints,Goal,ProtocolError
from .helpers import ScriptedClient


C=Constraints('2024','Company A',{'currency':None,'scale':None,'unit':None})


def binding(metric,value,context):
    return {'metric':metric,'value':value,'context':context,'confidence':1,'constraints':asdict(C)}


def test_unregistered_translation_requires_explicit_verbatim_label_and_explanation():
    context='Company A 2024年流动资产42元。'
    b=binding('Current Assets',42,context)
    with pytest.raises(ProtocolError,match='metric label'):
        grounded(b,Goal('Current Assets',C),context,[])
    b['label_alignment']={'kind':'translation','source_label':'流动资产','explanation':'Current Assets is 流动资产 in this Chinese statement.'}
    assert grounded(b,Goal('Current Assets',C),context,[])==42
    b['value']=43
    with pytest.raises(ProtocolError,match='unquoted'):
        grounded(b,Goal('Current Assets',C),context,[])
    b['value']=42;b['label_alignment']['source_label']='非流动资产'
    with pytest.raises(ProtocolError,match='quoted source label'):
        grounded(b,Goal('Current Assets',C),context,[])


def test_translation_does_not_allow_an_unregistered_same_language_alias():
    context='Profit: 42'
    b=binding('Revenue',42,context)
    b['label_alignment']={'kind':'translation','source_label':'Profit','explanation':'These are the same.'}
    with pytest.raises(ProtocolError,match='different financial metric'):
        grounded(b,Goal('Revenue',C),context,[])


def test_disjoint_table_header_grounding_checks_the_value_column():
    header='| Year | Revenue | Debt |';row='| 2024 | 42 | 99 |'
    context=header+'\n| --- | --- | --- |\n| 2023 | 31 | 80 |\n'+row
    b=binding('Revenue',42,row)
    b['context_spans']=[header,row]
    assert grounded(b,Goal('Revenue',C),context,[])==42
    b['value']=99
    with pytest.raises(ProtocolError,match='unquoted'):
        grounded(b,Goal('Revenue',C),context,[])
    b['value']=42;b['context_spans']=['| Year | Invented Revenue | Debt |',row]
    with pytest.raises(ProtocolError,match='non-verbatim'):
        grounded(b,Goal('Revenue',C),context,[])


def test_partial_quotes_recover_one_source_table_coordinate_without_combining_tables():
    context='| Year | Revenue | Debt |\n| --- | --- | --- |\n| 2023 | 31 | 80 |\n| 2024 | 42 | 99 |'
    b=binding('Revenue',42,'2024 | 42');b['context_spans']=['Revenue','2024 | 42']
    assert grounded(b,Goal('Revenue',C),context,[])==42
    b['value']=31;b['context']='2023 | 31';b['context_spans']=['Revenue','2023 | 31']
    with pytest.raises(ProtocolError):grounded(b,Goal('Revenue',C),context,[])
    other='| Year | Debt | Revenue |\n| --- | --- | --- |\n| 2024 | 42 | 100 |'
    b['value']=42;b['context']='2024 | 42';b['context_spans']=['Revenue','2024 | 42']
    with pytest.raises(ProtocolError):grounded(b,Goal('Revenue',C),other,[])


def test_translated_direct_evidence_does_not_need_a_second_judge_call():
    context='Company A 2024年流动资产42元。'
    graph=MetricGraph([Metric('Current Assets',[],'','atomic',[])])
    plan={'reasoning_type':'DirectRetrieval','operator':'sum','precision':'unknown','subgoals':[{'metric':'Current Assets','constraints':asdict(C)}]}
    class Client(ScriptedClient):
        async def json(self,task,prompt):
            r=await super().json(task,prompt)
            if task=='OES' and r['found']:
                r['notes']=None
                r['var_bindings']['v1']['label_alignment']={'kind':'translation','source_label':'流动资产','explanation':'Direct Chinese translation of Current Assets.'}
            return r
    client=Client(asdict(C),{'Current Assets':(42,context)},plan=plan)
    p=asyncio.run(GBFR(graph,client).predict('Find Current Assets',context))
    assert p.status=='answered' and p.value==42
    assert not any(task=='Verify' for task,_ in client.calls)


def test_explicit_contextual_alias_stays_query_local_and_respects_known_concepts():
    graph=MetricGraph([Metric('Initial Deposit',[],'','atomic',[]),Metric('Revenue',[],'','atomic',[]),Metric('Profit',[],'','atomic',[])])
    class Client(ScriptedClient):
        async def json(self,task,prompt):
            r=await super().json(task,prompt)
            if task=='OES' and r['found']:
                b=r['var_bindings']['v1'];r['notes']=None
                label='amount deposited' if b['metric']=='Initial Deposit' else 'Profit'
                b['label_alignment']={'kind':'semantic_alias','source_label':label,'explanation':'Explicit claimed contextual alignment.'}
            return r
    def plan(metric):return {'reasoning_type':'DirectRetrieval','operator':'sum','precision':'unknown','subgoals':[{'metric':metric,'constraints':asdict(C)}]}
    c=Client(asdict(C),{'Initial Deposit':(42,'The amount deposited was 42.')},plan=plan('Initial Deposit'))
    p=asyncio.run(GBFR(graph,c).predict('Find Initial Deposit','The amount deposited was 42.'))
    assert p.status=='answered' and p.value==42 and graph.find('amount deposited') is None
    c=Client(asdict(C),{'Revenue':(42,'Profit: 42')},plan=plan('Revenue'))
    p=asyncio.run(GBFR(graph,c).predict('Find Revenue','Profit: 42'))
    assert p.status=='abstained'  # A distinct known concept cannot be relabelled.


def test_rejected_grounding_prunes_but_malformed_response_is_a_technical_error():
    graph=MetricGraph([Metric('Revenue',[],'','atomic',[])])
    plan={'reasoning_type':'DirectRetrieval','operator':'sum','precision':'unknown','subgoals':[{'metric':'Revenue','constraints':asdict(C)}]}
    c=ScriptedClient(asdict(C),{'Revenue':(90,'Revenue: 100')},plan=plan)
    p=asyncio.run(GBFR(graph,c).predict('Find Revenue','Revenue: 100'))
    assert p.status=='abstained'
    class Broken(ScriptedClient):
        async def json(self,task,prompt):
            if task=='OES':raise ProtocolError('Invalid structured output')
            return await super().json(task,prompt)
    with pytest.raises(ProtocolError):
        asyncio.run(GBFR(graph,Broken(asdict(C),plan=plan)).predict('Find Revenue','Revenue: 100'))
