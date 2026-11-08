import asyncio
import json
from dataclasses import asdict
from decimal import Decimal
import pytest

from gbfr.engine import grounded
from gbfr.executor import execute,validate_program
from gbfr.graph import Formula,Metric,MetricGraph,Operand
from gbfr.metrics import correct
from gbfr.types import Constraints,Goal,Plan,ProtocolError
from gbfr.units import normalize_meta


def test_output_scale_comes_from_question_not_from_prediction():
    sample={'answer':'704.25','answer_meta':{},'question':'Average revenue in millions','context':'','unanswerable':False}
    def p(value,scale,currency='USD'):
        return {'status':'answered','value':value,'meta':{'currency':currency,'scale':scale,'unit':'currency'}}
    assert correct(p(704.25,'millions'),sample)
    assert correct(p(704250000,'ones'),sample)
    assert correct({'status':'answered','value':704.25,'meta':{}},sample)
    assert not correct(p(704.25,'thousands'),sample)
    sample['context']='All amounts in USD millions.'
    assert not correct(p(704.25,'millions','CNY'),sample)


def test_document_units_supply_defaults_but_do_not_overwrite_gold_display_units():
    sample={'answer':94,'answer_meta':{},'question':'What was net revenue?',
            'context':'Amounts in USD millions. Net revenue: 94.','unanswerable':False}
    assert correct({'status':'answered','value':94000000,'meta':{'scale':'ones','currency':'USD'}},sample)
    sample.update(answer_meta={'scale':'million'},context='All amounts in USD thousands. Net revenue: 94.')
    # The official reference's display scale can differ from the input table.
    # A document declaration cannot replace that explicit target contract.
    assert not correct({'status':'answered','value':94,'meta':{'scale':'thousands','currency':'USD'}},sample)
    assert correct({'status':'answered','value':94,'meta':{'scale':'millions','currency':'USD'}},sample)


def test_no_unknown_unit_factor_search_or_currency_conversion():
    s={'answer':2,'question':'Compute the value','unanswerable':False}
    # Raw numeric agreement does not establish a physical million multiplier
    # when the target display scale has no source-backed declaration.
    assert not correct({'status':'answered','value':2,'meta':{'scale':'million'}},s)
    assert correct({'status':'answered','value':2,'meta':{}},s)
    assert correct({'status':'answered','value':2,'meta':{'unit':'ratio'}},s)
    assert correct({'status':'answered','value':2,'meta':{'scale':'million'}},
                   {**s,'question':'Compute the value in millions'})
    assert not correct({'status':'answered','value':2000000,'meta':{'scale':'ones'}},s)
    s.update(answer='$2')
    assert not correct({'status':'answered','value':2,'meta':{'scale':'million'}},s)


@pytest.mark.parametrize('raw,scale,unit',[
    ({'scale':'in thousands'},'thousand',None),
    ({'scale':"$'000"},'thousand',None),
    ({'scale':'shares','unit':'shares'},None,'shares'),
    ({'scale':'per share','unit':'price'},None,'currency/share'),
    ({'scale':'thousands of barrels per day'},'thousand','barrels/day'),
    ({'scale':'lakh'},'lakh',None),
])
def test_real_reporting_formats_preserve_magnitude_and_dimension(raw,scale,unit):
    actual=normalize_meta(raw)
    assert actual['scale']==scale and actual['unit']==unit


def test_paper_tuple_subgoals_and_integer_precision_are_representation_only():
    c={'temporal_scope':'2024','entity_scope':'A','meta':{'currency':None,'scale':'shares','unit':'shares'}}
    p=Plan.parse({'reasoning_type':'Arithmetic Calculation','operator':'division','subgoals':[['Shares',c]],'precision':2})
    assert p.subgoals[0].metric=='Shares' and p.subgoals[0].constraints.meta['scale'] is None
    assert p.precision=='2 decimal places'
    with pytest.raises(ProtocolError):Plan.parse({'reasoning_type':'DirectRetrieval','operator':'sum','subgoals':[],'precision':'unknown'})


