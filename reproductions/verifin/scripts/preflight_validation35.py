"""Local retrieval checks on original filings; no claim generation or API calls."""
from pathlib import Path
from dataclasses import asdict
import json
from vf_repro.common import read_jsonl,write_json
from vf_repro.document_tables import augment_pages
from vf_repro.retrieval import Retriever,chunks_from_pages,plan_retrieval,table_labels,statement_scope
from vf_repro.grounding import tokens

root=Path(__file__).resolve().parent.parent
cfg=json.loads((root/'configs/validation35-v1.json').read_text(encoding='utf-8'))
data={r['id']:r for r in read_jsonl(root/'data/main/FinanceBench.jsonl')}
previous={r['id']:r for r in read_jsonl(root/'runs/coverage50-v3/GPT-5.6-Sol/FinanceBench/predictions.jsonl')}
retriever=Retriever(cfg['retrieval'],root/'runs/embedding-cache')
checks=[]
for sid,labels in [('financebench_id_03069',['Depreciation and amortization','Net revenue']),
    ('financebench_id_06272',['Dividends','Net income attributable to shareowners of The Coca-Cola Company']),
    ('financebench_id_10420',['TOTAL ASSETS','NET INCOME (LOSS) ATTRIBUTABLE TO THE AES CORPORATION'])]:
    row=data[sid];doc=row['doc_name']
    class CachedQuestionPlan:
        def chat(self,*args,**kwargs):return json.dumps(previous[sid]['retrieval_plan'])
    plan=plan_retrieval(row['question'],CachedQuestionPlan(),expand=True)
    corpus=json.loads((root/'data/corpus'/(doc+'.json')).read_text(encoding='utf-8'))
    pages=augment_pages(root,doc,corpus)
    chunks=chunks_from_pages(doc,pages,table_aware=True)
    selected,traces=retriever.retrieve(row['question'],plan,chunks,doc)
    rows=[label for c in selected for label in table_labels(c.text)]
    found={label:any(tokens(label)<=tokens(x) for x in rows) for label in labels}
    result={'id':sid,'doc_name':doc,'selected':[c.chunk_id for c in selected],'required_labels_covered':found,
        'primary_evidence':[c.chunk_id for c in selected if max(statement_scope(c.text,s) for s in ['cash flow','income statement','balance sheet'])>0],
        'no_provider_API_calls':True,'no_candidate_or_gold_used':True}
    checks.append(result);write_json(root/'research/validation35_preflight_retrieval.json',checks)
    print(json.dumps(result,ensure_ascii=True),flush=True)
    assert all(found.values()),('preflight_required_row_missing',sid,found)
