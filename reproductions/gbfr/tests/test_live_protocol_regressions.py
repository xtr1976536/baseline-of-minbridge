"""Issues observed with the first real service responses; no network in tests."""
import asyncio
import json
import pytest

from gbfr.engine import grounded,verbatim_spans
from gbfr.graph import Metric,MetricGraph
from gbfr.types import Constraints,Goal,ProtocolError
from gbfr.engine import GBFR,metric_hints
from gbfr.graph import Formula,Operand
from .helpers import ScriptedClient


def test_lowercase_canonical_name_wins_over_another_nodes_broad_alias():
    g=MetricGraph([Metric('Stock Price',[], '', 'atomic',[]),
                   Metric('Next Period Stock Price',['Stock Price'],'','atomic',[])])
    assert g.find('stock price').name=='Stock Price'
    assert g.find('next period stock price').name=='Next Period Stock Price'


def test_paper_primary_synonym_wins_over_a_qualified_nodes_soft_alias():
    g=MetricGraph([Metric('Net Income',['Net Profit'], '', 'atomic',[],['Net Profit']),
                   Metric('Adjusted Net Income',['Net Profit'],'','atomic',[])])
    assert g.find('net profit').name=='Net Income'


def test_query_name_hints_prefer_whole_qualified_metrics_and_canonical_spelling():
    g=MetricGraph([Metric('Stock Price',[],'','atomic',[]),
        Metric('Next Period Stock Price',[],'','atomic',[]),Metric('Net Income',['Net Profit'],'','atomic',[],['Net Profit'])])
    hints=metric_hints(g,'Compare Next Period Stock Price and Net Profit')
    assert [h['canonical_metric'] for h in hints]==['Next Period Stock Price','Net Income']


def test_query_hints_do_not_replace_fiscal_revenue_with_unqualified_revenue():
    graph=MetricGraph([Metric('Revenue',[],'','atomic',[])])
    assert metric_hints(graph,"What is Company A's Fiscal Revenue for 2024?")==[]
    assert metric_hints(graph,'What is Revenue for 2024?')[0]['canonical_metric']=='Revenue'


def test_separately_quoted_header_and_labelled_row_are_each_verbatim():
    context='All amounts are USD millions. Net Profit 2024: 500. Total Equity 2023: 2200.'
    snippet='All amounts are USD millions. Total Equity 2023: 2200.'
    spans=verbatim_spans(snippet,context)
    assert len(spans)==2 and all(span in context for span in spans)
    c=Constraints('2023','A',{'currency':'USD','scale':'million','unit':None})
    goal=Goal('Total Equity',c)
    binding={'metric':goal.metric,'constraints':{'temporal_scope':'2023','entity_scope':'A','meta':c.meta},
             'value':2200,'context':snippet,'confidence':1}
    assert grounded(binding,goal,context,[])==2200
    binding['context']='All amounts are USD millions. Total Equity 2023: 2200 invented.'
    with pytest.raises(ProtocolError):
        grounded(binding,goal,context,[])


def test_disjoint_header_cannot_supply_an_unlabelled_numeric_value():
    context='Revenue is not reported. An unrelated amount is 100. End of document.'
    c=Constraints('2024','A',{'currency':None,'scale':None,'unit':None})
    binding={'metric':'Revenue','constraints':{'temporal_scope':'2024','entity_scope':'A','meta':c.meta},
             'value':100,'context':'Revenue is not reported. An unrelated amount is 100.','confidence':1}
    # Force a disjoint quotation; even though both sentences are real, the number
    # belongs to an unrelated sentence and cannot ground Revenue.
    context='Revenue is not reported. Middle sentence omitted. An unrelated amount is 100.'
    with pytest.raises(ProtocolError,match='unquoted'):
        grounded(binding,Goal('Revenue',c),context,[])


