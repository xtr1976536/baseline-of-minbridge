"""R22 offline operator contracts and source-scale dataflow regressions.

The client supplies fixed plans/programs: these tests verify operator wiring,
operand/metadata preservation and execution, not an LLM accuracy improvement.
No API, benchmark labels, answer-based replanning or output corrections.
"""
import asyncio
from dataclasses import asdict

import pytest

from gbfr.engine import GBFR
from gbfr.graph import MetricGraph
from gbfr.types import Constraints
from .helpers import ScriptedClient


def goal(metric, period=None, *, entity=None, scale=None, unit=None):
    return {'metric':metric,'constraints':asdict(Constraints(period,entity,
        {'currency':'$' if unit is None else None,'scale':scale,'unit':unit}))}


class Client(ScriptedClient):
    def __init__(self, subgoals, evidence, expression, output_meta, *,
                 operator='sum', reasoning='DirectRetrieval', observed=None):
        super().__init__(subgoals[0]['constraints'],evidence,
            plan={'reasoning_type':reasoning,'operator':operator,
                  'subgoals':subgoals,'precision':'unknown'})
        self.expression=expression
        self.output_meta=output_meta
        self.observed=observed

    async def json(self,task,prompt):
        result=await super().json(task,prompt)
        if task=='OES' and result['found'] and self.observed is not None:
            binding=result['var_bindings']['v1']
            binding['observed_meta']=dict(self.observed)
            binding['source_label']=binding['metric']
        return result

    async def complete(self,task,prompt):
        if task!='OPE.final':return await super().complete(task,prompt)
        self.calls.append((task,prompt))
        return ('def compute(vars):\n    return {"value": '+self.expression+
                ', "trace": {"source_values": vars, "output_meta": '+repr(self.output_meta)+
                ', "scale_explanation": "No scale conversion is supported when source scale is unknown."}}')


def run(client,question,context):
    return asyncio.run(GBFR(MetricGraph([]),client,evidence_policy='paper').predict(question,context))


def prompt(client,task):
    return next(p for t,p in client.calls if t==task)


MONEY={'currency':'USD','scale':None,'unit':None}
PERCENT={'currency':None,'scale':None,'unit':'percentage'}


def test_during_period_issuance_keeps_movement_and_rollforward_boundaries():
    gs=[goal('Debt issued during the year','2024')]
    c=Client(gs,{'Debt issued during the year':(12,'Debt issued during the year: 12')},
             'vars["v1"]',MONEY)
    p=run(c,'How much debt was issued during 2024?',
          '2024 rollforward. Beginning balance: 100. Debt issued during the year: 12. '
          'Repayments: 8. Ending balance: 104.')
    assert p.value==12
    oq=prompt(c,'OQA')
    assert 'Do not add successive ending balances' in oq.instructions
    assert 'a start-of-year balance is not the end-of-that-year balance' in oq.instructions
    assert 'Do not equate net movement with gross issuance' in oq.instructions
    assert prompt(c,'OES').data['var_list'][0]['metric']=='Debt issued during the year'


def test_explicit_average_of_balances_is_still_permitted():
    gs=[goal('Opening balance','beginning of 2024'),goal('Closing balance','end of 2024')]
    c=Client(gs,{'Opening balance':(100,'Opening balance: 100'),
                 'Closing balance':(104,'Closing balance: 104')},
             '(vars["v1"] + vars["v2"]) / 2',MONEY,
             operator='average',reasoning='StatisticalAggregation')
    p=run(c,'What was the average of the opening and closing balances for 2024?',
          'Opening balance: 100. Closing balance: 104.')
    assert p.value==102
    assert 'explicitly requested sum/average of balances is allowed' in prompt(c,'OQA').instructions
    assert [e['constraints']['temporal_scope'] for e in prompt(c,'OPE.final').data['evidences']]==[
        'beginning of 2024','end of 2024']


