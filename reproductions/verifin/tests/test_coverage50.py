import json
from dataclasses import replace
from pathlib import Path
import pytest
from verifiqa.agent.types import RoleSpec
from vf_repro.authority import authorize,signature
from vf_repro.semantics import normalize_plan,question_equation,question_policy
from vf_repro.question_math import checked_subdefinitions
from vf_repro.retrieval import row_lexical_score,table_header,select_chunks
from vf_repro.source_rows import tagged_row_labels
from test_paper_fixes import filing,fact,spec


def test_lexical_score_rewards_a_financial_row_not_a_risk_paragraph():
    assert row_lexical_score(['Inventories'],'Inventories                 6,854       7,367')==1
    assert row_lexical_score(['Inventories'],'We manage inventories and inventory-related business risks.')==0


def test_bounded_evidence_preserves_each_operands_best_reranked_exact_row():
    rankings=[[0,1,2,3],[1,0,4,5]]
    rows=[{2,3},{4,5}]
    assert select_chunks(rankings,rows,3,preserve_operand_rows=True)==[2,4,0]
    assert select_chunks(rankings,rows,3)==[0,1,2]


def test_operand_row_selection_deduplicates_shared_year_columns_and_keeps_bound():
    assert select_chunks([[0,1,2],[1,0,2]],[{2},{2}],2,preserve_operand_rows=True)==[2,0]
    assert select_chunks([[0,1],[0,2]],[set(),set()],2,preserve_operand_rows=True)==[0,1]
    assert select_chunks([[0,1],[0,2]],[{1},{2}],1,preserve_operand_rows=True)==[1]


def test_financial_headers_keep_units_and_periods_without_copying_answer_rows():
    h=table_header('Table of Contents\nCONSOLIDATED BALANCE SHEETS\n(In millions)\n     2021    2020\nInventories       6854    7367')
    assert 'millions' in h and '2021' in h and '6854' not in h and 'Table of Contents' not in h


def test_issuer_tag_to_row_mapping_uses_labels_not_numeric_values():
    html=b'<table><tr><td>Capital spending</td><td>(<ix:nonFraction name="us-gaap:PaymentsToAcquireProductiveAssets">4625</ix:nonFraction>)</td></tr></table>'
    assert tagged_row_labels(html)=={'us-gaap:PaymentsToAcquireProductiveAssets':['Capital spending']}
    assert tagged_row_labels(html.replace(b'4625',b'999'))==tagged_row_labels(html)


def test_less_is_a_question_authorized_subtraction():
    s=spec('net_working_capital',[RoleSpec('current_assets',period='2022'),RoleSpec('current_liabilities',period='2022')],
           'current_assets-current_liabilities',measure='USD millions')
    q='What is net working capital? Define net working capital as total current assets less total current liabilities. Answer in USD millions.'
    assert signature(question_equation(q,s))==signature(s.formula)


def test_average_expands_derived_margin_roles_using_registered_leaves():
    s=spec('capex_as_percent_of_revenue',[
        RoleSpec('capex_as_percent_of_revenue_2017',period='2017'),
        RoleSpec('capex_as_percent_of_revenue_2018',period='2018'),
        RoleSpec('capex_as_percent_of_revenue_2019',period='2019')],'a',measure='percent')
    q='What is the FY2017 - FY2019 3 year average of capex as a % of revenue?'
    s,_=normalize_plan(s,q,'',filing([]))
    assert len(s.roles)==6 and s.metric.endswith('3yr_avg')
    assert {r.period for r in s.roles}=={'2017','2018','2019'}


def test_period_margin_change_expands_ratios_before_subtotal_authorization():
    s=spec('operating_income_margin_change',[
        RoleSpec('operating_margin_start',period='2018'),RoleSpec('operating_margin_end',period='2019')],
        '(operating_margin_end-operating_margin_start)*100',measure='percent')
    q='What is the FY2018 - FY2019 change in unadjusted operating income % margin? Round to one decimal place.'
    s,_=normalize_plan(s,q,'',filing([]))
    assert len(s.roles)==4 and {r.period for r in s.roles}=={'2018','2019'}
    f=filing([fact('us-gaap:OperatingIncomeLoss',10,'2019-12-31','2019-01-01'),
              fact('us-gaap:Revenues',100,'2019-12-31','2019-01-01')])
    f.data['calculations']=[{'role':'income_statement','parent':'us-gaap:OperatingIncomeLoss',
        'children':[{'concept':'us-gaap:Revenues','weight':1},{'concept':'us-gaap:CostOfRevenue','weight':-1}]}]
    admitted,authority=authorize(s,q,'',f,{})
    assert authority['kind']=='curated_metric_registry' and len(admitted.roles)==4
    assert '/' in admitted.formula


