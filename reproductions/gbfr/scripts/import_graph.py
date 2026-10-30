import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'vendor/gbfr'))
from utils.graph import FinanceGraph
settings=json.loads((R/'.runtime/graph-env.json').read_text())
# Release contains failed-generation objects and repeated names. Merge all unique
# formulas/aliases/dependencies per name without inventing terms or formulas.
source=json.loads((R/'vendor/gbfr/knowledge_base/term_en_final.json').read_text())
merged={}
for item in source:
 if 'term_en' not in item:continue
 name=item['term_en']['name']
 if name not in merged:
  merged[name]=json.loads(json.dumps(item));continue
 target=merged[name]
 for key in ['related_concepts_en','category_en']:
  for value in item.get(key,[]):
   if value not in target.setdefault(key,[]):target[key].append(value)
 for key,values in item['term_en'].get('aliases',{}).items():
  for value in values:
   if value not in target['term_en'].setdefault('aliases',{}).setdefault(key,[]):target['term_en']['aliases'][key].append(value)
 for i,formula in enumerate(item.get('formula_en',[])):
  codes=item.get('code',[]);code=codes[i] if i<len(codes) else ''
  pairs=list(zip(target.get('formula_en',[]),target.get('code',[])))
  if (formula,code) not in pairs:
   target.setdefault('formula_en',[]).append(formula);target.setdefault('code',[]).append(code)
path=R/'.runtime/graph-normalized.json';path.write_text(json.dumps(list(merged.values()),ensure_ascii=False))
g=FinanceGraph('bolt://localhost:17687','neo4j',settings['GBFR_NEO4J_PASSWORD'],data_path=str(path))
# Dedicated instance, import only if empty, never delete an existing graph.
n=g.g.run('MATCH (n) RETURN count(n)').evaluate()
if n:raise RuntimeError(f'Nonempty graph ({n}); refusing duplicate import')
g.build()
print(g.g.run('MATCH (n:FinanceTerm_en) RETURN count(n)').evaluate())
