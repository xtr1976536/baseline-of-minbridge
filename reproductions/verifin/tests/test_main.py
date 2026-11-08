import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
import httpx
import numpy as np
import pytest
import z3
from verifiqa.agent.types import ClaimSpec,RoleSpec,GroundedFact
from verifiqa.generation.llm_client import ChatMessage
from verifiqa.types import EvidenceChunk,RetrievalPlan,RetrievalFact
from vf_repro.authority import authorize
from vf_repro.client import Client,ApiError
from vf_repro.common import read_jsonl,write_json,write_jsonl,MODELS,DATASETS
from vf_repro.grounding import Filing,Unresolved,conversion,reporting_tolerance
from vf_repro.pipeline import PaperVerifier
from vf_repro.retrieval import Retriever
from vf_repro.runner import recover,check
from vf_repro.scoring import summarize,correctness
from vf_repro.solver import verify,Unsupported

def fixture_filing():
    facts=[]
    for concept,value in [('ResearchAndDevelopmentExpense','34550000000'),('SellingGeneralAndAdministrativeExpense','27601000000')]:
        facts.append({'id':concept+'2025','concept':'us-gaap:'+concept,'value':value,'unit':'iso4217:USD',
                      'decimals':'-6','period':{'start_date':'2024-09-29','end_date':'2025-09-27','instant':'','dimensions':[]}})
    return Filing({'doc_name':'AAPL_2025_10K','accession':'0000320193-25-000079','fiscal_year':2025,
        'period_end':'2025-09-27','source_url':'https://www.sec.gov/Archives/example.xml',
        'instance_sha256':'fixture','calculation_sha256':'fixture','facts':facts,'labels':{},
        'calculations':[{'parent':'us-gaap:OperatingExpenses','role':'income_statement',
            'children':[{'concept':f['concept'],'weight':'1'} for f in facts]}]})

def fixture_spec():
    return ClaimSpec(metric='operating_expenses',formula='research_and_development + selling_general_and_administrative',
        roles=[RoleSpec(name='research_and_development',aliases=['Research and Development Expense'],period='2025'),
               RoleSpec(name='selling_general_and_administrative',aliases=['Selling General and Administrative Expense'],period='2025')],
        claim_unit='USD millions',tolerance=.5,formula_source='document_derived',period='2025')

QUESTION="What were Apple's FY2025 total operating expenses, in USD millions? Round to the nearest million."
EVIDENCE='All amounts in millions of USD.\nResearch and Development Expense 34,550\nSelling General and Administrative Expense 27,601\nOperating Expenses [redacted]'

class Scripted:
    def __init__(self,claim=62151): self.claim=claim;self.calls=[]
    def chat(self,messages,stage='unknown',**kwargs):
        self.calls.append((stage,messages[0].content))
        if stage=='question_decomposition':
            return json.dumps({'verifiable':'true','metric':'operating_expenses','formula':'research_and_development + selling_general_and_administrative',
                'roles':[{'name':r.name,'aliases':r.aliases,'period':r.period} for r in fixture_spec().roles],
                'claim_unit':'USD millions','formula_source':'document_derived'})
        if stage=='fact_extraction': return '{"found":false,"reason":"bind to filed facts"}'
        if stage=='claim_value_parse': return json.dumps({'claimed_value':self.claim,'claimed_unit':'USD millions'})
        raise AssertionError(stage)

@pytest.mark.parametrize('answer,question,claim,claim_unit',[
    ('JnJ will gain approximately $20 billion from the separation.',
     'What gain will JnJ make from the separation?', '20','USD billions'),
    ('50%','What was the ratio?', '0.5','ratio'),
    ('$1616.00','What were net receivables in USD millions?', '1616','USD millions'),
])
def test_explicit_label_units_precede_question_heuristics_without_losing_magnitude(answer,question,claim,claim_unit):
    row={'dataset':'FinanceBench','question':question,'gold':{'answer':answer,'unit':None}}
    result={'claimed_value':claim,'claimed_unit':claim_unit}
    assert correctness(row,result) is True
    assert correctness(row,{**result,'claimed_value':str(Decimal(claim)+1)}) is False