def test_enumerated_periods_are_separate_scalar_goals_not_a_vector_answer():
    c={'temporal_scope':['2013','2012'],'entity_scope':'Company','meta':{'currency':None,'scale':None,'unit':'ratio'}}
    p=Plan.parse({'reasoning_type':'StatisticalAggregation','operator':'average','subgoals':[['Debt to Equity Ratio',c]],'precision':'unknown'})
    assert [g.constraints.temporal_scope for g in p.subgoals]==['2013','2012']


def test_explicit_range_endpoints_are_extracted_without_calculation_or_arbitrary_selection():
    context='| Metric | 2024 |\n|---|---|\n| Fair value | $70.18 – $81.05 |'
    c=Constraints('2024','Company',{'currency':'USD','scale':None,'unit':None})
    for role,value in [('Lower bound',70.18),('Upper bound',81.05)]:
        goal=Goal(role+' fair value',c)
        b={'metric':goal.metric,'constraints':asdict(c),'value':value,'confidence':1,'source_label':'Fair value','context':'Fair value: '+str(value)}
        assert grounded(b,goal,context,[],'The requested bound is the explicit interval endpoint.')==value
        b['value']=80
        with pytest.raises(ProtocolError):grounded(b,goal,context,[],'Explicit interval endpoint.')


def test_ragged_multilevel_header_and_wrong_period_are_checked_from_source():
    context='| | Year Ended December |\n|---|---|\n| $ in millions | 2024 | 2023 | 2022 |\n| Provision for losses | 674 | 657 | 182 |'
    c=Constraints('2022','Company',{'currency':None,'scale':None,'unit':None})
    b={'metric':'Provision for losses','constraints':asdict(c),'value':182,'confidence':1,
       'source_label':'Provision for losses','context':'Provision for losses: 182'}
    assert grounded(b,Goal(b['metric'],c),context,[])==182
    b['value']=657
    with pytest.raises(ProtocolError):grounded(b,Goal(b['metric'],c),context,[])


def test_safe_container_operations_and_json_null_without_imports():
    code='def compute(vars):\n    value = vars.get("a") / vars.get("b")\n    return {"value": value, "trace": {"output_meta": {"currency": null}}}'
    result=asyncio.run(execute(code,{'a':10,'b':4}))
    assert result['value']==2.5 and result['trace']['output_meta']['currency'] is None
    assert result['trace']['executor_protocol']['json_literals_to_python']==['null']
    with pytest.raises(ProtocolError):validate_program('def compute(vars):\n    return vars.__class__')
    with pytest.raises(ProtocolError):validate_program('def compute(vars):\n    return "{0.__globals__}".format(range)')


def test_invalid_real_math_is_undefined_without_a_programming_error_mask():
    code='def compute(vars):\n    return {"value": math.sqrt(vars["x"]), "trace": {}}'
    assert asyncio.run(execute(code,{'x':-1})) is None
    assert asyncio.run(execute(code,{'x':4}))['value']==2


def test_transcendental_inverse_cannot_block_the_main_event_loop():
    graph=MetricGraph([Metric('Rate',[],'','atomic',[]),Metric('Periods',[],'','atomic',[]),Metric('Payment',[],'','atomic',[]),
        Metric('Present Value',[],'','derived',[Formula('annuity','Present Value','p*(1-(1+r)**(-n))/r',
            [Operand('p','Payment'),Operand('r','Rate'),Operand('n','Periods')],'PV = p*(1-(1+r)^(-n))/r')])])
    assert graph.inverses('Rate')==[]
    result=asyncio.run(graph.inverses_for('Rate',{'Present Value'},timeout=.05))
    assert result==[] and graph.inverse_failures[('Rate','annuity')]=='symbolic_solver_deadline'


