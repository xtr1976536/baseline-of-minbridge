import asyncio
from dataclasses import asdict
import json
from pathlib import Path

import pytest

from gbfr.adjustments import correct_cf_gold, eligible
from gbfr.build_graph import Builder
from gbfr.data import jsonl, sha256, write_json
from gbfr.engine import GBFR
from gbfr.graph import Formula, Metric, MetricGraph, Operand, operand_goal
from gbfr.runner import audit_datasets, preflight, resolve_paths
from gbfr.types import AssetError, Constraints, ProtocolError
from .helpers import ScriptedClient


def record(name, formulas=(), related=(), aliases=()):
    return {'term_en': {'name': name, 'aliases': {'english': list(aliases)}},
            'definition_en': name, 'formula_en': list(formulas),
            'related_concepts_en': [{'concept': n, 'relation': 'Calculation'} for n in related]}


def test_helper_equation_keeps_its_actual_target_and_unknowns_are_not_guessed():
    graph, report, rejected = Builder([
        record('Article', ['Payment = Principal * Interest Rate', 'Article = mystery + 2'], ['Principal', 'Interest Rate']),
    ]).build()
    g = MetricGraph.load_object(graph)
    assert g.find('Article').kind == 'atomic'
    assert {o.metric for o in g.find('Payment').formulas[0].operands} == {'Principal', 'Interest Rate'}
    assert g.find('Principal').kind == 'atomic'
    assert report['benchmark_inputs_used'] is False
    assert any(n['name']=='Payment' and n['source_records']==[] for n in graph['nodes'])


def test_source_percent_representation_is_explicit_and_qualified_metrics_do_not_merge():
    obj, _, _ = Builder([
        record('Margin', ['Margin = Profit / Sales * 100%'], ['Profit', 'Sales']),
        record('Profit'), record('Adjusted Profit'), record('Sales'),
    ]).build()
    g = MetricGraph.load_object(obj)
    f = g.find('Margin').formulas[0]
    rhs, symbols = f.symbolic()
    assert float(rhs.subs({symbols['x0']:20, symbols['x1']:100})) == 20
    assert f.meta['unit'] == 'percentage'
    assert g.find('Profit').name != g.find('Adjusted Profit').name


def test_cycles_remove_whole_formulas_and_keep_independent_alternatives():
    obj, report, rejected = Builder([
        record('A', ['A = B + X', 'A = X * 2'], ['B','X']),
        record('B', ['B = A - X'], ['A','X']), record('X'),
    ]).build()
    g = MetricGraph.load_object(obj)
    assert any(r['reason']=='reverse_or_cyclic_dependency' for r in rejected)
    assert len(g.find('A').formulas) >= 1
    required={'A = B + X': {'B','X'}, 'A = X * 2': {'X'}, 'B = A - X': {'A','X'}}
    for name in ['A','B']:
        for f in g.find(name).formulas:
            assert {o.metric for o in f.operands} == required[f.source_formula]
    assert report['max_depth'] <= 6


def test_paper_roe_uses_average_equity_even_if_source_says_final_equity():
    obj, _, _ = Builder([record('Return on Equity', ['Return on Equity = Net Income / Final Equity'],
                               ['Net Income','Final Equity'])]).build()
    g = MetricGraph.load_object(obj)
    assert len(g.find('ROE').formulas) == 1
    assert [o.metric for o in g.find('ROE').formulas[0].operands] == ['Net Income','Average Equity']
    assert g.find('Final Equity').kind == 'atomic'
    assert g.provenance['paper_validated'] is False


def test_reference_code_conflicts_are_excluded_without_executing_the_code():
    a=record('Combined Amount',['Combined Amount = First Amount + Second Amount'],['First Amount','Second Amount'])
    a['code']=['def compute(first_amount, second_amount):\n    return first_amount - second_amount']
    b=record('Margin',['Margin = Profit / Sales * 100%'],['Profit','Sales'])
    b['code']=['def margin(profit, sales):\n    return profit / sales']
    c=record('Doubled Amount',['Doubled Amount = First Amount * 2'],['First Amount'])
    c['code']=['def value(first_amount):\n    return first_amount * 4']
    obj, _, _=Builder([a,b,c]).build()
    g=MetricGraph.load_object(obj)
    assert not g.find('Combined Amount').formulas
    assert not g.find('Doubled Amount').formulas
    assert g.find('Margin').formulas[0].meta['unit']=='percentage'


