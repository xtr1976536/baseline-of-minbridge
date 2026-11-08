import json

import pytest

from gbfr.query_constraints import table_structure_hints
from gbfr.types import Plan


def plan(scope,operator='counting',metric='Equipment and software'):
    return Plan.parse({'reasoning_type':'StatisticalAggregation','operator':operator,'precision':'unknown',
        'subgoals':[{'metric':metric,'constraints':{'temporal_scope':scope,'entity_scope':'Company',
            'meta':{'currency':'USD','scale':'thousand','unit':None}}}]})


@pytest.mark.parametrize('scope',['2018 and 2019','2017, 2018 and 2019','2017, 2018, and 2019'])
def test_plain_independent_year_enumerations_become_scalar_goals(scope):
    p=plan(scope)
    assert [g.constraints.temporal_scope for g in p.subgoals]==(['2018','2019'] if scope.startswith('2018') else ['2017','2018','2019'])
    assert all(g.constraints.entity_scope=='Company' and g.constraints.meta['scale']=='thousand' for g in p.subgoals)


@pytest.mark.parametrize('metric',['Change in payroll and benefits','Reported percentage change in revenue',
    'Cumulative total return','Annualized return','Price range','Duration of a loan'])
def test_multi_period_values_are_not_replaced_by_independent_annual_values(metric):
    p=plan('2019 and 2018','difference',metric)
    assert len(p.subgoals)==1 and p.subgoals[0].constraints.temporal_scope=='2019 and 2018'


@pytest.mark.parametrize('scope',['2018 to 2019','2018–2019','as of December 31, 2018; due within one year',
    'before December 2018; debt due 2019','2018 and thereafter'])
def test_ranges_and_compound_date_constraints_remain_intact(scope):
    p=plan(scope,'average','Debt payments')
    assert len(p.subgoals)==1 and p.subgoals[0].constraints.temporal_scope==scope


def test_nested_change_column_headers_keep_coordinates_and_period_pairs():
    doc='Compensation costs\n|  | Change between Fiscal |  |\n| --- | --- | --- |\n|  | 2019 and 2018 | 2018 and 2017 |\n| Payroll | (80) | 90 |'
    hint=table_structure_hints(doc)[0]
    assert hint['column_count']==3
    assert [(p['column_index'],p['text'],p['years']) for p in hint['period_columns']]==[
        (1,'2019 and 2018',['2019','2018']),(2,'2018 and 2017',['2018','2017'])]
    assert [r['text'] for r in hint['row_labels']]==['Payroll']
    assert '(80)' not in json.dumps(hint['header_rows'])
    for r in hint['header_rows']+hint['row_labels']:
        assert doc[slice(*r['span'])]==r['text']


def test_blank_subtotal_labels_never_become_an_amount_label():
    doc='|  | 2019 | 2018 |\n| --- | --- | --- |\n| Leasehold improvements | 3,522 | 3,157 |\n|  | 79,828 | 86,190 |'
    hint=table_structure_hints(doc)[0]
    assert len(hint['header_rows'])==1
    assert [r['text'] for r in hint['row_labels']]==['Leasehold improvements','']
    assert hint['row_labels'][1]['span'][0]==hint['row_labels'][1]['span'][1]
    assert '79,828' not in json.dumps(hint)


def test_section_labels_and_footnote_restrictions_remain_verbatim():
    doc='|  | 2019 | 2018 |\n| --- | --- | --- |\n| Retail net activations | 6,053 | 21,559 |\n| Satellite<sup>(1)</sup> | (85,423) | (89,231) |\n| Total retail subscribers | 2,772,464 | 2,766,411 |\n| Satellite | 1,005,282 | 1,090,705 |\n(1) Excludes wholesale subscribers.'
    h=table_structure_hints(doc)[0]
    assert [r['text'] for r in h['row_labels']]==['Retail net activations','Satellite<sup>(1)</sup>','Total retail subscribers','Satellite']
    assert h['footnotes'][0]['text']=='(1) Excludes wholesale subscribers.'
    assert doc[slice(*h['footnotes'][0]['span'])]==h['footnotes'][0]['text']


def test_unicode_and_escaped_pipes_do_not_move_columns_or_change_source():
    doc='说明\n| 指标 | 2024 | 2023 |\n| --- | --- | --- |\n| 收入\\|净额 | 20 | 10 |'
    h=table_structure_hints(doc)[0]
    assert h['column_count']==3 and h['row_labels'][0]['text']=='收入\\|净额'
    assert doc[slice(*h['row_labels'][0]['span'])]=='收入\\|净额'
    assert h['period_columns'][0]['column_index']==1


