import json
from dataclasses import replace
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
import pytest
from verifiqa.agent.types import ClaimSpec,RoleSpec,GroundedFact
from vf_repro.grounding import Filing,Unresolved,unit
from vf_repro.semantics import normalize_plan,question_equation,role_measure
from vf_repro.authority import authorize,signature
from vf_repro.pipeline import PaperVerifier


def filing(facts,year=2022,end='2022-12-31',doc='COMPANY_2022_10K',labels=None):
    return Filing({'doc_name':doc,'fiscal_year':year,'period_end':end,'accession':'fixture',
        'source_url':'https://www.sec.gov/Archives/fixture.xml','instance_sha256':'fixture',
        'facts':facts,'labels':labels or {},'calculations':[]})


def fact(concept,value,end='2022-12-31',start=None,currency='USD'):
    return {'concept':concept,'value':str(value),'unit':'iso4217:'+currency,'id':concept+str(start)+end,
        'decimals':'0','period':{'instant':'' if start else end,'start_date':start or '',
                               'end_date':end if start else '','dimensions':[]}}


def spec(metric,roles,formula,measure='ratio',period='2022'):
    return ClaimSpec(metric,formula,roles,measure,.005,'policy_registry',period)


def test_ratio_operands_have_money_units_and_ignore_unrelated_foreign_currency():
    f=filing([fact('us-gaap:AssetsCurrent',200),fact('us-gaap:LiabilitiesCurrent',100),
              fact('ext:UnrelatedForeignDebt',500,currency='SEK')])
    s=spec('current_ratio',[RoleSpec('current_assets',period='2022'),RoleSpec('current_liabilities',period='2022')],
           'current_assets / current_liabilities')
    assert role_measure(s.roles[0],'ratio',f)=='USD millions'
    admitted,authority=authorize(s,'What was the current ratio for 2022?','',f,{})
    assert admitted.formula==s.formula and authority['kind']=='curated_metric_registry'
    assert unit('iso4217:SEK')==('sek',Decimal(1))


DPO_QUESTION=('What is FY2018 days payable outstanding (DPO)? DPO is defined as: '
    '365 * (average accounts payable between FY2017 and FY2018) / '
    '(FY2018 COGS + change in inventory between FY2017 and FY2018). Round your answer to two decimal places.')


def dpo_filing():
    facts=[]
    for year,ap,inventory in [(2017,100,50),(2018,200,60)]:
        facts += [fact('us-gaap:AccountsPayableCurrent',ap,f'{year}-12-31'),
                  fact('us-gaap:InventoryNet',inventory,f'{year}-12-31')]
    facts.append(fact('us-gaap:CostOfRevenue',1000,'2018-12-31','2018-01-01'))
    return filing(facts,2018,'2018-12-31','COMPANY_2018_10K')


def test_nested_change_is_not_the_top_level_dpo_operation():
    s=spec('inventory_change',[],'',measure='other',period='2018')
    s,changes=normalize_plan(s,DPO_QUESTION,'',dpo_filing())
    q=question_equation(DPO_QUESTION,s)
    assert q and signature(q)==signature(s.formula)
    admitted,source=authorize(s,DPO_QUESTION,'',dpo_filing(),{})
    assert source['kind']=='question_definition' and admitted.claim_unit=='days'
    assert {r.name:r.period for r in s.roles}['inventory_start']=='2017'


def test_composite_average_keeps_inner_ratios_and_all_three_periods():
    question='What is the FY2018 - FY2020 3 year average of capex as a % of revenue? Round to one decimal place.'
    s=spec('capex_as_percent_of_revenue_3yr_avg',[],'',measure='percent',period='2020')
    f=filing([fact('us-gaap:PaymentsToAcquirePropertyPlantAndEquipment',10),fact('us-gaap:Revenues',100)])
    s,_=normalize_plan(s,question,'',f)
    admitted,authority=authorize(s,question,'',f,{})
    assert len(admitted.roles)==6
    assert sorted(set(r.period for r in admitted.roles))==['2018','2019','2020']
    assert '/' in admitted.formula and authority['question_composition']=='average_of_authorized_period_metrics'