def test_numeric_names_and_date_headers_do_not_turn_headers_into_observations():
    context='| Measurement Point December 31 | Fund | S&P 500 Index |\n|---|---|---|\n| 2023 | 120 | 110 |\n| 2024 | 150 | 130 |'
    c=Constraints('2024','Fund',{'currency':None,'scale':None,'unit':None})
    b={'metric':'Fund','constraints':asdict(c),'value':150,'context':'Fund: 150',
       'context_spans':['Measurement Point December 31 | Fund','2024 | 150'],'source_label':'Fund'}
    assert grounded(b,Goal('Fund',c),context,[])==150
    b['value']=130
    with pytest.raises(ProtocolError):grounded(b,Goal('Fund',c),context,[])


def test_table_projection_recovers_actual_source_but_checks_entity_and_period():
    context='| Name | Bonus | Cap |\n|---|---|---|\n| Alex | 30 | 90 |\n| Bea | 20 | 80 |'
    c=Constraints('2024','Alex',{'currency':None,'scale':None,'unit':None})
    b={'metric':'Bonus','constraints':asdict(c),'value':30,'context':'Bonus for Alex: 30',
       'context_spans':['| Name | Bonus |','| Alex | 30 |'],'source_label':'Alex'}
    assert grounded(b,Goal('Bonus',c),context,[])==30
    b.update(value=20,context='Bonus for Alex: 20',context_spans=['| Name | Bonus |','| Bea | 20 |'])
    with pytest.raises(ProtocolError):grounded(b,Goal('Bonus',c),context,[])


def test_raw_currency_symbol_is_preserved_as_a_source_constraint():
    c=Constraints.parse({'temporal_scope':'2024','entity_scope':'Group','meta':{'currency':'$','scale':'million','unit':None}})
    assert c.meta['currency']=='$'
    from gbfr.engine import currency_matches
    assert currency_matches('$','AUD') and currency_matches('$','USD')
    assert not currency_matches('USD','AUD') and not currency_matches('$','CNY')


def test_merged_year_headers_apply_to_each_column_in_the_group():
    context='| | 2024 | | 2023 | |\n|---|---|---|---|---|\n| | Count | Amount | Count | Amount |\n| Dividends | 2 | 90 | 3 | 80 |'
    c=Constraints('2023','Company',{'currency':None,'scale':None,'unit':None})
    b={'metric':'Dividends','constraints':asdict(c),'value':80,'source_label':'Dividends','context':'Dividends: 80',
       'context_spans':['|---|---|---|---|---|','| | 2024 | | 2023 | |','| Dividends | 2 | 90 | 3 | 80 |']}
    assert grounded(b,Goal('Dividends',c),context,[])==80
    b['value']=90
    with pytest.raises(ProtocolError):grounded(b,Goal('Dividends',c),context,[])


def test_split_descriptive_label_is_not_a_new_financial_alias():
    context='The world fleet was served by approximately 400 berths at the end of 2024.'
    c=Constraints('2024','world fleet',{'currency':None,'scale':None,'unit':'berths'})
    b={'metric':'World fleet berths','constraints':asdict(c),'value':400,'source_label':'world fleet ... berths',
       'context':'world fleet was served by approximately 400 berths'}
    assert grounded(b,Goal(b['metric'],c),context,[])==400
    b['value']=401
    with pytest.raises(ProtocolError):grounded(b,Goal(b['metric'],c),context,[])


def test_qualifier_in_oqa_constraint_adapter_is_never_silently_discarded():
    c={'temporal_scope':'2024','entity_scope':'Group','meta':{'currency':None,'scale':None,'unit':None},'metric_qualifier':'paid in cash'}
    goal=Goal.parse({'metric':'Total Dividends','constraints':c})
    assert goal.metric=='Total Dividends paid in cash'


