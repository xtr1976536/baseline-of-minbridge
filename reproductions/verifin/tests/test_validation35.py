import json
from dataclasses import replace
import pytest
from verifiqa.agent.types import RoleSpec
from vf_repro.concept_extensions import qualified_extension
from vf_repro.document_tables import html_table_pages
from vf_repro.retrieval import table_labels,table_header,statement_scope,plan_retrieval
from vf_repro.authority import authorize,signature
from vf_repro.generation import AnswerGenerator
from vf_repro.solver import verify
from test_paper_fixes import filing,fact,spec


def test_inventory_variant_is_value_blind_and_requires_total_row_label():
    q='us-gaap:InventoryFinishedGoodsNetOfReserves'
    f=filing([fact(q,24,'2022-12-31')]);f.data['labels']={q:['Inventories']}
    r=RoleSpec('inventory',['Inventories'],'2022')
    a=f.bind(r,'USD','2022')
    f.data['facts'][0]['value']='999'
    b=f.bind(r,'USD','2022')
    assert a['concept']==b['concept']==q and a['value']!=b['value']
    f.data['labels'][q]=['Finished goods']
    assert qualified_extension('InventoryLike',f.data) is None


def test_net_receivables_balance_cannot_bind_cash_flow_change_with_same_label():
    q='us-gaap:ReceivablesNetCurrent';cf='us-gaap:IncreaseDecreaseInAccountsReceivable'
    f=filing([fact(q,30,'2022-12-31'),fact(cf,7,'2022-12-31','2022-01-01')]);f.data['labels']={q:['Receivables'],cf:['Receivables']}
    b=f.bind(RoleSpec('receivables',['Receivables'],'2022'),'USD','2022')
    assert b['value']=='30' and b['period']['instant']=='2022-12-31'


def test_html_table_rendering_keeps_cells_years_and_negative_signs():
    html=b'''<h2>Consolidated Statements of Cash Flows</h2><table>
    <tr><td>2022</td><td>2021</td></tr><tr><td>(In millions)</td></tr>
    <tr><td>Depreciation and amortization</td><td>17</td><td>19</td></tr>
    <tr><td>Net loss</td><td>(20)</td><td>(30)</td></tr></table>'''
    pages=html_table_pages(html);assert len(pages)==1
    text=pages[0]['text']
    assert 'Depreciation and amortization  17  19' in text and '(20)' in text and '(30)' in text
    assert '2022 2021' in table_header(text)
    assert statement_scope(text,'cash flow')==2
    assert table_labels(text)[0]=='Depreciation and amortization'


def test_date_headers_survive_without_copying_data_rows():
    h=table_header('Consolidated Statements of Cash Flows\nDecember 26, 2022  December 27, 2021\nNet revenue  6789  1234')
    assert '2022' in h and '2021' in h and '6789' not in h


def test_primary_statement_scope_excludes_parent_only_and_notes():
    assert statement_scope('Consolidated Balance Sheets\nAssets  100  90','balance sheet')==2
    assert statement_scope('BALANCE SHEETS\nSCHEDULE I CONDENSED FINANCIAL INFORMATION OF PARENT\nAssets  100','balance sheet')==-1
    assert statement_scope('Notes to Consolidated Financial Statements\nAssets  100  90','balance sheet')==0
    assert statement_scope('Consolidated Statements of Cash Flows','income statement')==0


def test_question_ratio_uses_percent_representation_once():
    f=filing([fact('us-gaap:NetIncomeLoss',18,'2022-12-31','2022-01-01'),
              fact('us-gaap:Assets',180,'2021-12-31'),fact('us-gaap:Assets',220,'2022-12-31')])
    s=spec('return_on_assets',[RoleSpec('net_income',period='2022'),RoleSpec('assets_start',['total assets'],'2021'),
        RoleSpec('assets_end',['total assets'],'2022')],'net_income/((assets_start+assets_end)/2)',measure='percent')
    q='What is FY2022 ROA? ROA is defined as: FY2022 net income / (average total assets between FY2021 and FY2022).'
    admitted,a=authorize(s,q,'',f,{})
    assert a['display_conversion']['factor']==100
    values={'net_income':18,'assets_start':180,'assets_end':220}
    assert verify(admitted.formula,values,9,.005)['status']=='VERIFIED'
    assert verify(admitted.formula,values,900,.005)['status']=='VIOLATED'