def test_formal_unqualified_acronym_does_not_merge_a_next_period_metric():
    obj,_,_=Builder([record('Earnings Before Interest and Taxes (EBIT)'),
                      record('Next Period EBIT',aliases=['EBIT'])]).build()
    g=MetricGraph.load_object(obj)
    assert g.find('EBIT').name=='Earnings Before Interest and Taxes (EBIT)'
    assert g.find('Next Period EBIT').name!=g.find('EBIT').name


def test_equivalent_formula_records_cannot_manufacture_consensus_votes():
    rows=[record('Cost of Sales',['Cost of Sales = Beginning Inventory + Purchases - Ending Inventory'],
                 ['Beginning Inventory','Purchases','Ending Inventory']),
          record('Cost of Sales',['Cost of Sales = Purchases - Ending Inventory + Beginning Inventory'],
                 ['Beginning Inventory','Purchases','Ending Inventory'])]
    obj,_,_=Builder(rows).build()
    g=MetricGraph.load_object(obj)
    cost=g.find('Cost of Sales')
    inventory=[f for f in cost.formulas if {o.metric for o in f.operands}=={'Beginning Inventory','Purchases','Ending Inventory'}]
    assert len(inventory)==1 and inventory[0].id.startswith('paper:')
    assert len(next(f for n in obj['nodes'] if n['name']=='Cost of Sales' for f in n['formulas'] if f['id']==inventory[0].id)['supporting_source_formulas'])>=2


def test_gold_fixes_require_exact_source_and_unchanged_context():
    a={'id':'a','source':{'file':'金融指标计算.json','index':18},'answer':'-0.037',
       'context':'净利润-214.8万元，销售收入5.799亿元'}
    q=correct_cf_gold(a)
    assert a['answer']=='-0.0037' and q['old_answer']=='-0.037'
    b={'id':'b','source':{'file':'金融指标计算.json','index':66},'answer':'4.26%',
       'context':'2021年6.4515；2022年6.7261'}
    correct_cf_gold(b)
    assert b['answer']=='4.08%'
    b['answer']='other label'
    with pytest.raises(AssetError):
        correct_cf_gold(b)


def test_scalar_eligibility_never_picks_one_number_and_keeps_comparison_types():
    assert eligible('CFBenchmark','0.7个百分点')
    assert not eligible('TAT-QA','ratio 2.00 and amount 100.0 million')
    assert not eligible('CFBenchmark','偏股混合型基金')
    assert eligible('FinanceReasoning',False)
    assert not eligible('CFBenchmark',False)


def test_relative_year_preserves_fiscal_scope_and_rejects_ambiguous_ranges():
    c=Constraints('FY2024', 'A', {'currency':None,'scale':None,'unit':None})
    assert operand_goal(Operand('e','Equity',{'temporal_scope':'$year-1'}),c).constraints.temporal_scope=='FY2023'
    with pytest.raises(AssetError):
        operand_goal(Operand('e','Equity',{'temporal_scope':'$year-1'}),Constraints('2023-2024','A',c.meta))
    with pytest.raises(AssetError):
        operand_goal(Operand('e','Equity',{'temporal_scope':'$year-1'}),Constraints('Q1 2024','A',c.meta))


def test_adjusted_data_gate_still_rejects_identity_or_audit_changes(tmp_path,monkeypatch):
    from gbfr import runner
    monkeypatch.setattr(runner,'EXPECTED',{'CFBenchmark':{'original':140,'counterfactual':11,'total':151}})
    row={'id':'frozen-id','question':'Find revenue','context':'Revenue: 10','answer':10,'unanswerable':False}
    path=tmp_path/'CFBenchmark.jsonl'
    path.write_text(json.dumps(row)+'\n',encoding='utf-8')
    audit=tmp_path/'CFBenchmark.adjustments.json'
    write_json(audit,{'exclusions':[]})
    manifest={'policy':'paper-method-v1','predictions_used':False,'datasets':{'CFBenchmark':{
        'expected_frozen':{'original':1,'counterfactual':0,'total':1},'processed_sha256':sha256(path),
        'retained_ids':['frozen-id'],'adjustments_sha256':sha256(audit)}}}
    write_json(tmp_path/'manifest.json',manifest)
    config={'data_dir':str(tmp_path),'asset_policy':'paper-method-v1'}
    assert audit_datasets(config)['all_datasets_ready']
    row['id']='substituted-id'
    path.write_text(json.dumps(row)+'\n',encoding='utf-8')
    issues=audit_datasets(config)['datasets']['CFBenchmark']['issues']
    assert 'frozen_sample_identity_mismatch' in issues and 'prepared_manifest_hash_mismatch' in issues
    audit.write_text('{}',encoding='utf-8')
    assert 'adjustment_audit_hash_mismatch' in audit_datasets(config)['datasets']['CFBenchmark']['issues']