@pytest.mark.parametrize('candidate,status',[(62151,'VERIFIED'),(62151.5,'VERIFIED'),(62151.50001,'VIOLATED'),(0,'VIOLATED')])
def test_paper_example_end_to_end(candidate,status):
    llm=Scripted(candidate)
    result=PaperVerifier(llm).verify(QUESTION,'The claimed final answer is '+str(candidate)+' million USD.',EVIDENCE,fixture_filing())
    assert result['status']==status, result
    assert result['audit']['repair_attempts']==0
    assert len(result['audit']['bindings'])==2
    assert result['audit']['formula_authority']['kind']=='filing_calculation_linkbase'
    assert not any(stage=='fact_extraction' for stage,_ in llm.calls)
    assert Decimal(result['audit']['tolerance'])==Decimal('0.5')
    assert not any(str(candidate)+' million USD' in prompt for stage,prompt in llm.calls if stage!='claim_value_parse')

def test_candidate_changes_do_not_change_authority_facts_or_tolerance():
    a=PaperVerifier(Scripted(62151)).verify(QUESTION,'62151',EVIDENCE,fixture_filing())
    b=PaperVerifier(Scripted(999999999)).verify(QUESTION,'999999999',EVIDENCE,fixture_filing())
    assert a['audit']==b['audit']

def test_missing_fact_abstains_and_does_not_parse_candidate():
    f=fixture_filing();f.data['facts'].pop()
    llm=Scripted()
    r=PaperVerifier(llm).verify(QUESTION,'62151',EVIDENCE,f)
    assert r['status']=='ABSTAIN'
    assert not any(s=='claim_value_parse' for s,_ in llm.calls)

def test_unusable_model_plan_abstains_but_transport_failure_propagates():
    class Malformed:
        def chat(self,*a,**k):return 'invalid JSON'
    assert PaperVerifier(Malformed()).verify(QUESTION,'62151',EVIDENCE,fixture_filing())['status']=='ABSTAIN'
    class Offline:
        def chat(self,*a,**k):raise ApiError('transport_retries_exhausted')
    with pytest.raises(ApiError):PaperVerifier(Offline()).verify(QUESTION,'62151',EVIDENCE,fixture_filing())

def test_registry_bindings_override_wrong_extraction():
    f=fixture_filing()
    role=RoleSpec(name='research_and_development',concept=f.data['facts'][0]['concept'],period='2025')
    wrong=GroundedFact(name=role.name,value=999,unit='USD millions',source_quote='999')
    assert Decimal(f.bind(role,'USD millions','2025',wrong)['value'])==Decimal(34550)

def test_conflicting_duplicate_facts_abstain():
    f=fixture_filing(); duplicate=dict(f.data['facts'][0]);duplicate['value']='1';f.data['facts'].append(duplicate)
    with pytest.raises(Unresolved): f.bind(RoleSpec(name='r',concept=duplicate['concept'],period='2025'),'USD millions','2025')

def test_wrong_unit_and_year_never_bind():
    f=fixture_filing();r=RoleSpec(name='r',concept=f.data['facts'][0]['concept'],period='2024')
    with pytest.raises(Unresolved): f.bind(r,'USD millions','2024')
    with pytest.raises(Unresolved): f.bind(replace(r,period='2025'),'shares','2025')

def test_heuristic_ties_abstain():
    f=fixture_filing();f.data['labels']={x['concept']:['unknown expense'] for x in f.data['facts']}
    r=RoleSpec(name='unregistered_role',aliases=['unknown expense'],period='2025')
    p=GroundedFact(name=r.name,value=30000,unit='USD millions',source_quote='30000',row_label='unknown expense')
    with pytest.raises(Unresolved):f.bind(r,'USD millions','2025',p)

def test_no_formula_authority_cannot_be_claimed_by_a_source_string():
    s=ClaimSpec('made_up_metric','a+b',[RoleSpec('a',period='2025'),RoleSpec('b',period='2025')],'USD millions',.5,'document_derived',period='2025')
    with pytest.raises(Unresolved):authorize(s,'What is the made up metric for FY2025?','a 1 b 2',fixture_filing(),{})

def test_registry_formula_selection_has_no_claim_input():
    s=ClaimSpec('current_ratio','current_assets / current_liabilities',[RoleSpec('current_assets',period='2025'),RoleSpec('current_liabilities',period='2025')],'ratio',.005,'policy_registry',period='2025')
    extracted={r.name:GroundedFact(r.name,1,'USD millions','',period='2025') for r in s.roles}
    result,source=authorize(s,'What is the current ratio for 2025?','',fixture_filing(),extracted)
    assert source['kind']=='curated_metric_registry'
    assert result.formula=='current_assets / current_liabilities'

