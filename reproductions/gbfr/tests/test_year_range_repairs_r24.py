"""Only independent annual aggregates expand a bare inclusive year interval."""
import asyncio
from dataclasses import asdict
import pytest
from gbfr.engine import GBFR
from gbfr.graph import MetricGraph
from gbfr.types import Constraints,Plan
from gbfr.query_constraints import expand_source_annual_aggregates,table_structure_hints
from .helpers import ScriptedClient

def plan(metric='Shares issued during the year',operator='sum',kind='ArithmeticCalculation',scope='2020 to 2022'):
    return {'reasoning_type':kind,'operator':operator,'precision':'unknown','subgoals':[
        {'metric':metric,'constraints':asdict(Constraints(scope,'Orion',{'currency':None,'scale':'ones','unit':'shares'}))}]}

@pytest.mark.parametrize('scope',['2020 to 2022','2020 through 2022','2020–2022'])
def test_annual_flow_aggregate_resolves_each_year_not_an_unreported_interval_total(scope):
    raw=plan(scope=scope);c=raw['subgoals'][0]['constraints'];metric=raw['subgoals'][0]['metric']
    class Client(ScriptedClient):
        async def complete(self,task,prompt):
            if task!='OPE.final':return await super().complete(task,prompt)
            self.calls.append((task,prompt))
            return 'def compute(vars):\n    return {"value": sum(vars.values()), "trace": {"output_meta":{"unit":"shares","scale":"ones","currency":None}}}'
    client=Client(c,{(metric,'2020'):(2,'| 2020 | 2 |'),
                            (metric,'2021'):(4,'| 2021 | 4 |'),
                            (metric,'2022'):(1,'| 2022 | 1 |')},plan=raw)
    result=asyncio.run(GBFR(MetricGraph([]),client,evidence_policy='paper').predict('How many shares were issued during 2020 to 2022?',
        'Orion.\n| Year | Shares issued during the year |\n| --- | --- |\n| 2020 | 2 |\n| 2021 | 4 |\n| 2022 | 1 |'))
    assert result.status=='answered' and result.value==7
    assert [p.data['var_list'][0]['constraints']['temporal_scope'] for t,p in client.calls if t=='OES']==['2020','2021','2022']

def test_average_of_annual_observations_is_expanded():
    parsed,events=expand_source_annual_aggregates(Plan.parse(plan(metric='Revenue',operator='average',kind='StatisticalAggregation')),
        table_structure_hints('| Year | Revenue |\n| --- | --- |\n| 2020 | 2 |\n| 2021 | 4 |\n| 2022 | 1 |'))
    assert [g.constraints.temporal_scope for g in parsed.subgoals]==['2020','2021','2022']
    assert events[0]['source_table_index']==0

@pytest.mark.parametrize('raw',[
    plan(metric='Cumulative return',kind='TemporalReasoning'),
    plan(metric='Annualized growth rate',operator='average'),
    plan(metric='Reported total issuances',kind='DirectRetrieval'),
    plan(metric='Borrowing',operator='change ratio',kind='ComparativeReasoning'),
    plan(scope='as of 2020; due through 2022'),
])
def test_cross_period_metrics_dates_and_direct_change_columns_are_not_expanded(raw):
    parsed,_=expand_source_annual_aggregates(Plan.parse(raw),
        table_structure_hints('| Year | Shares issued during the year |\n| --- | --- |\n| 2020 | 2 |\n| 2021 | 4 |\n| 2022 | 1 |'))
    assert len(parsed.subgoals)==1
    assert parsed.subgoals[0].constraints.temporal_scope==raw['subgoals'][0]['constraints']['temporal_scope']

def test_single_multi_year_column_and_absent_source_year_are_not_expanded():
    for context in ['| Measure | 2020 to 2022 |\n| --- | --- |\n| Shares issued | 7 |',
                    '| Year | Shares issued |\n| --- | --- |\n| 2020 | 2 |\n| 2022 | 1 |']:
        parsed,events=expand_source_annual_aggregates(Plan.parse(plan()),table_structure_hints(context))
        assert len(parsed.subgoals)==1 and not events