def test_auxiliary_limits_are_explicit_and_do_not_truncate_the_document():
    first='| Metric | 2024 |\n| --- | --- |\n'+''.join(f'| Metric {i} | {100+i} |\n' for i in range(20))
    doc=first+'\n| Other | 2023 |\n| --- | --- |\n| Data | 900 |'
    h=table_structure_hints(doc,max_tables=1,max_row_labels=2)
    assert len(h)==1 and len(h[0]['row_labels'])==2
    assert h[0]['source_body_row_count']==20 and h[0]['truncated']['row_labels']
    assert h[0]['following_tables_omitted']==1 and h[0]['source_table_count']==2
    assert 'Metric 19' in doc and '| Data | 900 |' in doc


def test_large_tables_have_a_bounded_optional_hint_with_a_truncation_marker():
    head='|  | '+ ' | '.join(f'Column {i} 2024' for i in range(40))+' |\n'
    sep='| --- | '+' | '.join('---' for _ in range(40))+' |\n'
    doc=head+sep+''.join('| '+('very long metric name '*20)+f' {i} | 123 |\n' for i in range(80))
    h=table_structure_hints(doc,max_hint_chars=2000)
    assert len(json.dumps(h,ensure_ascii=False))<=2000
    assert h[0]['hint_budget_truncated']
    assert h[0]['truncated']['row_labels'] or h[0]['truncated']['header_rows']
    for row in h[0]['header_rows']:
        assert doc[slice(*row['span'])]==row['text']


def test_pipe_prose_without_a_markdown_separator_is_not_invented_as_a_table():
    assert table_structure_hints('A | B | C\nNumbers: 1, 2, 3.')==[]
    with pytest.raises(ValueError):table_structure_hints('',max_row_labels=0)


def test_numeric_only_year_table_does_not_turn_its_first_amount_into_a_label():
    doc='Receivables from the money pool:\n| 2011 | 2010 | 2009 |\n| --- | --- | --- |\n| (In Thousands) |\n| $23,596 | $63,003 | $50,131 |'
    h=table_structure_hints(doc)[0]
    assert [p['column_index'] for p in h['period_columns']]==[0,1,2]
    assert h['row_labels'][0]['numeric_first_column']
    assert h['row_labels'][0]['text']==''
    assert '$23,596' not in json.dumps(h) and '$63,003' not in json.dumps(h)


def test_repeated_high_low_headers_retain_their_own_year_scopes():
    doc='| 2016 | High | Low |\n| --- | --- | --- |\n| Quarter ended March 31 | $102.93 | $83.07 |\n| 2015 | High | Low |\n| Quarter ended March 31 | $101.88 | $93.21 |'
    h=table_structure_hints(doc)[0]
    assert [g['period_label'] for g in h['period_groups']]==['2016','2015']
    assert h['period_groups'][0]['table_row_end_exclusive']==3
    assert h['period_groups'][1]['table_row_start']==4
    assert [r['text'] for r in h['row_labels']]==['Quarter ended March 31','Quarter ended March 31']
    assert h['header_rows'][1]['repeated_period_header']
    assert '$101.88' not in json.dumps(h)


def test_direct_retrieval_does_not_invent_a_sum_of_two_annual_values():
    p=Plan.parse({'reasoning_type':'DirectRetrieval','operator':'sum','precision':'unknown','subgoals':[
        {'metric':'Revenue','constraints':{'temporal_scope':'2018 and 2019','entity_scope':None,
            'meta':{'currency':None,'scale':None,'unit':None}}}]})
    assert len(p.subgoals)==1 and p.subgoals[0].constraints.temporal_scope=='2018 and 2019'


@pytest.mark.parametrize('metric',['Improvements','Leasehold improvements'])
def test_asset_improvements_are_not_a_cross_period_improvement_measure(metric):
    p=plan('2018 and 2019','counting',metric)
    assert [g.constraints.temporal_scope for g in p.subgoals]==['2018','2019']
    change=plan('2018 and 2019','difference','Operating ratio improvement')
    assert len(change.subgoals)==1 and change.subgoals[0].constraints.temporal_scope=='2018 and 2019'
