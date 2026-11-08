"""Protocol regressions for lost request labels and structural table hints.

The scripted client tests wiring/constraints only, not language-model accuracy.
"""
import asyncio
from dataclasses import asdict

from gbfr.engine import GBFR
from gbfr.graph import Formula,Metric,MetricGraph,Operand
from gbfr.types import Constraints
from .helpers import ScriptedClient


def constraints(year='2024',unit=None):
    return asdict(Constraints(year,None,{'currency':None,'scale':None,'unit':unit}))


def plan(metrics,c,operator='sum'):
    return {'reasoning_type':'DirectRetrieval' if len(metrics)==1 else 'ArithmeticCalculation',
        'operator':operator,'subgoals':[{'metric':m,'constraints':c} for m in metrics],'precision':'unknown'}


def receivable_graph():
    # Deliberately broad registered aliases reproduce the former engine-level
    # information loss; the Evidence Finder must still see the exact request.
    return MetricGraph([Metric('Accounts Receivable',['Trade receivables','Trade receivables, net'],
        'A broad receivable accounting concept.','atomic',[])])


def test_original_requested_row_survives_optional_graph_canonical_name():
    c=constraints();client=ScriptedClient(c,{'Trade receivables':(30,'Trade receivables: 30')},plan=plan(['Trade receivables'],c))
    p=asyncio.run(GBFR(receivable_graph(),client).predict('What were trade receivables in 2024?',
        '2024. Trade receivables: 30. Trade receivables, net: 27.'))
    assert p.status=='answered' and p.value==30
    prompt=next(prompt for task,prompt in client.calls if task=='OES');var=prompt.data['var_list'][0]
    assert var['metric']=='Trade receivables'
    assert var['graph_metric_hint']['canonical_metric']=='Accounts Receivable'
    assert var['definition']==''
    path=p.trace['evidence'][0]['paths'][0]
    assert path['alias_mapping']['requested_metric']=='Trade receivables'
    assert path['alias_mapping']['canonical_metric']=='Accounts Receivable'


def test_two_requested_measures_do_not_share_one_broad_alias_cache_entry():
    c=constraints();client=ScriptedClient(c,{'Trade receivables':(30,'Trade receivables: 30'),
        'Trade receivables, net':(27,'Trade receivables, net: 27')},plan=plan(['Trade receivables','Trade receivables, net'],c,'difference'))
    p=asyncio.run(GBFR(receivable_graph(),client).predict('How much was the allowance in 2024?',
        '2024. Trade receivables: 30. Trade receivables, net: 27.'))
    assert p.status=='answered' and p.value==3
    assert [prompt.data['var_list'][0]['metric'] for task,prompt in client.calls if task=='OES']==['Trade receivables','Trade receivables, net']


def test_net_only_source_does_not_satisfy_a_missing_requested_gross_row():
    c=constraints();client=ScriptedClient(c,{'Trade receivables, net':(27,'Trade receivables, net: 27')},plan=plan(['Trade receivables'],c))
    p=asyncio.run(GBFR(receivable_graph(),client).predict('What were trade receivables before the allowance in 2024?',
        '2024. Only Trade receivables, net: 27 is reported.'))
    assert p.status=='abstained'
    assert not any(t=='OPE.final' for t,_ in client.calls)


def test_source_category_label_does_not_become_a_graph_gain_metric():
    c=constraints();g=MetricGraph([Metric('Fair Value Change Gains/Losses',['FVPL'],'A gain or loss for a period.','atomic',[])])
    client=ScriptedClient(c,{'FVPL':(40,'FVPL: 40')},plan=plan(['FVPL'],c))
    p=asyncio.run(GBFR(g,client).predict('What was the level-one FVPL balance in 2024?',
        'Financial instruments at fair value, level one, 2024. FVPL: 40.'))
    assert p.status=='answered' and p.value==40
    prompt=next(prompt for t,prompt in client.calls if t=='OES')
    assert prompt.data['var_list'][0]['metric']=='FVPL'
    assert prompt.data['var_list'][0]['definition']==''


def test_graph_formula_and_single_verifier_keep_the_original_requested_alias():
    c=constraints();g=MetricGraph([Metric('Revenue',[],'','atomic',[]),Metric('Cost',[],'','atomic',[]),
        Metric('Gross Profit',['Gross earnings'],'','derived',[
            Formula('gp','Gross Profit','r-c',[Operand('r','Revenue'),Operand('c','Cost')],'Gross Profit = Revenue - Cost')])])
    client=ScriptedClient(c,{'Revenue':(80,'Revenue: 80'),'Cost':(30,'Cost: 30')},plan=plan(['Gross earnings'],c))
    p=asyncio.run(GBFR(g,client).predict('Find Gross earnings for 2024.','2024. Revenue: 80. Cost: 30.'))
    assert p.status=='answered' and p.value==50
    verify=[prompt for task,prompt in client.calls if task=='Verify']
    assert len(verify)==1
    assert verify[0].data['query']['current_metric_subgoal']['metric']=='Gross earnings'
    assert verify[0].data['candidate_paths'][0]['computation']['graph_target']=='Gross Profit'
    assert 'registered graph alias alone does not justify' in verify[0].instructions