@pytest.mark.parametrize('plain,combined',[(0,411000000),(999000000,0)])
def test_combined_restructuring_concept_is_selected_by_semantics_not_value(plain,combined):
    f=filing([fact('us-gaap:RestructuringCharges',plain),
              fact('us-gaap:RestructuringCostsAndAssetImpairmentCharges',combined)])
    role=RoleSpec('restructuring_costs',['Total restructuring and impairment charges'],'2022')
    b=f.bind(role,'USD millions','2022')
    assert b['concept']=='us-gaap:RestructuringCostsAndAssetImpairmentCharges'
    assert Decimal(b['value'])==Decimal(combined)/1000000


def test_registry_failure_can_reach_unique_issuer_label_with_plausibility_guard():
    f=filing([fact('issuer:PurchaseOfEquipment',100000000)],labels={'issuer:PurchaseOfEquipment':['Capital expenditures']})
    role=RoleSpec('capex',['Capital expenditures'],'2022')
    proposal=GroundedFact('capex',100,'USD millions','Capital expenditures 100',row_label='Capital expenditures')
    b=f.bind(role,'USD millions','2022',proposal)
    assert b['method']=='symbolic_label_heuristic' and Decimal(b['value'])==100
    with pytest.raises(Unresolved,match='plausibility'):
        f.bind(role,'USD millions','2022',replace(proposal,value=10000))


def test_quarter_names_prior_year_and_ytd_are_distinct():
    f=filing([fact('us-gaap:Revenues',100,'2023-07-02','2023-04-03'),
              fact('us-gaap:Revenues',250,'2023-07-02','2023-01-01'),
              fact('us-gaap:Revenues',80,'2022-07-03','2022-04-04')],
              2023,'2023-07-02','Company_2023Q2_10Q')
    for period,value in [('second quarter of 2023',100),('through the second quarter of 2023',250),('Q2 2022',80)]:
        b=f.bind(RoleSpec('revenue',period=period),'USD',period)
        assert Decimal(b['value'])==value
    with pytest.raises(Unresolved):f.bind(RoleSpec('revenue',period='Q1 2023'),'USD','Q1 2023')


def test_symbolic_authority_does_not_touch_z3_native_context(monkeypatch):
    import z3
    def forbidden(*a,**k):raise AssertionError('authority must be pure symbolic Python')
    monkeypatch.setattr(z3,'Real',forbidden)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(signature,['a+b','b+a','2*(a+b)/2','a+(b*1)']*4))
    assert len(set(results))==1
    with pytest.raises(ValueError):signature('__import__("os")')


def test_dpo_normalization_remains_candidate_independent_end_to_end():
    class Scripted:
        def __init__(self,value):self.value=value
        def chat(self,messages,stage='unknown',**kw):
            if stage=='question_decomposition':return json.dumps({'metric':'inventory_change','roles':[],'formula':'','claim_unit':'other'})
            if stage=='claim_value_parse':return json.dumps({'claimed_value':self.value,'claimed_unit':'other'})
            raise AssertionError(stage)
    a=PaperVerifier(Scripted(54.21)).verify(DPO_QUESTION,'54.21 days','',dpo_filing())
    b=PaperVerifier(Scripted(54.22)).verify(DPO_QUESTION,'54.22 days','',dpo_filing())
    assert a['status']=='VERIFIED' and b['status']=='VIOLATED'
    assert a['audit']==b['audit'] and a['audit']['repair_attempts']==0