@pytest.mark.parametrize('requested,value,label',[
    ('Tax credit investment balance including unfunded commitments',80,
     'Tax credit investment balance including unfunded commitments'),
    ('Unfunded commitments included in tax credit investments',7,
     'Unfunded commitments included in tax credit investments'),
])
def test_local_antecedent_preserves_whole_versus_included_component(requested,value,label):
    gs=[goal(requested,'2024',entity='Orion; tax credit investments')]
    c=Client(gs,{requested:(value,f'{label}: {value}')},'vars["v1"]',MONEY)
    p=run(c,f'What was the {requested} in 2024?',
          'Orion 2024. Total equity investments: 120. Tax credit investments. '
          'Tax credit investment balance including unfunded commitments: 80. '
          'Unfunded commitments included in tax credit investments: 7.')
    assert p.value==value
    for task in ['OQA','OES','OPE.final']:
        instructions=prompt(c,task).instructions
        assert 'Do not add Total or broaden a category' in instructions
        assert 'nearest compatible antecedent' in instructions
        assert 'does not make the component a synonym for the whole balance' in instructions
    actual=prompt(c,'OES').data['var_list'][0]
    assert actual['metric']==requested
    assert actual['constraints']['entity_scope']=='Orion; tax credit investments'
    assert 'these balances' not in actual['metric']


def test_specific_note_rate_does_not_fill_a_different_instruments_missing_rate():
    gs=[goal('Interest rate for note B','2024',entity='Orion; note B',unit='percentage'),
        goal('Principal of note B','2024',entity='Orion; note B')]
    c=Client(gs,{'Interest rate for note A':(5,'Interest rate for note A: 5%'),
                 'Principal of note B':(100,'Principal of note B: 100')},
             'vars["v1"] * vars["v2"] / 100',MONEY,
             operator='product',reasoning='ArithmeticCalculation')
    p=run(c,'What annual interest applies to note B in 2024?',
          'Orion 2024. Interest rate for note A: 5%. Principal of note B: 100.')
    assert p.status=='abstained'
    assert not any(t=='OPE.final' for t,_ in c.calls)
    assert 'A rate for this note cannot be applied to all company debt' in prompt(c,'OQA').instructions
    assert all(p.data['var_list'][0]['constraints']['entity_scope']=='Orion; note B'
               for t,p in c.calls if t=='OES')


@pytest.mark.parametrize('operator,expression,expected',[
    ('difference','(vars["v3"] / vars["v4"] - vars["v1"] / vars["v2"]) * 100',10),
    ('change ratio','((vars["v3"] / vars["v4"]) - (vars["v1"] / vars["v2"])) / (vars["v1"] / vars["v2"]) * 100',20),
])
def test_ratio_difference_and_relative_growth_remain_distinct(operator,expression,expected):
    gs=[goal('Net amount','2023'),goal('Base amount','2023'),
        goal('Net amount','2024'),goal('Base amount','2024')]
    ev={('Net amount','2023'):(20,'Net amount: 20'),('Base amount','2023'):(40,'Base amount: 40'),
        ('Net amount','2024'):(30,'Net amount: 30'),('Base amount','2024'):(50,'Base amount: 50')}
    c=Client(gs,ev,expression,PERCENT,operator=operator,reasoning='ComparativeReasoning')
    query=('What is the difference in percentage points between the two net-to-base percentages?'
           if operator=='difference' else 'What is the relative percentage growth of the net-to-base ratio?')
    p=run(c,query,'2023: Net amount: 20. Base amount: 40. 2024: Net amount: 30. Base amount: 50.')
    assert p.value==pytest.approx(expected)
    for task in ['OQA','OPE.final']:
        assert 'subtract in percentage-point units' in prompt(c,task).instructions
        assert 'relative change of a ratio' in prompt(c,task).instructions
    assert prompt(c,'OPE.final').data['operator']==operator


@pytest.mark.parametrize('query,operator,expression,expected',[
    ('What is the difference between category A and category B?',
     'difference','abs(vars["v1"] - vars["v2"])',5),
    ('What is category A minus category B?',
     'difference','vars["v1"] - vars["v2"]',-5),
    ('What is the signed change from old to new?',
     'difference','vars["v1"] - vars["v2"]',-5),
    ('What is the relative change from a negative old base to the new value?',
     'change ratio','(vars["v1"] - vars["v2"]) / vars["v2"] * 100',-125),
])
def test_symmetric_gaps_do_not_erase_explicit_direction_or_signed_base(query,operator,expression,expected):
    values=(5,-20) if operator=='change ratio' else (5,10)
    c=Client([goal('A'),goal('B')],{'A':(values[0],f'A: {values[0]}'),
             'B':(values[1],f'B: {values[1]}')},expression,
             PERCENT if operator=='change ratio' else MONEY,
             operator=operator,reasoning='ComparativeReasoning')
    p=run(c,query,f'A: {values[0]}. B: {values[1]}.')
    assert p.value==expected
    instructions=prompt(c,'OPE.final').instructions
    assert 'with no direction and no temporal-change meaning' in instructions
    assert 'Never apply absolute value to every difference' in instructions
    assert 'preserving the signed base; never abs(old)' in instructions