@pytest.mark.parametrize('value,expected',[(20,'(net_income-dividends_paid)/net_income'),(-20,'(net_income+dividends_paid)/net_income')])
def test_sign_variants_use_only_documented_cash_convention_and_raw_fact(value,expected):
    f=filing([fact('us-gaap:NetIncomeLoss',100,'2022-12-31','2022-01-01'),
              fact('us-gaap:PaymentsOfDividends',value,'2022-12-31','2022-01-01')])
    s=spec('retention_ratio',[RoleSpec('net_income',period='2022'),RoleSpec('dividends_paid',period='2022')],expected)
    admitted,a=authorize(s,'What is the retention ratio for FY2022?','',f,{})
    assert signature(admitted.formula)==signature(expected)
    assert a['cash_sign_normalization']['concept']=='us-gaap:PaymentsOfDividends'


def test_verified_inner_ebitda_definition_can_support_outer_less_capex():
    s=spec('unadjusted_ebitda_less_capex',[RoleSpec('operating_income',period='2022'),
        RoleSpec('depreciation_amortization',period='2022'),RoleSpec('capex',period='2022')],
        'operating_income + depreciation_amortization - capex',measure='USD millions')
    q='What is unadjusted EBITDA less capex? Define unadjusted EBITDA as unadjusted operating income + depreciation and amortization [from cash flow statement]. Answer in USD millions.'
    assert checked_subdefinitions(q,s)
    bad=q.replace(' + depreciation',' - depreciation')
    assert not checked_subdefinitions(bad,s)


def test_nested_ccc_definitions_are_composed_from_question_arithmetic():
    roles=[RoleSpec(n,period='2018' if n.endswith('start') else '2019') for n in [
        'inventory_start','inventory_end','accounts_receivable_start','accounts_receivable_end',
        'accounts_payable_start','accounts_payable_end','cost_of_revenue','revenue']]
    s=spec('cash_conversion_cycle',roles,'',measure='days')
    q=('What is FY2019 cash conversion cycle (CCC)? CCC is defined as: DIO + DSO - DPO. '
       'DIO is defined as: 365 * (average inventory between FY2018 and FY2019) / (FY2019 COGS). '
       'DSO is defined as: 365 * (average accounts receivable between FY2018 and FY2019) / (FY2019 Revenue). '
       'DPO is defined as: 365 * (average accounts payable between FY2018 and FY2019) / '
       '(FY2019 COGS + change in inventory between FY2018 and FY2019). Round to two decimal places.')
    eq=question_equation(q,s)
    assert eq is not None
    assert 'accounts_payable' in eq and 'accounts_receivable' in eq and 'inventory' in eq
    assert question_policy(q) is None  # Do not select the AP policy from a nested definition.


def test_validation_profile_cannot_be_launched_with_the_full_run_command(tmp_path,monkeypatch,capsys):
    import sys
    from vf_repro.runner import main
    p=tmp_path/'configs/coverage.json';p.parent.mkdir()
    p.write_text(json.dumps({'scope':'verifin-main-user-backbone','run_mode':'coverage_validation',
        'datasets':['FinanceBench'],'models':{'GPT-5.6-Sol':{'model':'gpt-5.6-sol'}},
        'backbone_override':{'source':'explicit_user_request','requested_model':'gpt-5.6-sol'}}),encoding='utf-8')
    monkeypatch.setattr(sys,'argv',['verifin','run','--config',str(p)])
    with pytest.raises(SystemExit) as e:main()
    assert e.value.code==2 and 'validation_profile_and_validate_command' in capsys.readouterr().err


@pytest.mark.parametrize('n',[49,67])
def test_validation_rejects_too_small_and_full_dataset_scopes(tmp_path,n):
    from vf_repro.runner import run_cell
    from vf_repro.common import write_jsonl,write_json,digest
    data=tmp_path/'data/main/FinanceBench.jsonl';write_jsonl(data,[{'id':str(i)} for i in range(67)])
    write_json(tmp_path/'manifest.json',{'ids':[str(i) for i in range(n)],'dataset_sha256':digest(data)})
    with pytest.raises(ValueError,match='50_or_more'):
        run_cell(tmp_path,{'run_mode':'coverage_validation','validation_manifest':'manifest.json'},'FinanceBench','model',None)


def test_newly_appearing_optional_labels_cannot_silently_change_a_validation(tmp_path):
    from vf_repro.runner import run_cell
    from vf_repro.common import write_jsonl,write_json,digest
    data=tmp_path/'data/main/FinanceBench.jsonl';write_jsonl(data,[{'id':str(i)} for i in range(67)])
    write_json(tmp_path/'manifest.json',{'ids':[str(i) for i in range(50)],'dataset_sha256':digest(data)})
    write_json(tmp_path/'lock.json',{'files':{},'absent':['unexpected.json']});write_json(tmp_path/'unexpected.json',{})
    with pytest.raises(ValueError,match='previously_absent'):
        run_cell(tmp_path,{'run_mode':'coverage_validation','validation_manifest':'manifest.json','validation_inputs_lock':'lock.json'},'FinanceBench','model',None)