def test_reference_display_rounding_is_prediction_independent_and_query_precision_wins():
    s={'answer':'34.4%','question':'What percentage?','unanswerable':False}
    p={'status':'answered','value':173000/503000,'meta':{'unit':'ratio'}}
    assert correct(p,s,precision_policy='reference_display')
    assert not correct(p,s,precision_policy='fixed')
    s['question']='What percentage to two decimal places?'
    assert not correct(p,s,precision_policy='reference_display')
    s.update(answer='1.72',question='What ratio?')
    p['value']=1.3027575107296137
    assert not correct(p,s,precision_policy='reference_display')


def test_paper_oes_decision_is_not_replaced_by_supplementary_lexical_guard():
    from gbfr.engine import GBFR
    from .helpers import ScriptedClient
    c=Constraints('2024','Company',{'currency':None,'scale':None,'unit':None})
    plan={'reasoning_type':'DirectRetrieval','operator':'sum','precision':'unknown',
          'subgoals':[{'metric':'Revenue','constraints':asdict(c)}]}
    class Client(ScriptedClient):
        async def json(self,task,prompt):
            r=await super().json(task,prompt)
            if task=='OES' and r['found']:
                r['notes']=None;r['var_bindings']['v1']['source_label']='Net sales'
            return r
    client=Client(asdict(c),{'Revenue':(40,'Net sales: 40')},plan=plan)
    graph=MetricGraph([Metric('Revenue',[],'','atomic',[])])
    p=asyncio.run(GBFR(graph,client,evidence_policy='paper').predict('Find Revenue','Net sales: 40'))
    assert p.status=='answered' and p.value==40
    assert any(e['operator']=='evidence_audit' for e in p.trace['events'])
    assert not any(task=='Verify' for task,_ in client.calls)


def test_ratio_output_cannot_inherit_monetary_operand_dimensions():
    from gbfr.units import result_meta
    assert result_meta({'unit':'percent','currency':'USD','scale':'million'})=={'unit':'percentage','currency':None,'scale':None}
    assert result_meta({'currency':'USD','scale':'million'},'ratio')=={'unit':None,'currency':None,'scale':None}
    assert result_meta({'unit':'currency/share','currency':'USD','scale':None},'division')['currency']=='USD'


def test_input_investment_dollars_are_not_the_unit_of_a_return_output():
    s={'question':'What is the return on investment if $100 is invested in a stock index?',
       'answer':'45.51','unanswerable':False}
    assert correct({'status':'answered','value':45.51,'meta':{'unit':'percentage'}},s,precision_policy='reference_display')
    assert not correct({'status':'answered','value':.4551,'meta':{'unit':'ratio'}},s,precision_policy='reference_display')


def test_placeholder_plan_is_a_technical_error_not_an_abstention():
    c={'temporal_scope':None,'entity_scope':None,'meta':{'currency':None,'scale':None,'unit':None}}
    with pytest.raises(ProtocolError,match='placeholder'):
        Goal.parse({'metric':'unknown','constraints':c})


def test_structured_plan_name_format_does_not_pretend_to_validate_semantics():
    import re
    from gbfr.prompts import PLAN_RESPONSE_FORMAT
    pattern=PLAN_RESPONSE_FORMAT['json_schema']['schema']['properties']['subgoals']['items']['properties']['metric']['pattern']
    for name in ['Revenue','Gross receivables','目标净利润','r','N/A revenue','Unknown liability','Net sales',"Owners' equity"]:
        assert re.fullmatch(pattern,name),name
    for name in ['unknown','null','none']:
        assert re.fullmatch(pattern,name)
    for name in ['',' ','unknown ']:
        assert not re.fullmatch(pattern,name),name


def test_financial_hints_exclude_numbers_in_question_amounts():
    from gbfr.engine import metric_hints
    graph=MetricGraph([Metric('100',[],'','atomic',[]),Metric('Price Return',[],'price-only return','atomic',[])])
    assert [h['canonical_metric'] for h in metric_hints(graph,'What is the Price Return on $100,000?')]==['Price Return']


