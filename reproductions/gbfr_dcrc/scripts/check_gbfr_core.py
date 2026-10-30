"""Offline regression probes: route compilation, aliases, and unresolved core divergence."""
import sys,json
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'vendor/gbfr'))
from apply_gbfr_fixes import install
workflow=install()
from agents.edges import after_question_analysis
from operators.Base import OQAResult
from operators.EvidenceSeeking import EvidenceSeekingOperator
from types import SimpleNamespace
captured=[]
seeker=EvidenceSeekingOperator()
seeker.llm=SimpleNamespace(invoke=lambda messages: (captured.append(messages) or SimpleNamespace(content='{"found":false,"var_bindings":{},"missing_vars":["Net Income"]}')))
seeker.run('No income evidence',[{'metric':'Net Income','constraints':{},'aliases':['Net Profit']}])
assert 'Net Profit' in captured[0][1]['content']
class FakeFactory:
 def __init__(self,**kw):pass
 def __getattr__(self,name):return lambda state:{}
workflow.create_operators=lambda config:{'analyzer':None,'seeker':None,'decomposer':None,'generator':None,'executor':None,'kg':None}
workflow.NodeFactory=FakeFactory
compiled=workflow.create_graph()
assert ('question_analysis','multipath_compute') in {(e.source,e.target) for e in compiled.get_graph().edges}
assert after_question_analysis({'success':True,'oqa_result':OQAResult(reasoning_type='DirectRetrieval'),'formula_context':{'formulas':[{}]}})=='multipath_compute'
# Same metric, different year/entity/unit must not reuse a cached value.
from agents.nodes import NodeFactory
from operators.Base import EvidenceSeekingOutput, EvidenceItem, Constraints
calls=[]
def evidence(context,goals):
 c=goals[0]['constraints'];calls.append(c)
 value=1 if c['temporal_scope']=='2020' else 2
 return EvidenceSeekingOutput(found=True,var_bindings={'v1':EvidenceItem(metric='Revenue',constraints=Constraints(**c),value=value,context='Revenue',confidence=1)})
nodes=NodeFactory(None,SimpleNamespace(run=evidence),None,None,None)
a={'temporal_scope':'2020','entity_scope':'A','meta':{'unit':'USD'}}
b={**a,'temporal_scope':'2021'}
assert nodes._compute_indicator_recursive('Revenue','Revenue',a,0,2,set(),{})[1]==1
assert nodes._compute_indicator_recursive('Revenue','Revenue',b,0,2,set(),{})[1]==2
assert nodes._compute_indicator_recursive('Revenue','Revenue',a,0,2,set(),{})[1]==1
assert len(calls)==2
assert nodes._scoped_key('Revenue',a)!=nodes._scoped_key('Revenue',{**a,'meta':{'unit':'CNY'}})
report={'checks' :{'graph_route_destination':'PASS','explicit_alias_propagation':'PASS','scope_sensitive_cache':'PASS'},'readiness':'NOT_READY','blocking_core_gaps':['paper LLM cross-path judge and validated consensus absent','recursive path selection currently shallowest success','paper parallel resolution absent','one-hop upward formula rearrangement absent','safe abstention mixed with execution/API errors','paper test-data selection and exact normalization not released']}
(R/'results/core_audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
