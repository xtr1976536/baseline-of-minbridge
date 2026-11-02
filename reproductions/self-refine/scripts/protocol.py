"""Execute original GSM class and loop ASTs; transport only injected."""
import ast,hashlib,json,sys,types
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];VENDOR=ROOT/'vendor'
def extract(path,names,namespace):
 tree=ast.parse(path.read_text());nodes=[]
 for n in tree.body:
  if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names:
   n.decorator_list=[];nodes.append(n)
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),namespace)
def instantiate(call):
 class API:
  @staticmethod
  def get_first_response(output):return output
 API.call=staticmethod(call)
 ns={'openai_api':types.SimpleNamespace(OpenaiAPIWrapper=API),'print':lambda *args,**kwargs:None}
 extract(VENDOR/'src/utils.py',{'Prompt'},ns)
 extract(VENDOR/'src/gsm/task_init.py',{'GSMInit'},ns)
 extract(VENDOR/'src/gsm/feedback.py',{'GSMFeedback'},ns)
 ns['ENGINE']='gpt-5.6-sol'
 extract(VENDOR/'src/gsm/run.py',{'iterative_gsm'},ns)
 return ns['iterative_gsm']
def check_corr(result,gold):
 ns={};extract(VENDOR/'src/gsm/gsm_selfref_eval.py',{'check_corr'},ns)
 return ns['check_corr'](str(result),str(gold))
def manifest():
 paths=['src/utils.py','src/gsm/run.py','src/gsm/task_init.py','src/gsm/feedback.py','src/gsm/gsm_selfref_eval.py','data/tasks/gsm/gsm.jsonl','data/prompt/gsm/init.txt','data/prompt/gsm/feedback.txt']
 return {p:hashlib.sha256((VENDOR/p).read_bytes()).hexdigest() for p in paths}