def test_formula_literal_requires_its_explicit_rhs_and_is_not_document_data():
    from gbfr.graph import formula_literal
    f=Formula('percent','Margin','a/b*k',[Operand('a','Profit'),Operand('b','Revenue'),Operand('k','100')],
              'Margin = Profit / Revenue * 100')
    assert formula_literal(f,'100')==100
    assert formula_literal(f,'10') is None
    assert formula_literal(f,'Revenue') is None
    other=Formula('other','Value','x',[Operand('x','100')],'Value = benchmark value')
    assert formula_literal(other,'100') is None


@pytest.mark.parametrize('has_cost,expected',[(True,25),(False,None)])
def test_percentage_factor_is_not_a_missing_fact_but_cost_still_must_be_grounded(has_cost,expected):
    from gbfr.engine import GBFR
    from .helpers import ScriptedClient
    c=Constraints('2024','Company',{'currency':None,'scale':None,'unit':None})
    f=Formula('margin','Margin','(r-c)/r*k',[Operand('r','Revenue'),Operand('c','Cost'),Operand('k','100')],
              'Margin = (Revenue - Cost) / Revenue * 100',meta={'unit':'percentage'})
    graph=MetricGraph([Metric('Margin',[],'','derived',[f]),Metric('Revenue',[],'','atomic',[]),
                       Metric('Cost',[],'','atomic',[]),Metric('100',[],'','atomic',[])])
    plan={'reasoning_type':'DirectRetrieval','operator':'sum','precision':'unknown','subgoals':[{'metric':'Margin','constraints':asdict(c)}]}
    evidence={'Revenue':(120,'Revenue: 120')}
    if has_cost:evidence['Cost']=(90,'Cost: 90')
    client=ScriptedClient(asdict(c),evidence,plan=plan)
    p=asyncio.run(GBFR(graph,client).predict('Find margin','Revenue: 120. Cost: 90.' if has_cost else 'Revenue: 120.'))
    assert p.value==expected and p.status==('answered' if has_cost else 'abstained')
    assert not any(task=='OES' and '"metric": "100"' in prompt for task,prompt in client.calls)


def test_missing_operand_finishes_invalid_path_without_waiting_for_unneeded_subtree():
    from gbfr.engine import GBFR
    from .helpers import ScriptedClient
    c=Constraints('2024','Company',{'currency':None,'scale':None,'unit':None})
    graph=MetricGraph([Metric('Target',[],'','derived',[Formula('f','Target','a+b',[Operand('a','Absent'),Operand('b','Slow')],'Target = Absent + Slow')]),
                       Metric('Absent',[],'','atomic',[]),Metric('Slow',[],'','atomic',[])])
    plan={'reasoning_type':'DirectRetrieval','operator':'sum','precision':'unknown','subgoals':[{'metric':'Target','constraints':asdict(c)}]}
    class Client(ScriptedClient):
        async def json(self,task,prompt):
            if task=='OES':
                var=json.loads(prompt.rsplit('Variables to resolve:\n',1)[1].split('\nReturn JSON',1)[0])[0]
                if var['metric']=='Slow':await asyncio.Event().wait()
            return await super().json(task,prompt)
    client=Client(asdict(c),{},plan=plan)
    async def run():return await asyncio.wait_for(GBFR(graph,client).predict('Find Target','No values reported.'),timeout=2)
    p=asyncio.run(run())
    assert p.status=='abstained'


