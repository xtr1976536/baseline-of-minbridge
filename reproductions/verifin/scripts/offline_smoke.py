"""Paper Figure 3 with primary-source Apple XBRL and scripted LLM responses.

This is an integration check, never an experiment accuracy estimate.
"""
from pathlib import Path
import copy
import json
from vf_repro.common import read_jsonl,write_json
from vf_repro.grounding import Filing
from vf_repro.pipeline import PaperVerifier

ROOT=Path(__file__).resolve().parents[1]

class Scripted:
    def __init__(self,number):self.number=number
    def chat(self,messages,stage='unknown',**kwargs):
        if stage=='question_decomposition':
            return json.dumps({'verifiable':'true','metric':'operating_expenses','formula':'research_and_development + selling_general_and_administrative',
                'roles':[{'name':'research_and_development','period':'2025','aliases':['Research and Development Expense']},
                         {'name':'selling_general_and_administrative','period':'2025','aliases':['Selling General and Administrative Expense']}],
                'claim_unit':'USD millions','formula_source':'document_derived'})
        if stage=='fact_extraction':return '{"found":false,"reason":"use independently filed XBRL"}'
        if stage=='claim_value_parse':return json.dumps({'claimed_value':self.number,'claimed_unit':'USD millions'})
        raise AssertionError(stage)

row=read_jsonl(ROOT/'data/main/XBRLFiling.jsonl')[0]
filing=Filing.load(ROOT/'data/filings/AAPL_2025_10K.json')
results={}
for name,value in [('paper_correct_claim',62151),('incorrect_claim',62000)]:
    results[name]=PaperVerifier(Scripted(value)).verify(row['question'],str(value)+' million USD',row['context'],filing)
missing=Filing(copy.deepcopy(filing.data))
missing.data['facts']=[f for f in missing.data['facts'] if f['concept']!='us-gaap:ResearchAndDevelopmentExpense']
results['missing_operand']=PaperVerifier(Scripted(62151)).verify(row['question'],'62151 million USD',row['context'],missing)
expected={'paper_correct_claim':'VERIFIED','incorrect_claim':'VIOLATED','missing_operand':'ABSTAIN'}
assert {k:r['status'] for k,r in results.items()}==expected,results
write_json(ROOT/'research/offline_smoke.json',{'scripted_LLM':True,'primary_source_facts':True,
    'main_experiment_results':False,'results':results})
print(json.dumps(expected))