@pytest.mark.parametrize('output_unit',['USD millions','USD billions'])
def test_registry_does_not_apply_a_second_display_unit_conversion(output_unit):
    s=ClaimSpec('capital_expenditure','capex',[RoleSpec('capex',period='2025')],output_unit,.005,'policy_registry',period='2025')
    extracted={'capex':GroundedFact('capex',1,'USD millions','',period='2025')}
    result,source=authorize(s,'What was capital expenditure in FY2025?','',fixture_filing(),extracted)
    assert result.formula=='capex' and source['kind']=='curated_metric_registry'

def test_unsat_core_and_standalone_trace():
    result=verify('a+b',{'a':'1.1','b':'2.2'},'9','.01')
    assert result['status']=='VIOLATED' and result['unsat_core']
    # z3 SMT parser ignores commands; assertions plus tracking assumptions reproduce UNSAT.
    solver=z3.Solver();solver.from_string(result['smtlib'])
    assumptions=[z3.Bool(x) for x in ['filing_a','filing_b','authorized_formula','claim_lower_bound','claim_upper_bound']]
    assert solver.check(*assumptions)==z3.unsat

def test_zero_denominator_is_abstention():
    assert verify('a/b',{'a':'1','b':'0'},0,'.1')['status']=='ABSTAIN'

def test_exact_decimal_boundary():
    assert verify('a+b',{'a':'.1','b':'.2'},'.3','0')['status']=='VERIFIED'

def test_cagr_is_algebraic_with_unique_positive_root():
    assert verify('cagr_percent(end,start,3)',{'end':'1331','start':'1000'},'10','.000001')['status']=='VERIFIED'
    assert verify('cagr_percent(end,start,3)',{'end':'1331','start':'1000'},'11','.000001')['status']=='VIOLATED'
    assert verify('cagr_percent(end,start,3)',{'end':'1331','start':'0'},'10','.01')['status']=='ABSTAIN'

def test_parse_xbrl_instance_preserves_provenance_and_per_share_units(tmp_path):
    from vf_repro.assets import parse_filing
    p=tmp_path/'instance.xml'
    p.write_text('''<xbrl xmlns="http://www.xbrl.org/2003/instance" xmlns:us-gaap="http://fasb.org/us-gaap/2025" xmlns:iso4217="http://www.xbrl.org/2003/iso4217"><context id="c"><entity><identifier scheme="https://www.sec.gov/CIK">320193</identifier></entity><period><startDate>2024-09-29</startDate><endDate>2025-09-27</endDate></period></context><unit id="u"><divide><unitNumerator><measure>iso4217:USD</measure></unitNumerator><unitDenominator><measure>shares</measure></unitDenominator></divide></unit><us-gaap:EarningsPerShareBasic contextRef="c" unitRef="u" decimals="2" id="f1">6.12</us-gaap:EarningsPerShareBasic></xbrl>''',encoding='utf-8')
    f=parse_filing({'doc_name':'d','accession':'a','doc_link':'https://example.org/source'},p)
    assert len(f['facts'])==1 and f['facts'][0]['id']=='f1'
    assert f['facts'][0]['unit']=='iso4217:USD/shares'
    assert f['facts'][0]['value']=='6.12'

@pytest.mark.parametrize('formula',['__import__("os")','a.__class__','a[0]','a**.5'])
def test_unsafe_or_unsupported_formula_is_rejected(formula):
    with pytest.raises(Unsupported):verify(formula,{'a':1},1,0)

def test_precision_is_candidate_independent():
    assert reporting_tolerance('What ratio?','ratio',[], 'USD millions')==('.005','reproduction_assumption_derived_ratio_two_decimals')
    assert conversion('USD billions','USD millions')==1000

class Encoder:
    def encode(self,texts,**kwargs): return np.array([[1.,0.] for _ in texts])
class Reranker:
    def predict(self,pairs): return [1. if 'Revenue' in text else 0. for _,text in pairs]

def test_hybrid_retrieval_document_scope_and_reranking(tmp_path):
    cfg={'embedding_model':'fake','embedding_revision':'fixed','lexical_weight':.2,'first_stage_k':30,'top_k':1}
    r=Retriever(cfg,tmp_path,Encoder(),Reranker())
    chunks=[EvidenceChunk('a','correct',0,'Revenue 1'),EvidenceChunk('b','wrong',0,'Revenue 999'),EvidenceChunk('c','correct',0,'Unrelated')]
    out,trace=r.retrieve('Revenue?',RetrievalPlan(facts=[RetrievalFact('revenue',['Revenue'])]),chunks,'correct')
    assert [x.chunk_id for x in out]==['a']
    assert all(x['id']!='b' for x in trace[0]['first_stage'])