def test_qualified_index_unit_gets_series_rules_and_is_not_relabelled_as_share_price():
    c=constraints(unit='investment performance index value')
    client=ScriptedClient(c,{'Orion Fund':(125,'Orion Fund: 125')},plan=plan(['Orion Fund'],c))
    p=asyncio.run(GBFR(MetricGraph([]),client).predict('What is the Orion Fund series level in 2024?',
        '2024. Orion Fund: 125. Levels assume reinvestment of dividends.'))
    assert p.status=='answered' and p.value==125
    prompt=next(prompt for t,prompt in client.calls if t=='OES')
    assert 'cumulative-total-return or wealth table' in prompt.instructions
    assert 'never turns a total-return level into an actual share price' in prompt.instructions
    assert prompt.data['var_list'][0]['constraints']['meta']['unit']=='investment performance index value'


def test_missing_actual_price_is_not_filled_from_a_total_return_level():
    c=constraints(unit='currency/share')
    client=ScriptedClient(c,{'Orion Fund':(125,'Orion Fund: 125')},plan=plan(['Actual share price'],c))
    p=asyncio.run(GBFR(MetricGraph([]),client).predict('What was the actual share price in 2024?',
        '2024. Orion Fund: 125. This is a total-return wealth level with reinvested dividends.'))
    assert p.status=='abstained'
    prompt=next(prompt for t,prompt in client.calls if t=='OES')
    assert 'cumulative-total-return or wealth table' not in prompt.instructions


def test_structural_table_hints_reach_both_operators_without_splitting_a_change_column():
    c=constraints('2019 and 2018','percentage')
    doc='| Measure | 2019 and 2018 |\n| --- | --- |\n| Change | 7% |'
    client=ScriptedClient(c,{'Change':(7,'| Change | 7% |')},plan=plan(['Change'],c))
    p=asyncio.run(GBFR(MetricGraph([]),client).predict('What was the reported change for 2019 and 2018?',doc))
    assert p.status=='answered' and p.value==7
    calls=[(task,prompt) for task,prompt in client.calls if task in {'OQA','OES'}]
    assert len([task for task,_ in calls if task=='OES'])==1
    assert all(prompt.data['source_table_hints'] for _,prompt in calls)
    assert calls[0][1].data['source_table_hints']==calls[1][1].data['source_table_hints']
    assert 'two years can name one change/comparison column' in calls[0][1].instructions
    assert calls[1][1].data['var_list'][0]['constraints']['temporal_scope']=='2019 and 2018'


def test_cross_period_category_counting_groups_objects_after_year_expansion():
    c=constraints('2018 and 2019')
    p={'reasoning_type':'StatisticalAggregation','operator':'counting',
       'subgoals':[{'metric':m,'constraints':c} for m in ['Equipment','Improvements']],'precision':'unknown'}
    evidence={('Equipment','2018'):(10,'Equipment 2018: 10'),('Equipment','2019'):(12,'Equipment 2019: 12'),
              ('Improvements','2018'):(5,'Improvements 2018: 5'),('Improvements','2019'):(6,'Improvements 2019: 6')}
    class Client(ScriptedClient):
        async def complete(self,task,prompt):
            if task!='OPE.final':return await super().complete(task,prompt)
            es=prompt.data['evidences'];assert len(es)==4
            grouped={}
            for e in es:grouped.setdefault(e['metric'],[]).append(e['var_name'])
            assert sorted(len(keys) for keys in grouped.values())==[2,2]
            expressions=['['+', '.join('vars['+repr(key)+']' for key in keys)+']' for keys in grouped.values()]
            return 'def compute(vars):\n    groups = ['+', '.join(expressions)+']\n    return {"value": len(groups), "trace": {"groups": groups, "output_meta": {"unit":"count","currency":None,"scale":None}}}'
    client=Client(c,evidence,plan=p)
    doc='Equipment 2018: 10. Equipment 2019: 12. Improvements 2018: 5. Improvements 2019: 6.'
    r=asyncio.run(GBFR(MetricGraph([]),client).predict('How many equipment categories are reported in both 2018 and 2019?',doc))
    assert r.status=='answered' and r.value==2
    assert sum(t=='OES' for t,_ in client.calls)==4


def test_counted_periods_remain_distinct_when_the_metric_name_is_shared():
    c=constraints();p={'reasoning_type':'StatisticalAggregation','operator':'counting','precision':'unknown',
       'subgoals':[{'metric':'Revenue','constraints':constraints(period)} for period in ['Q1 2024','Q2 2024','Q3 2024']]}
    class Client(ScriptedClient):
        async def complete(self,task,prompt):
            if task!='OPE.final':return await super().complete(task,prompt)
            es=prompt.data['evidences'];assert len(es)==3
            assert len({e['constraints']['temporal_scope'] for e in es})==3
            return 'def compute(vars):\n    return {"value": sum(1 for x in vars.values() if x > 10), "trace": {"output_meta":{"unit":"count","currency":None,"scale":None}}}'
    ev={('Revenue','Q1 2024'):(12,'Q1 2024 Revenue: 12'),('Revenue','Q2 2024'):(9,'Q2 2024 Revenue: 9'),('Revenue','Q3 2024'):(15,'Q3 2024 Revenue: 15')}
    client=Client(c,ev,plan=p)
    r=asyncio.run(GBFR(MetricGraph([]),client).predict('How many quarters had Revenue greater than 10 in 2024?',
        'Q1 2024 Revenue: 12. Q2 2024 Revenue: 9. Q3 2024 Revenue: 15.'))
    assert r.status=='answered' and r.value==2