@pytest.mark.parametrize('currency,raises',[('USD',False),('CNY',True)])
def test_observed_evidence_units_reach_calculation_without_changing_raw_value(currency,raises):
    c={'temporal_scope':'2024','entity_scope':'A','meta':{'currency':'USD','scale':None,'unit':None}}
    class Client(ScriptedClient):
        async def json(self,task,prompt):
            r=await super().json(task,prompt)
            if task=='OES' and r['found']:
                r['var_bindings']['v1']['observed_meta']={'currency':currency,'scale':'million','unit':None}
            return r
    client=Client(c,{'Gross Profit':(40,'Gross Profit: $40 million')})
    g=MetricGraph([Metric('Gross Profit',[], '', 'atomic',[])])
    if raises:
        result=asyncio.run(GBFR(g,client).predict('Find profit','Gross Profit: $40 million'))
        assert result.status=='abstained'
        assert any(e['operator']=='evidence_rejected' for e in result.trace['events'])
    else:
        pred=asyncio.run(GBFR(g,client).predict('Find profit','Gross Profit: $40 million'))
        ev=pred.trace['evidence'][0]
        assert ev['value']==40 and ev['meta']['scale']=='million'


@pytest.mark.skipif(not Path('data/assets/main_assets.lock.json').exists(),reason='run bootstrap for full assets')
def test_frozen_main_assets_and_no_gold_changes_in_model_inputs():
    config=resolve_paths(Path('configs/main.json'))
    graph,datasets=preflight(config)
    assert len(graph.nodes)>7000
    assert all(a['ready'] for a in audit_datasets(config)['datasets'].values())
    manifest=json.loads((Path(config['data_dir'])/'manifest.json').read_text(encoding='utf-8'))
    assert len(manifest['gold_corrections'])==2
    for name, rows in datasets.items():
        original={s['id']:s for s in jsonl(Path('data/processed')/(name+'.jsonl'))}
        for row in rows:
            assert row['question']==original[row['id']]['question']
            assert row['context']==original[row['id']]['context']
            if row['unanswerable']:
                assert row['answer'] is None
    assert not graph.provenance['benchmark_inputs_used']


@pytest.mark.skipif(not Path('data/assets/fmkg.reconstructed.json').exists(),reason='run bootstrap for full graph')
@pytest.mark.parametrize('has_prior',[False,True])
def test_paper_multihop_and_abstention_use_the_full_reconstructed_graph(has_prior):
    g=MetricGraph.load('data/assets/fmkg.reconstructed.json')
    c={'temporal_scope':'2024','entity_scope':'Company A','meta':{'currency':None,'scale':None,'unit':'ratio'}}
    plan={'reasoning_type':'ComparativeReasoning','operator':'change ratio','precision':'percentage',
          'subgoals':[{'metric':'ROE','constraints':c},
                      {'metric':'ROE','constraints':{**c,'temporal_scope':'2023'}}]}
    evidence={('Net Income','2024'):(500,'Net Income 2024: 500'),
              ('Net Income','2023'):(420,'Net Income 2023: 420'),
              ('Final Equity','2024'):(2500,'Total Equity 2024: 2500'),
              ('Final Equity','2023'):(2200,'Total Equity 2023: 2200')}
    if has_prior:
        evidence[('Final Equity','2022')]=(1900,'Total Equity 2022: 1900')
    client=ScriptedClient(c,evidence,plan=plan)
    result=asyncio.run(GBFR(g,client).predict('Compute ROE growth', '; '.join(v[1] for v in evidence.values())))
    assert result.status==('answered' if has_prior else 'abstained')
    if has_prior:
        expected=(500/2350-420/2050)/(420/2050)
        assert result.value==pytest.approx(expected)
