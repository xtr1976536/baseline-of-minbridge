"""Reproducible narrow fixes to official release, saved separately from upstream."""
import sys,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1]
def install():
 if getattr(install,"installed",False):
  import agents.workflow
  return agents.workflow
 sys.path.insert(0,str(R/'vendor/gbfr'))
 import agents.edges as edges
 import agents.workflow as workflow
 from operators.EvidenceSeeking import EvidenceSeekingOperator
 # Official router can return multipath_compute but workflow omitted the destination.
 # Alias propagation was discarded in EvidenceSeeking.run: use explicit passed aliases.
 import inspect
 source=inspect.getsource(EvidenceSeekingOperator.run)
 source=source.replace('            aliases = []','            aliases = sg.get("aliases", [])')
 import textwrap
 namespace={}
 module=sys.modules[EvidenceSeekingOperator.__module__]
 exec(textwrap.dedent(source),vars(module),namespace)
 EvidenceSeekingOperator.run=namespace['run']
 # Fix the mapping in an isolated generated module, without modifying pinned files.
 source=(R/'vendor/gbfr/agents/workflow.py').read_text()
 source=source.replace('"evidence_seeking": "evidence_seeking",\n        "error": "error"\n    })','"evidence_seeking": "evidence_seeking",\n        "multipath_compute": "multipath_compute",\n        "error": "error"\n    })',1)
 # This repair only fixes a crash; it does not supply missing paper verification.
 namespace=vars(workflow)
 code=compile(source,str(R/'vendor/gbfr/agents/workflow.py'),'exec')
 exec(code,namespace)
 # Recursive cache must include every constraint attribute, not only metric name.
 from agents.nodes import NodeFactory
 import json
 def scoped(metric,constraints):
  return json.dumps([metric,constraints],sort_keys=True,ensure_ascii=False)
 method=inspect.getsource(NodeFactory._compute_indicator_recursive)
 method=method.replace('if indicator in self.indicator_cache:', 'cache_id = self._scoped_key(indicator, constraints)\n        if cache_id in self.indicator_cache:')
 method=method.replace('self.indicator_cache[indicator]','self.indicator_cache[cache_id]')
 method="\n".join("        cache_key = cache_id" if line.strip().startswith("cache_key = f") else line for line in method.splitlines())
 namespace={};module=sys.modules[NodeFactory.__module__]
 exec(textwrap.dedent(method),vars(module),namespace)
 NodeFactory._compute_indicator_recursive=namespace['_compute_indicator_recursive']
 NodeFactory._scoped_key=staticmethod(scoped)
 # Prepopulating by metric alone cannot be correct for repeated metrics across scopes.
 method=inspect.getsource(NodeFactory.multipath_compute_node)
 method=method.replace('self.indicator_cache[item.metric] = item.value','self.indicator_cache[self._scoped_key(item.metric, item.constraints.model_dump())] = item.value')
 namespace={};exec(textwrap.dedent(method),vars(module),namespace)
 NodeFactory.multipath_compute_node=namespace['multipath_compute_node']
 # Add graph aliases to evidence requests, without changing the extraction prompt.
 original_factory=workflow.create_operators
 def create_operators(config):
  ops=original_factory(config)
  if ops['kg'] is None:raise RuntimeError('FMKG unavailable; no graph-free fallback permitted')
  original_run=ops['seeker'].run
  def seek(context,subgoals):
   enriched=[]
   for goal in subgoals:
    goal=dict(goal);term=ops['kg'].get_term_by_name(goal['metric'])
    if term:goal['aliases']=term.get('aliases_en',[])+term.get('aliases_zh',[])+term.get('aliases_abbr',[])
    enriched.append(goal)
   return original_run(context,enriched)
  ops['seeker'].run=seek
  return ops
 workflow.create_operators=create_operators
 install.installed=True
 return workflow
if __name__=='__main__':
 install(); print('Routing and passed-alias propagation fixes installed; core audit remains NOT READY')