def test_pruning_an_invalid_path_does_not_cancel_another_paths_shared_operand():
    from gbfr.engine import GBFR
    from .helpers import ScriptedClient
    c=Constraints('2024','Company',{'currency':None,'scale':None,'unit':None})
    graph=MetricGraph([Metric('Target',[],'','derived',[
        Formula('bad','Target','a+b',[Operand('a','Absent'),Operand('b','Slow')],'Target = Absent + Slow'),
        Formula('good','Target','2*b',[Operand('b','Slow')],'Target = 2 * Slow')]),
        Metric('Absent',[],'','atomic',[]),Metric('Slow',[],'','atomic',[])])
    plan={'reasoning_type':'DirectRetrieval','operator':'sum','precision':'unknown','subgoals':[{'metric':'Target','constraints':asdict(c)}]}
    class Client(ScriptedClient):
        async def json(self,task,prompt):
            if task=='OES':
                var=json.loads(prompt.rsplit('Variables to resolve:\n',1)[1].split('\nReturn JSON',1)[0])[0]
                if var['metric']=='Slow':await asyncio.sleep(.05)
            return await super().json(task,prompt)
    client=Client(asdict(c),{'Slow':(4,'Slow: 4')},plan=plan)
    p=asyncio.run(GBFR(graph,client).predict('Find Target','Slow: 4'))
    assert p.status=='answered' and p.value==8
    slow=[prompt for task,prompt in client.calls if task=='OES' and '"metric": "Slow"' in prompt]
    assert len(slow)==1


def test_placeholder_description_cannot_be_miscounted_as_correct_abstention():
    from gbfr.engine import GBFR
    from .helpers import ScriptedClient
    c=Constraints(None,None,{'currency':None,'scale':None,'unit':None})
    plan={'reasoning_type':'DirectRetrieval','operator':'sum','precision':'unknown',
          'subgoals':[{'metric':'unknown requested financial metric','constraints':asdict(c)}]}
    client=ScriptedClient(asdict(c),{},plan=plan)
    with pytest.raises(ProtocolError,match='placeholder description'):
        asyncio.run(GBFR(MetricGraph([Metric('Revenue',[],'','atomic',[])]),client).predict('Find Revenue','Revenue: 40'))
    assert not any(task=='OES' for task,_ in client.calls)


def test_compound_temporal_constraint_is_not_misread_as_period_enumeration():
    c={'temporal_scope':'as of December 31, 2024; due within one year','entity_scope':'Company',
       'meta':{'currency':None,'scale':None,'unit':None}}
    raw={'reasoning_type':'ComparativeReasoning','operator':'ratio','precision':'unknown','subgoals':[{'metric':'Lease payments','constraints':c}]}
    p=Plan.parse(raw)
    assert len(p.subgoals)==1 and p.subgoals[0].constraints.temporal_scope==c['temporal_scope']
    c['temporal_scope']='2022; 2023; 2024'
    assert [g.constraints.temporal_scope for g in Plan.parse(raw).subgoals]==['2022','2023','2024']


def test_unused_subtree_releases_capacity_needed_by_a_valid_parallel_path():
    from gbfr.engine import GBFR
    from .helpers import ScriptedClient
    c=Constraints('2024','Company',{'currency':None,'scale':None,'unit':None})
    graph=MetricGraph([Metric('Target',[],'','derived',[
        Formula('bad','Target','a+b',[Operand('a','Absent'),Operand('b','Slow')],'Target = Absent + Slow'),
        Formula('good','Target','2*b',[Operand('b','Live')],'Target = 2 * Live')]),
        Metric('Absent',[],'','atomic',[]),Metric('Slow',[],'','atomic',[]),Metric('Live',[],'','atomic',[])])
    plan={'reasoning_type':'DirectRetrieval','operator':'sum','precision':'unknown','subgoals':[{'metric':'Target','constraints':asdict(c)}]}
    async def run():
        started=asyncio.Event();capacity=asyncio.Semaphore(1)
        class Client(ScriptedClient):
            async def json(self,task,prompt):
                if task=='OES':
                    var=json.loads(prompt.rsplit('Variables to resolve:\n',1)[1].split('\nReturn JSON',1)[0])[0]
                    if var['metric']=='Slow':
                        async with capacity:
                            started.set();await asyncio.Event().wait()
                    if var['metric']=='Absent':await started.wait()
                    if var['metric']=='Live':
                        await started.wait()
                        async with capacity:return await super().json(task,prompt)
                return await super().json(task,prompt)
        client=Client(asdict(c),{'Live':(4,'Live: 4')},plan=plan)
        return await asyncio.wait_for(GBFR(graph,client).predict('Find Target','Live: 4'),timeout=2)
    p=asyncio.run(run())
    assert p.status=='answered' and p.value==8


