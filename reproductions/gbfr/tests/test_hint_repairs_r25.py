"""Conservative OQA name recommendations; never change graph or OES goals.

These are offline protocol/phrase-boundary tests, not language-model accuracy
results. Generic examples do not use benchmark answers or the new live subset.
"""
import asyncio
from copy import deepcopy
from dataclasses import asdict

import pytest

from gbfr.engine import GBFR,metric_hints
from gbfr.graph import Metric,MetricGraph
from gbfr.types import Constraints
from .helpers import ScriptedClient


def graph(*entries):
    return MetricGraph([Metric(name,aliases,'Definition of '+name,'atomic',[])
                        for name,aliases in entries])


def names(g,q):
    return [h['canonical_metric'] for h in metric_hints(g,q)]


@pytest.mark.parametrize('word',['change','total','term','average','ratio','value','rate','sum'])
def test_generic_task_words_do_not_suggest_a_financial_graph_meaning(word):
    g=graph(('Unrelated specialized measure',[word]))
    assert names(g,'What is the '+word+'?')==[]
    # The scope is only OQA recommendations. The registered graph entry stays.
    assert g.find(word).name=='Unrelated specialized measure'


@pytest.mark.parametrize('alias,query',[
    ('equity','What was the value of equity investments?'),
    ('common stock','What is the proportion of common stock outstanding?'),
    ('borrowing','What was borrowing under the loan facility?'),
    ('revenue','What was revenue attributable to the parent?'),
    ('revenue','What was revenue per employee?'),
    ('profit','What was gross-profit?'),
    ('revenue','What was revenue-adjusted income?'),
])
def test_a_metric_fragment_does_not_replace_a_more_specific_phrase(alias,query):
    g=graph(('Broad canonical measure',[alias]))
    assert names(g,query)==[]
    assert g.find(alias).name=='Broad canonical measure'


def test_left_qualifiers_remain_protected_and_complete_names_can_be_recommended():
    g=graph(('Revenue',[]),('Adjusted revenue',[]))
    assert names(g,'What is adjusted revenue in 2024?')==['Adjusted revenue']
    assert names(graph(('Revenue',[])),'What is adjusted revenue in 2024?')==[]


@pytest.mark.parametrize('phrase',[
    "shareholders' equity",'shareholders’ equity',
    'total asset turnover','return on equity','net income attributable to parent',
    'fulfillment reserve','common stock outstanding','revenue per employee',
])
def test_complete_registered_multiword_measures_survive_without_a_financial_whitelist(phrase):
    g=graph((phrase.title(),[]),('Equity',[]),('Revenue',[]),('Common stock',[]))
    assert names(g,'What is '+phrase+' in 2024?')==[phrase.title()]


@pytest.mark.parametrize('phrase',[
    "shareholders' equity",'shareholders’ equity',
])
def test_a_registered_complete_possessive_alias_still_recommends_its_canonical_metric(phrase):
    g=graph(('Equity',[phrase]))
    assert names(g,'What is '+phrase+'?')==['Equity']


def test_longer_registered_alias_wins_over_its_shorter_word():
    g=graph(('Equity',[]),('Equity investment balance',['equity investments']))
    assert names(g,'What was the change in equity investments?')==['Equity investment balance']
    assert names(g,'What was equity?')==['Equity']


@pytest.mark.parametrize('alias,query',[
    ('debt','What was the debtor count?'),
    ('equity','What is the inequity measure?'),
    ('cost','What was the costliest item?'),
])
def test_alias_substrings_inside_longer_words_do_not_recommend_metrics(alias,query):
    assert names(graph((alias.title(),[])),query)==[]


def test_complete_short_measure_and_registered_abbreviations_are_retained():
    g=graph(('Debt',[]),('Return on Equity',['ROE']),('Earnings per Share',['EPS']),('Tax',[]))
    assert names(g,'What is debt in 2024?')==['Debt']
    assert names(g,'What is roe?')==['Return on Equity']
    assert names(g,'What is EPS?')==['Earnings per Share']
    assert names(g,'What is tax?')==[]  # Conservative optional-hint recall.
    assert g.find('tax').name=='Tax'


def test_two_complete_measure_names_are_retained_across_arithmetic_language():
    g=graph(('Revenue',[]),('Cost',[]))
    assert names(g,'What is the difference between revenue and cost?')==['Revenue','Cost']


def test_a_complete_price_return_name_keeps_its_following_investment_relation():
    g=graph(('100',[]),('Price Return',[]))
    assert names(g,'What is the Price Return on $100,000?')==['Price Return']
    assert names(g,'What is the Price Return on the investment?')==['Price Return']


def test_filtering_hints_cannot_rewrite_an_accepted_oq_a_plan_or_original_oes_goal():
    g=graph(('Equity',[]),('Net Change',['change']))
    before={n:(list(m.aliases),list(m.primary_aliases)) for n,m in g.nodes.items()}
    c=asdict(Constraints('2024',None,{'currency':None,'scale':None,'unit':None}))
    plan={'reasoning_type':'DirectRetrieval','operator':'sum','precision':'unknown',
          'subgoals':[{'metric':'Equity investments','constraints':c}]}
    original_plan=deepcopy(plan)
    client=ScriptedClient(c,{'Equity investments':(30,'Equity investments: 30')},plan=plan)
    prediction=asyncio.run(GBFR(g,client).predict('What were equity investments in 2024?',
                                               '2024. Equity investments: 30.'))
    assert prediction.status=='answered' and prediction.value==30
    oq=next(p for task,p in client.calls if task=='OQA')
    assert oq.data['canonical_metric_hints']==[]
    assert next(p for task,p in client.calls if task=='OES').data['var_list'][0]['metric']=='Equity investments'
    assert client.plan==original_plan
    assert {n:(list(m.aliases),list(m.primary_aliases)) for n,m in g.nodes.items()}==before


def test_an_unreported_outstanding_measure_is_not_filled_by_an_authorized_measure():
    g=graph(('Authorized shares',['shares']))
    c=asdict(Constraints('2024',None,{'currency':None,'scale':'ones','unit':'shares'}))
    p={'reasoning_type':'DirectRetrieval','operator':'sum','precision':'unknown',
       'subgoals':[{'metric':'Shares outstanding','constraints':c}]}
    client=ScriptedClient(c,{'Authorized shares':(100,'Authorized shares: 100')},plan=p)
    prediction=asyncio.run(GBFR(g,client).predict('What were shares outstanding in 2024?',
                                               '2024. Authorized shares: 100.'))
    assert prediction.status=='abstained'
    assert not any(task=='OPE.final' for task,_ in client.calls)
    assert next(pr for task,pr in client.calls if task=='OQA').data['canonical_metric_hints']==[]
    assert next(pr for task,pr in client.calls if task=='OES').data['var_list'][0]['metric']=='Shares outstanding'