def test_contra_asset_sign_is_not_automatically_replaced_by_its_magnitude():
    c=Client([goal('Net assets','2024'),goal('Accumulated depreciation','2024')],
             {'Net assets':(10,'Net assets: 10'),
              'Accumulated depreciation':(-20,'Accumulated depreciation: (20)')},
             'vars["v1"] / vars["v2"] * 100',PERCENT,
             operator='ratio',reasoning='ComparativeReasoning')
    p=run(c,'What is the signed ratio of net assets to accumulated depreciation in 2024?',
          '2024. Net assets: 10. Accumulated depreciation: (20).')
    assert p.value==-50
    assert 'Do not automatically take the magnitude of a contra-asset' in prompt(c,'OQA').instructions


@pytest.mark.parametrize('label,value,question',[
    ('Reported decrease magnitude',7,'By how much did the amount decrease?'),
    ('Reported signed change',-7,'What was the reported signed change?'),
])
def test_direct_retrieval_keeps_reported_decrease_or_signed_change(label,value,question):
    c=Client([goal(label)],{label:(value,f'{label}: {value}')},'vars["v1"]',MONEY)
    p=run(c,question,f'{label}: {value}.')
    assert p.value==value
    final=prompt(c,'OPE.final')
    assert len(final.data['evidences'])==1
    assert 'return the one resolved reported scalar without arithmetic or a sign change' in final.instructions
    assert 'reported decrease magnitude of 7; do not negate it' in final.instructions
    assert 'For a computed non-DirectRetrieval difference' in final.instructions


@pytest.mark.parametrize('source_scale,raw,expression,output_scale,expected',[
    (None,12500,'vars["v1"]',None,12500),
    ('unknown',12500,'vars["v1"]',None,12500),
    ('thousand',12500,'vars["v1"] / 1000','million',12.5),
    ('ones',1250000,'vars["v1"] / 1000000','million',1.25),
])
def test_requested_millions_cannot_supply_an_unknown_source_scale(source_scale,raw,expression,output_scale,expected):
    c=Client([goal('Revenue',scale='million')],{'Revenue':(raw,f'Revenue: ${raw}')},
             expression,{'currency':'USD','scale':output_scale,'unit':None},
             observed={'currency':'$','scale':source_scale,'unit':None})
    source_decl='' if source_scale in {None,'unknown'} else f'Source amounts explicitly in {source_scale}. '
    p=run(c,'What is revenue in millions?',source_decl+f'Revenue: ${raw}.')
    assert p.value==expected and p.meta['scale']==output_scale
    es=prompt(c,'OPE.final').data['evidences']
    assert es[0]['value']==raw
    effective=None if source_scale in {None,'unknown'} else source_scale
    assert es[0]['meta']['scale']==effective
    assert es[0]['paths'][0]['evidence']['v1']['value']==raw
    resolution=es[0]['paths'][0]['source_scale_resolution']
    assert resolution=={'requested_scale':'million','observed_scale':effective,'effective_scale':effective,
        'rule':'Observed source scale takes precedence; unknown is not ones or a requested display scale.'}
    for task in ['OQA','OES','OPE.final']:
        assert 'unknown source reporting scale is not ones/base units' in prompt(c,task).instructions
    execution=next(e['execution'] for e in p.trace['events'] if e['operator']=='OPE.final')
    assert execution['trace']['source_values']['v1']==raw
    if effective is None:
        assert 'source scale is unknown' in execution['trace']['scale_explanation']


def test_missing_legacy_observed_metadata_is_not_reinterpreted_as_a_new_scale_claim():
    c=Client([goal('Revenue',scale='thousand')],{'Revenue':(50,'Revenue: 50')},
             'vars["v1"]',{'currency':'USD','scale':'thousand','unit':None})
    p=run(c,'What revenue is reported?','Amounts in thousands. Revenue: 50.')
    assert p.meta['scale']=='thousand'
    path=p.trace['evidence'][0]['paths'][0]
    assert 'source_scale_resolution' not in path
    assert path['meta']['scale']=='thousand'