def test_embedding_cache_keys_include_content(tmp_path):
    cfg={'embedding_model':'fake','embedding_revision':'fixed','lexical_weight':.2,'first_stage_k':30,'top_k':1}
    r=Retriever(cfg,tmp_path,Encoder(),Reranker())
    for text in ['Revenue 1','Revenue 2']:
        r.retrieve('Revenue?',RetrievalPlan(),[EvidenceChunk('a','d',0,text)],'d')
    assert len(list(tmp_path.glob('*.npy')))==2

def test_gpt_payload_and_request_cache_are_secret_free(tmp_path,monkeypatch):
    monkeypatch.setenv('TEST_VF_KEY','test-secret')
    seen=[]
    def handler(request):
        seen.append(json.loads(request.content))
        return httpx.Response(200,json={'model':'gpt-5.5','choices':[{'message':{'content':'{"ok":true}'},'finish_reason':'stop'}]})
    cfg={'provider':'openai-compatible','model':'gpt-5.5','base_url':'https://example.test/v1','api_key_env':'TEST_VF_KEY',
        'max_tokens':8192,'temperature':None,'token_parameter':'max_completion_tokens','parameters':{'reasoning_effort':'low'}}
    client=Client(cfg,tmp_path,'FinanceBench',httpx.MockTransport(handler))
    for _ in range(2):client.chat([ChatMessage('user','test')])
    assert len(seen)==1 and seen[0]['max_completion_tokens']==8192 and 'temperature' not in seen[0]
    assert 'test-secret' not in next(tmp_path.glob('*.json')).read_text()

def test_truncated_response_is_error(tmp_path,monkeypatch):
    monkeypatch.setenv('TEST_VF_KEY','test-secret')
    client=Client({'provider':'openai-compatible','model':'test','base_url':'https://example.test/v1','api_key_env':'TEST_VF_KEY'},tmp_path,'XBRLFiling',
        httpx.MockTransport(lambda r:httpx.Response(200,json={'choices':[{'message':{'content':'123'},'finish_reason':'length'}]})))
    with pytest.raises(ApiError,match='truncated'):client.chat([ChatMessage('user','test')])

def test_metric_denominators_preserve_unknown_errors_and_missing():
    rows=[{'id':str(i),'result':{'status':status},'correct':correct} for i,(status,correct) in enumerate([
        ('VERIFIED',True),('VERIFIED',False),('VIOLATED',False),('VIOLATED',True),('ABSTAIN',None),('VERIFIED',None),('ERROR',None)])]
    m=summarize(rows,8)
    assert m['coverage']==5/8 and m['precision']==.5 and m['accuracy']==.5
    assert m['Abs']==1 and m['errors']==1 and m['missing']==1 and not m['complete']

def test_torn_last_line_recovery_and_interior_corruption(tmp_path):
    p=tmp_path/'predictions.jsonl';p.write_bytes(b'{"id":"1"}\n{"id":')
    assert recover(p)==[{'id':'1'}]
    p.write_bytes(b'bad\n{"id":"2"}\n')
    with pytest.raises(ValueError):recover(p)