def test_pilot_profile_cannot_launch_full_run(tmp_path,monkeypatch,capsys):
    import sys
    from vf_repro.runner import main
    config=tmp_path/'configs/pilot.json';config.parent.mkdir()
    config.write_text(json.dumps({'scope':'verifin-main-user-backbone','run_mode':'diagnostic_pilot',
        'datasets':['FinanceBench'],'backbone_override':{'source':'explicit_user_request','requested_model':'gpt-5.6-sol'},
        'models':{'GPT-5.6-Sol':{'model':'gpt-5.6-sol'}}}),encoding='utf-8')
    monkeypatch.setattr(sys,'argv',['verifin','run','--config',str(config)])
    with pytest.raises(SystemExit) as exc:main()
    assert exc.value.code==2
    assert 'pilot_profile_cannot_start_a_full_run' in capsys.readouterr().err


def test_reference_days_unit_is_derived_from_the_question_without_relaxing_precision():
    from vf_repro.scoring import correctness
    row={'dataset':'FinanceBench','question':DPO_QUESTION,'gold':{'answer':'42.69','unit':None}}
    assert correctness(row,{'claimed_value':'42.69','claimed_unit':'days'}) is True
    assert correctness(row,{'claimed_value':'44.13','claimed_unit':'days'}) is False
    assert correctness(row,{'claimed_value':'42.70','claimed_unit':'days'}) is False


def test_unparsed_explicit_definition_never_falls_back_to_a_registry_formula():
    f=filing([fact('us-gaap:AssetsCurrent',200),fact('us-gaap:LiabilitiesCurrent',100)])
    s=spec('current_ratio',[RoleSpec('current_assets',period='2022'),RoleSpec('current_liabilities',period='2022')],
           'current_assets / current_liabilities')
    with pytest.raises(Unresolved,match='unparsed_explicit_question_definition'):
        authorize(s,'Current ratio is defined as: an undisclosed custom adjustment.','',f,{})


def test_question_ppe_abbreviation_is_resolved_from_semantic_concepts():
    roles=[RoleSpec('revenue',period='2019'),RoleSpec('ppe_start',period='2018'),RoleSpec('ppe_end',period='2019')]
    s=spec('fixed_asset_turnover_ratio',roles,'revenue / ((ppe_start + ppe_end) / 2)',period='2019')
    q='Fixed asset turnover ratio is defined as: FY2019 revenue / (average PP&E between FY2018 and FY2019). Round to two decimal places.'
    assert signature(question_equation(q,s))==signature(s.formula)


def test_explicit_iso_currency_output_preserves_its_requested_scale():
    f=filing([fact('us-gaap:AssetsCurrent',200,currency='SEK')])
    assert role_measure(RoleSpec('current_assets'),'SEK billions',f)=='SEK billions'


def test_extra_average_role_does_not_replace_single_year_ppe_or_require_binding(monkeypatch):
    import vf_repro.pipeline
    q='Fixed asset turnover ratio is defined as: FY2019 revenue / (average PP&E between FY2018 and FY2019). Round to two decimal places.'
    s=spec('fixed_asset_turnover_ratio',[
        RoleSpec('revenue',period='FY2019'),RoleSpec('ppe',period='FY2018-FY2019 average'),
        RoleSpec('ppe_start',period='FY2018'),RoleSpec('ppe_end',period='FY2019')],
        'revenue / average_ppe',period='2019')
    monkeypatch.setattr(vf_repro.pipeline,'decompose_question',lambda *a,**k:s)
    f=filing([fact('us-gaap:Revenues',1000,'2019-12-31','2019-01-01'),
              fact('us-gaap:PropertyPlantAndEquipmentNet',100,'2018-12-31'),
              fact('us-gaap:PropertyPlantAndEquipmentNet',200,'2019-12-31')],2019,'2019-12-31','COMPANY_2019_10K')
    class Client:
        def chat(self,messages,stage='unknown',**kw):
            assert stage=='claim_value_parse'
            return '{"claimed_value":6.67,"claimed_unit":"ratio"}'
    r=PaperVerifier(Client()).verify(q,'6.67','',f)
    assert r['status']=='VERIFIED'
    assert {b['role'] for b in r['audit']['bindings']}=={'revenue','ppe_start','ppe_end'}