def test_explicit_percent_factor_is_not_applied_twice():
    from vf_repro.authority import question_display_equation,structural_ir
    f=filing([fact('us-gaap:NetIncomeLoss',10),fact('us-gaap:Revenues',100)])
    s=spec('margin',[RoleSpec('net_income',period='2022'),RoleSpec('revenue',period='2022')],
        'net_income/revenue*100',measure='percent')
    formula,note=question_display_equation(s.formula,s,structural_ir(s,{},f))
    assert signature(formula)==signature(s.formula) and note is None


def test_generation_preserves_source_precision_without_feedback_or_gold():
    class Fake:
        def chat(self,messages,**kwargs):
            self.prompt=messages[0].content;self.stage=kwargs['stage'];return '{"answer":"1"}'
    fake=Fake();g=AnswerGenerator(fake)
    assert g.generate('What is the margin?',[])=='1'
    assert 'six significant' in fake.prompt and fake.stage=='answer_generation'
    with pytest.raises(ValueError,match='forbids'):g.generate('Question',[],feedback='try again')


def test_question_named_ebitda_addbacks_do_not_include_unnamed_content_costs():
    f=filing([fact('us-gaap:OperatingIncomeLoss',10),fact('us-gaap:Revenues',100),
        fact('us-gaap:DepreciationDepletionAndAmortization',2),fact('issuer:DVD',3),fact('issuer:Streaming',4)])
    f.data['labels']={'issuer:DVD':['DVD content amortization'],'issuer:Streaming':['Streaming content amortization']}
    s=spec('unadjusted_ebitda_margin_percent',[RoleSpec('operating_income',period='2022'),
        RoleSpec('depreciation_amortization',period='2022'),RoleSpec('revenue',period='2022'),
        RoleSpec('dvd_content_amortization',['DVD content amortization'],'2022'),
        RoleSpec('streaming_content_amortization',['Streaming content amortization'],'2022')],
        '(operating_income+depreciation_amortization+dvd_content_amortization+streaming_content_amortization)/revenue*100',measure='percent')
    q='What is FY2022 EBITDA % margin? Calculate unadjusted EBITDA using unadjusted operating income and D&A from cash flow statement.'
    admitted,a=authorize(s,q,'',f,{})
    assert {r.name for r in admitted.roles}=={'operating_income','depreciation_amortization','revenue'}
    assert a['kind']=='curated_metric_registry'


def test_secondary_currency_padding_policy_is_explicit_bounded_and_keeps_legacy():
    from vf_repro.scoring import correctness
    row={'dataset':'FinanceBench','question':'What is the amount in USD billions?','gold':{'answer':'$0.40','unit':None}}
    result={'claimed_value':'.389','claimed_unit':'USD billions'}
    assert correctness(row,result) is False
    assert correctness(row,result,policy='financebench_currency_padding_v1') is True
    assert correctness(row,{**result,'claimed_value':'.451'},policy='financebench_currency_padding_v1') is False
    explicit={**row,'question':row['question']+' Round to two decimal places.'}
    assert correctness(explicit,result,policy='financebench_currency_padding_v1') is False
    zero={**row,'gold':{'answer':'$0.00','unit':None}}
    assert correctness(zero,{**result,'claimed_value':'.001'},policy='financebench_currency_padding_v1') is False


def test_income_statement_location_cannot_be_proved_by_a_cash_flow_or_note_fact():
    from vf_repro.pipeline import validate_explicit_statement_line
    from vf_repro.grounding import Unresolved
    q='What costs are directly outlined in the income statement? If not explicitly outlined state 0.'
    f=filing([]);binding={'concept':'issuer:Cost'}
    f.data['calculations']=[{'role':'http://issuer/role/ConsolidatedStatementOfCashFlows',
        'parent':'issuer:Cash','children':[{'concept':'issuer:Cost','weight':1}]}]
    with pytest.raises(Unresolved,match='income_statement_line'):validate_explicit_statement_line(q,[binding],f)
    f.data['calculations'][0]['role']='http://issuer/role/ConsolidatedStatementOfIncome'
    validate_explicit_statement_line(q,[binding],f)


@pytest.mark.parametrize('n',[34,36,67])
def test_35_question_profile_rejects_other_sizes(tmp_path,n):
    from vf_repro.common import write_json,write_jsonl,digest
    from vf_repro.runner import run_cell
    p=tmp_path/'data/main/FinanceBench.jsonl';write_jsonl(p,[{'id':str(i)} for i in range(67)])
    write_json(tmp_path/'manifest.json',{'ids':[str(i) for i in range(n)],'dataset_sha256':digest(p)})
    with pytest.raises(ValueError,match='exactly_35'):
        run_cell(tmp_path,{'run_mode':'coverage_validation','validation_sample_size':35,'validation_manifest':'manifest.json'},'FinanceBench','model',None)