@pytest.mark.parametrize('sample_workers',[1,4])
def test_entire_12_cell_runner_and_resume_without_gold_leakage(tmp_path,monkeypatch,sample_workers):
    from vf_repro.runner import run_cell
    import vf_repro.client
    class FullScripted(Scripted):
        def chat(self,messages,stage='unknown',**kwargs):
            assert 'POISON_GOLD' not in messages[0].content
            if stage=='retrieval_plan':
                return '{"metric":"operating_expenses","facts":[{"name":"operating_expenses","aliases":["Operating Expenses"],"period":"2025","statement":"income"}]}'
            if stage=='answer_generation':return '{"answer":"The total is 62151 million USD."}'
            return super().chat(messages,stage=stage,**kwargs)
    clients=[]
    def factory(*a,**kw):
        c=FullScripted();clients.append(c);return c
    monkeypatch.setattr(vf_repro.client,'Client',factory)
    cfg={'scope':'verifin-v3-table4-only','output_dir':'runs/main',
         'concurrency':{'samples':sample_workers,'api_requests':2},
         'datasets':['XBRLFiling','FinanceBench'],
         'models':{m:{'provider':'openai-compatible','model':m,'base_url':'https://example.test/v1'} for m in MODELS},
         'retrieval':{'embedding_model':'fake','embedding_revision':'fixed','lexical_weight':.2,'first_stage_k':30,'top_k':10,'chunk_words':200,'chunk_overlap_words':40}}
    for dataset in cfg['datasets']:
        row={'id':'paper-example','dataset':dataset,'question':QUESTION,'doc_name':'AAPL_2025_10K','context':EVIDENCE,
             'gold':{'answer':'POISON_GOLD','unit':'USD millions'}}
        write_jsonl(tmp_path/'data/main'/(dataset+'.jsonl'),[{**row,'id':f'paper-example-{i}'} for i in range(3)])
    write_json(tmp_path/'data/filings/AAPL_2025_10K.json',fixture_filing().data)
    write_json(tmp_path/'data/corpus/AAPL_2025_10K.json',{'pages':[{'page':0,'text':EVIDENCE}]})
    write_json(tmp_path/'data/assets.lock.json',{'files':{}})
    retriever=Retriever(cfg['retrieval'],tmp_path/'embeddings',Encoder(),Reranker())
    for model in MODELS:
        for dataset in cfg['datasets']:
            result=run_cell(tmp_path,cfg,dataset,model,retriever)
            assert result['complete'] and result['unresolved_decided']==3
            assert result['coverage']==1 and result['precision'] is None
            again=run_cell(tmp_path,cfg,dataset,model,retriever)
            assert again==result
            journal=read_jsonl(tmp_path/'runs/main'/model/dataset/'predictions.jsonl')
            assert [r['id'] for r in journal]==[f'paper-example-{i}' for i in range(3)]
            assert all(r['result']['status']=='VERIFIED' for r in journal)
    assert all(not c.calls for c in clients[1::2])

def test_dataset_scope_and_report_exclude_inactive_dataset(tmp_path):
    from vf_repro.runner import selected_datasets,report
    cfg={'datasets':['XBRLFiling','FinanceBench'],'output_dir':'runs/main'}
    assert selected_datasets(cfg)==['XBRLFiling','FinanceBench']
    assert selected_datasets(cfg,['FinanceBench'])==['FinanceBench']
    with pytest.raises(ValueError):selected_datasets(cfg,['TAT-DQA'])
    text=report(tmp_path,cfg).read_text(encoding='utf-8')
    assert 'TAT-DQA' not in text
    assert text.count('not run')==12

def test_explicit_gpt56_override_is_not_reported_as_a_paper_backbone(tmp_path):
    from vf_repro.runner import config_at,selected_models,report
    path=tmp_path/'configs/main.json'
    cfg={'scope':'verifin-main-user-backbone','backbone_override':{'source':'explicit_user_request','requested_model':'gpt-5.6-sol'},
         'datasets':['FinanceBench'],'models':{'GPT-5.6-Sol':{'model':'gpt-5.6-sol'}},'output_dir':'runs/test'}
    write_json(path,cfg)
    _,loaded=config_at(path)
    assert selected_models(loaded)==['GPT-5.6-Sol']
    with pytest.raises(ValueError):selected_models(loaded,['GPT-5.5'])
    text=report(tmp_path,loaded).read_text(encoding='utf-8')
    assert 'GPT-5.6-Sol' in text and 'GPT-5.5' not in text and text.count('not run')==1

def test_asset_lock_is_independent_of_inactive_dataset(tmp_path):
    from vf_repro.runner import asset_hashes
    main=tmp_path/'data/main'
    write_jsonl(main/'XBRLFiling.jsonl',[{'id':'a','doc_name':'filing_a'}])
    write_json(main/'documents.json',{'filing_a':{'source':'a'},'unused_tat':{'source':'old'}})
    write_json(main/'manifest.json',{'predictions_used':False,'datasets':{'XBRLFiling':{'n':1},'TAT-DQA':{'n':477}}})
    before=asset_hashes(tmp_path,['XBRLFiling'])
    write_json(main/'documents.json',{'filing_a':{'source':'a'},'unused_tat':{'source':'changed'}})
    write_json(main/'manifest.json',{'predictions_used':False,'datasets':{'XBRLFiling':{'n':1},'TAT-DQA':{'n':0}}})
    write_jsonl(main/'TAT-DQA.jsonl',[{'id':'unused'}])
    assert before==asset_hashes(tmp_path,['XBRLFiling'])
    write_jsonl(main/'XBRLFiling.jsonl',[{'id':'changed','doc_name':'filing_a'}])
    assert before!=asset_hashes(tmp_path,['XBRLFiling'])