def test_recursive_verifier_judges_the_current_metric_not_the_final_question():
    c={'temporal_scope':'2024','entity_scope':'A','meta':{'currency':None,'scale':None,'unit':None}}
    graph=MetricGraph([Metric('Leaf',[],'','atomic',[]),
        Metric('Intermediate',[],'','derived',[Formula('mid','Intermediate','x+1',[Operand('x','Leaf')],'Intermediate = Leaf + 1')]),
        Metric('Target',[],'','derived',[Formula('target','Target','2*x',[Operand('x','Intermediate')],'Target = 2 * Intermediate')])])
    plan={'reasoning_type':'ArithmeticCalculation','operator':'sum','precision':'unknown','subgoals':[{'metric':'Target','constraints':c}]}
    class LocalJudge(ScriptedClient):
        async def json(self,task,prompt):
            if task!='Verify':
                return await super().json(task,prompt)
            paths=json.loads(prompt.rsplit('Candidate paths:\n',1)[1])
            question=prompt.split('Question:',1)[1].split('Original question for background only:',1)[0]
            return {'path_decisions':[{'path_id':p['path_id'],
                'decision':'VALID' if ('"metric": "'+p['goal']['metric']+'"') in question else 'INVALID',
                'justification':'Judge the current intermediate quantity rather than requiring it to answer Target.'} for p in paths]}
    client=LocalJudge(c,{'Leaf':(10,'Leaf: 10')},plan=plan)
    result=asyncio.run(GBFR(graph,client).predict('Compute Target','Leaf: 10'))
    assert result.status=='answered' and result.value==22


@pytest.mark.parametrize('decision,expected',[('VALID','answered'),('INVALID','abstained')])
def test_single_candidate_missing_id_does_not_change_the_verifier_decision(graph,constraints,decision,expected):
    class NoId(ScriptedClient):
        async def json(self,task,prompt):
            r=await super().json(task,prompt)
            if task=='Verify':
                for d in r['path_decisions']:
                    d['path_id']=None;d['decision']=decision
            return r
    client=NoId(constraints,{'Revenue':(100,'Revenue: 100'),'Cost':(60,'Cost: 60')})
    p=asyncio.run(GBFR(graph,client).predict('Find gross profit','Revenue: 100; Cost: 60'))
    assert p.status==expected


def test_missing_ids_with_multiple_candidates_are_not_guessed(graph,constraints):
    class NoId(ScriptedClient):
        async def json(self,task,prompt):
            r=await super().json(task,prompt)
            if task=='Verify':
                for d in r['path_decisions']:d['path_id']=None
            return r
    client=NoId(constraints,{'Revenue':(100,'Revenue: 100'),'Cost':(60,'Cost: 60'),
                             'Profit Margin':(.4,'Profit Margin: 0.4')})
    with pytest.raises(ProtocolError,match='verification decision'):
        asyncio.run(GBFR(graph,client).predict('Find gross profit','Revenue: 100; Cost: 60; Profit Margin: 0.4'))


def test_registered_alias_proof_is_forwarded_to_recursive_path_verification(graph,constraints):
    class AliasJudge(ScriptedClient):
        async def json(self,task,prompt):
            result=await super().json(task,prompt)
            if task=='Verify':
                paths=json.loads(prompt.rsplit('Candidate paths:\n',1)[1])
                for d,p in zip(result['path_decisions'],paths):
                    evidence=[direct for branches in p['evidence'].values() for direct in branches]
                    supported=any('Net Sales' in direct.get('alias_mapping',{}).get('matched_registered_aliases',[]) for direct in evidence)
                    d['decision']='VALID' if supported else 'INVALID'
            return result
    client=AliasJudge(constraints,{'Revenue':(100,'Net Sales: 100'),'Cost':(60,'Cost: 60')})
    p=asyncio.run(GBFR(graph,client).predict('Compute gross profit','Net Sales: 100; Cost: 60'))
    assert p.status=='answered' and p.value==40
