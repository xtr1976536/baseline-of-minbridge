"""Source-only reference-code parameter binding; no benchmark labels or API."""
import json
from pathlib import Path

import pytest

from gbfr.graph_recovery import SourceIndex,bind_reference_code,bind_formula,compare_bound_expressions
from gbfr.build_graph import Builder,conservative_extension


def item(name,*,aliases=(),formula=None,code=None,related=()):
    r={'term_en':{'name':name,'aliases':{'english':list(aliases)}},'formula_en':[],'related_concepts_en':[{'concept':x} for x in related]}
    if formula is not None:r['formula_en']=[formula]
    if code is not None:r['code']=[code]
    return r


def records(code,*,extra=(),related=('Total Assets','Revenue')):
    return [item('Local Ratio',formula='Local Ratio = Total Assets / Revenue',code=code,related=related),
            item('Assets'),item('Total Assets',aliases=['Assets']),item('Revenue'),*extra]


def test_local_declared_alias_beats_an_unrelated_global_canonical_parameter_name():
    rr=records('def ratio(assets, revenue):\n    return assets/revenue')
    index=SourceIndex(rr);assert index.resolve('assets')['metric']=='Assets'
    bound=bind_reference_code(index,0,0)
    assert [o['metric'] for o in bound['operands']]==['Total Assets','Revenue']
    assert bound['record_local_parameter_bindings'][0]['global_metric']=='Assets'
    assert bound['record_local_parameter_bindings'][0]['binding_source']=='record_local_explicit_alias'
    assert compare_bound_expressions(bind_formula(index,0,0),bound)=='symbolically_equivalent'
    # Local binding does not declare a global financial synonym.
    assert index.resolve('assets')['metric']=='Assets'


def test_missing_total_alias_is_not_inferred_from_position_or_formula_shape():
    rr=[item('Leverage',formula='Leverage = Total Liabilities / Total Assets',
             code='def leverage(liabilities, assets):\n    return liabilities/assets',related=['Total Liabilities','Total Assets']),
        item('Liabilities'),item('Total Liabilities'),item('Assets'),item('Total Assets',aliases=['Assets'])]
    index=SourceIndex(rr);bound=bind_reference_code(index,0,0)
    assert [o['metric'] for o in bound['operands']]==['Liabilities','Total Assets']
    assert compare_bound_expressions(bind_formula(index,0,0),bound)=='symbolic_disagreement_requires_review'


def test_ambiguous_local_alias_cannot_choose_a_qualified_metric():
    rr=records('def ratio(assets, revenue):\n    return assets/revenue',
               extra=[item('Adjusted Assets',aliases=['Assets'])],related=['Total Assets','Adjusted Assets','Revenue'])
    bound=bind_reference_code(SourceIndex(rr),0,0)
    assert bound['operands'][0]['metric']=='Assets'
    assert bound['record_local_parameter_bindings']==[]


def test_explicit_parameter_documentation_can_define_the_local_metric_role():
    rr=records('''def ratio(x, revenue):
    """Args:
        x (float): The total assets of the company.
        revenue (float): Revenue.
    """
    return x/revenue
''')
    index=SourceIndex(rr);bound=bind_reference_code(index,0,0)
    assert bound['status']=='syntactically_bound'
    assert bound['operands'][0]['metric']=='Total Assets'
    assert bound['record_local_parameter_bindings'][0]['binding_source']=='explicit_parameter_documentation'
    assert compare_bound_expressions(bind_formula(index,0,0),bound)=='symbolically_equivalent'


def test_parameter_description_does_not_erase_a_financial_qualifier():
    rr=records('''def ratio(x, revenue):
    """Args:
        x (float): Adjusted total assets of the company.
    """
    return x/revenue
''')
    assert bind_reference_code(SourceIndex(rr),0,0)['reason']=='unresolved_code_parameter'


def test_related_concept_order_never_binds_generic_argument_positions():
    rr=records('def ratio(numerator, denominator):\n    return numerator/denominator')
    assert bind_reference_code(SourceIndex(rr),0,0)['reason']=='unresolved_code_parameter'


def test_two_parameter_roles_are_not_collapsed_by_one_local_alias():
    rr=records('def ratio(assets, total_assets):\n    return assets-total_assets',related=['Total Assets'])
    bound=bind_reference_code(SourceIndex(rr),0,0)
    assert bound['status']=='syntactically_bound'
    assert [o['metric'] for o in bound['operands']]==['Assets','Total Assets']
    assert bound['record_local_parameter_bindings']==[]


