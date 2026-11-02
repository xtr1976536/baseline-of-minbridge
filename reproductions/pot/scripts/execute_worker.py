import json,sys
sys.dont_write_bytecode=True
from protocol import VENDOR,guard
sys.path.insert(0,str(VENDOR))
from tool import safe_execute,floatify_ans
r=json.load(sys.stdin);code=r['code']
try:
 guard(code)
 if r['task'] in ['finqa','convfinqa']:code=code.replace('&','_')
 ans=safe_execute(code,keys=['ans','units'] if r['task']=='tatqa' else None)
 if r['task']=='finqa':ans=floatify_ans(ans)
 elif r['task']=='convfinqa' and ans is not None:
  if isinstance(ans,dict):
   from collections import Counter
   ans=Counter(ans.values()).most_common(1)[0][0]
  elif isinstance(ans,(list,tuple)):ans=float(ans[0])
  else:ans=float(ans)
 print(json.dumps({'value':ans,'status':'executed' if ans is not None else 'execution_failed'},default=str))
except Exception as e:print(json.dumps({'value':None,'status':'rejected_or_failed','error':type(e).__name__+': '+str(e)}))