def test_split_assignment_name_repair_changes_no_numbers_or_string_keys():
    code='''def compute(vars):
    total_amount_bro ken = vars["a"] + vars["b"]
    return {"value": total_amount_bro ken, "trace": {"total_amount_bro ken": total_amount_bro ken}}
'''
    r=asyncio.run(execute(code,{'a':3,'b':4}))
    assert r['value']==7 and r['trace']['total_amount_bro ken']==7
    assert r['trace']['executor_protocol']['identifier_joins']=={'total_amount_bro ken':'total_amount_broken'}
    with pytest.raises(ProtocolError,match='syntax'):
        asyncio.run(execute('def compute(vars):\n    return vars["a"] vars["b"]',{'a':3,'b':4}))


def test_split_name_collision_is_not_repaired_by_overwriting_a_different_variable():
    code='def compute(vars):\n    total_amount_broken = 99\n    total_amount_bro ken = vars["a"]\n    return {"value": total_amount_broken, "trace": {}}'
    with pytest.raises(ProtocolError,match='syntax'):asyncio.run(execute(code,{'a':3}))


def test_next_over_finite_numeric_comparisons_is_a_valid_operator_program():
    code='''def compute(vars):
    checks = {"2023": vars["a"] < 10, "2024": vars["b"] < 10}
    year = next((y for y, matches in checks.items() if matches), None)
    return {"value": year, "trace": {"comparisons": checks}}
'''
    r=asyncio.run(execute(code,{'a':12,'b':8}))
    assert r['value']==2024


def test_explicit_singapore_currency_and_mil_abbreviation_are_representation_aliases():
    from gbfr.engine import currency_matches
    from gbfr.metrics import canonical
    m=normalize_meta({'currency':'S$','scale':'Mil','unit':None})
    assert m=={'currency':'SGD','scale':'million','unit':None}
    assert canonical(Decimal('11.3'),m)==canonical(Decimal('11.3'),{'currency':'SGD','scale':'million'})
    assert currency_matches('S$','SGD') and not currency_matches('S$','USD')
    with pytest.raises(ValueError):normalize_meta({'scale':'some unknown scale'})


def test_selecting_a_calendar_year_does_not_inherit_the_compared_amounts_scale():
    from gbfr.units import result_meta
    from gbfr.metrics import canonical
    raw={'currency':'USD','scale':'million','unit':'shares'}
    year=result_meta(raw,'compare',query='Which year had more awards?')
    assert year=={'currency':None,'scale':None,'unit':'years'}
    assert canonical(Decimal(2023),year)[0]==Decimal(2023)
    # Do not infer year selection merely because a result looks like a year.
    assert result_meta(raw,'compare',query='Which amount was larger?')['scale']=='million'
    assert result_meta(raw,'compare',query='What year-over-year growth was higher?')['scale']=='million'
    assert result_meta(raw,'difference',query="What year's revenue was larger?")['scale']=='million'


def test_explicit_currency_per_share_unit_is_not_a_new_physical_dimension():
    from gbfr.units import result_meta
    p={'status':'answered','value':48.126,'meta':{'currency':'USD','scale':'ones','unit':'USD/share'}}
    s={'question':'What was the price per share?', 'answer':'48.1','answer_meta':{},'context':'','unanswerable':False}
    p['meta']=result_meta(p['meta'])
    assert p['meta']=={'currency':'USD','scale':'ones','unit':'currency/share'}
    assert correct(p,s,2,'reference_display')
    p['meta']['currency']='GBP'
    s['answer_meta']={'currency':'USD'}
    assert not correct(p,s,2,'reference_display')
