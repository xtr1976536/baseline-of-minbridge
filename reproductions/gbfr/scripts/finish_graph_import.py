"""Finish dedicated partial import with batched relationship writes, same official schema."""
import json,sys,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'vendor/gbfr'))
from utils.graph import FinanceGraph
password=json.loads((R/'.runtime/graph-env.json').read_text())['GBFR_NEO4J_PASSWORD']
g=FinanceGraph('bolt://localhost:17687','neo4j',password,data_path=str(R/'.runtime/graph-normalized.json'))
terms,concepts,categories,calc,belongs=g.read_nodes()
# All nodes were imported before the sequential relationship stage. Dedicated instance only.
n=g.g.run('MATCH (n:FinanceTerm_en) RETURN count(n)').evaluate()
assert n==7513,n
# Delete only this import's relationships to avoid duplicates from the interrupted stage.
g.g.run('MATCH ()-[r:CALCULATED_BY_EN|BELONGS_TO_EN]->() DELETE r')
for kind,label in [('Term','FinanceTerm_en'),('Concept','FinanceConcept_en')]:
 rows=[{'a':a,'b':b,'type':t} for a,b,k,t in calc if k==kind]
 for i in range(0,len(rows),500):
  g.g.run(f'UNWIND $rows AS row MATCH (a:FinanceTerm_en {{name_en:row.a}}), (b:{label} {{name_en:row.b}}) CREATE (a)-[:CALCULATED_BY_EN {{name:"Calculation Dependency",type:row.type}}]->(b)',rows=rows[i:i+500])
rows=[{'a':a,'b':b} for a,b in belongs]
for i in range(0,len(rows),500):
 g.g.run('UNWIND $rows AS row MATCH (a:FinanceTerm_en {name_en:row.a}), (b:FinanceCategory_en {name_en:row.b}) CREATE (a)-[:BELONGS_TO_EN {name:"Belongs To Category"}]->(b)',rows=rows[i:i+500])
report={'terms':n,'concepts':len(concepts),'categories':len(categories),'dependency_relationships':len(calc),'category_relationships':len(belongs),'normalized_sha256':hashlib.sha256((R/'.runtime/graph-normalized.json').read_bytes()).hexdigest(),'status':'import_complete_derived_release_graph'}
(R/'results/graph_import.json').write_text(json.dumps(report,indent=2))
with (R/'.runtime/import-normalized.log').open('a') as f:f.write('\n金融知识图谱构建完成\n')
print(report)
