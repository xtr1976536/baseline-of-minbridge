import collections,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'vendor/gbfr/knowledge_base/term_en_final.json'
data=json.loads(p.read_text());names=[d['term_en']['name'] for d in data if 'term_en' in d]
report={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'release_records':len(data),'valid_term_records':len(names),'unique_term_names':len(set(names)),'paper_readme_expected_terms':7521,'invalid_record_indices':[i for i,d in enumerate(data) if 'term_en' not in d],'duplicate_term_names':{k:v for k,v in collections.Counter(names).items() if v>1},'official_import_result':'KeyError: term_en at utils/graph.py read_nodes; before nodes imported','status':'blocked_official_graph_release_requires_reconciliation; no silent deduplication or fabricated replacement'}
(R/'results/graph_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print({k:v for k,v in report.items() if k!='duplicate_term_names'})