def test_builder_restores_proven_local_binding_but_rejects_real_operator_conflict():
    good=Builder(records('def ratio(assets, revenue):\n    return assets/revenue'))
    good.parse(0,0,good.records[0]['formula_en'][0])
    assert good.decisions[0]['status']=='parsed_candidate'
    assert good.candidates[0]['reference_code_check']=='equivalent'
    assert good.candidates[0]['record_local_parameter_bindings'][0]['metric']=='Total Assets'
    bad=Builder(records('def ratio(assets, revenue):\n    return assets+revenue'))
    bad.parse(0,0,bad.records[0]['formula_en'][0])
    assert bad.decisions[0]['reason']=='formula_code_semantic_disagreement'
    assert not bad.candidates


def test_actual_record_five_still_requires_liability_identity_evidence():
    p=Path(__file__).resolve().parents[1]/'research/upstream/knowledge_base/term_en_final.json'
    if not p.exists():pytest.skip('Pinned raw source not installed')
    raw=json.loads(p.read_text(encoding='utf-8'));bound=bind_reference_code(SourceIndex(raw),5,0)
    assert [o['metric'] for o in bound['operands']]==['Liabilities','Total Assets']
    assert [b['parameter'] for b in bound['record_local_parameter_bindings']]==['assets']


def base_node(name,formulas=()):
    return {'name':name,'aliases':[],'definition':'source definition','formulas':list(formulas),
            'kind':'derived' if formulas else 'atomic','classification_basis':'baseline'}


def formula(ident,target,expression,operands,*,unit=None):
    return {'id':ident,'target':target,'expression':expression,'source_formula':target+' = '+expression,
            'operands':[{'symbol':s,'metric':m} for s,m in operands], 'meta':{'unit':unit},
            'record_local_parameter_bindings':[{'parameter':operands[0][0],'metric':operands[0][1],'binding_source':'source_alias'}],
            'reference_code_check':'equivalent','source_records':[0],'source_formula_index':0,'priority':3}


def baseline():
    old=formula('old:R','R','a/b',[('a','A'),('b','B')],unit='ratio')
    old={k:v for k,v in old.items() if k not in {'target','priority'}}
    return {'schema_version':1,'nodes':[base_node('A'),base_node('B'),base_node('R',[old]),base_node('T')]}


def test_conservative_extension_preserves_old_formulas_and_only_adds_proven_paths():
    old=baseline();old_formula=old['nodes'][2]['formulas'][0]
    graph,report=conservative_extension(old,[formula('new:T','T','a+b',[('a','A'),('b','B')])])
    by={n['name']:n for n in graph['nodes']}
    assert by['R']['formulas']==[old_formula]
    assert by['T']['kind']=='derived' and by['T']['formulas'][0]['id']=='new:T'
    assert old['nodes'][3]['kind']=='atomic' and old['nodes'][3]['formulas']==[]
    assert report['old_formula_ids_preserved'] and report['removed_formula_ids']==[]
    unproven=formula('weak:T','T','a+b',[('a','A'),('b','B')]);unproven['reference_code_check']='unverifiable_static_code'
    unchanged,report=conservative_extension(old,[unproven])
    assert unchanged['nodes']==old['nodes'] and report['eligible_source_equations']==0


def test_new_formula_cannot_replace_an_old_dag_edge_to_resolve_a_cycle():
    old=baseline()
    graph,report=conservative_extension(old,[formula('new:A','A','r*b',[('r','R'),('b','B')])])
    assert graph['nodes']==old['nodes']
    assert report['skip_counts']=={'would_cycle_old_or_added_dag':1}


def test_equivalent_percentage_path_is_not_an_additional_vote():
    graph,report=conservative_extension(baseline(),[formula('new:R','R','100*a/b',[('a','A'),('b','B')],unit='percentage')])
    assert len(next(n for n in graph['nodes'] if n['name']=='R')['formulas'])==1
    assert report['skip_counts']=={'duplicate_equation_not_an_independent_vote':1}


def test_extension_must_not_increase_an_old_ancestor_beyond_depth_six():
    nodes=[base_node('L0'),base_node('Extra')]
    for i in range(1,7):
        f=formula('old:'+str(i),'L'+str(i),'x+1',[('x','L'+str(i-1))])
        nodes.append(base_node('L'+str(i),[{k:v for k,v in f.items() if k not in {'target','priority'}}]))
    old={'schema_version':1,'nodes':nodes}
    graph,report=conservative_extension(old,[formula('new:L0','L0','x+1',[('x','Extra')])])
    assert graph['nodes']==old['nodes'] and report['max_depth']==6
    assert report['skip_counts']=={'would_exceed_depth_six':1}
