"""Extract official prompts/builders without executing argparse, API code or main loops."""
import ast,hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];VENDOR=ROOT/'vendor'
TASKS={'finqa':('run_finqa.py','finqa_test.json','prompt_4shot',512), 'convfinqa':('run_convfinqa.py','convfinqa_dev.json','prompt_4shot',512), 'tatqa':('run_tatqa.py','tatqa_dev.json','prompt_8shot',256)}
def official(task):
 script,data,prompt_name,budget=TASKS[task];source=(VENDOR/script).read_text();tree=ast.parse(source)
 selected=[]
 for node in tree.body:
  if isinstance(node,ast.FunctionDef) and node.name=='create_reader_request_processed':selected.append(node)
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==prompt_name for t in node.targets):selected.append(node)
 namespace={'Dict':dict,'Any':object}
 exec(compile(ast.Module(body=selected,type_ignores=[]),script,'exec'),namespace)
 data_path=VENDOR/'data'/data;rows=json.loads(data_path.read_text())
 return namespace[prompt_name],namespace['create_reader_request_processed'],rows,{'script':script,'script_sha256':hashlib.sha256(source.encode()).hexdigest(),'data':data,'data_sha256':hashlib.sha256(data_path.read_bytes()).hexdigest(),'count':len(rows),'max_tokens':budget,'temperature':0.0,'top_p':1,'stop':['\n\n'],'n':1}
def guard(code):
 """Reject obvious filesystem/network/dynamic-code access before official execution.
 This is a compatibility guard, not a hostile-code security boundary.
 """
 tree=ast.parse(code)
 forbidden={'open','exec','eval','compile','__import__','globals','locals','getattr','setattr','delattr','input','breakpoint','exit','quit'}
 for n in ast.walk(tree):
  if isinstance(n,ast.Name) and (n.id in forbidden or n.id.startswith('__')):raise ValueError('Blocked name '+n.id)
  if isinstance(n,ast.Attribute) and (n.attr.startswith('_') or n.attr in ['system','popen','load','save','tofile','fromfile','memmap','read','write']):raise ValueError('Blocked attribute '+n.attr)
  if isinstance(n,(ast.Import,ast.ImportFrom)):
   names=[a.name for a in n.names] if isinstance(n,ast.Import) else [n.module or '']
   if any(s.split('.')[0] not in {'math','sympy','statistics','numpy'} for s in names):raise ValueError('Blocked import')
 return code
