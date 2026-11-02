import ast,json,signal,sys
sys.dont_write_bytecode=True
r=json.load(sys.stdin);code=r['code'];code=code.split('\n\n\n')[0].strip()+'\n';code=code.replace('The answer is','').strip()+'\n'
def timeout(*args):raise TimeoutError('1 second execution deadline')
try:
 tree=ast.parse(code)
 for n in ast.walk(tree):
  if isinstance(n,ast.Name) and (n.id.startswith('__') or n.id in {'open','exec','eval','compile','input','getattr','setattr','globals','locals','__import__'}):raise ValueError('Blocked access')
  if isinstance(n,ast.Attribute) and n.attr.startswith('_'):raise ValueError('Blocked attribute')
  if isinstance(n,ast.Import) and any(a.name.split('.')[0] not in {'math','fractions','decimal','statistics','sympy'} for a in n.names):raise ValueError('Blocked import')
  if isinstance(n,ast.ImportFrom) and (n.module or '').split('.')[0] not in {'math','fractions','decimal','statistics','sympy'}:raise ValueError('Blocked import')
 signal.signal(signal.SIGALRM,timeout);signal.alarm(1)
 ns={};exec(compile(tree,'generated','exec'),ns);value=str(ns['solution']());signal.alarm(0)
 print(json.dumps({'value':value,'status':'executed'}))
except Exception as e:print(json.dumps({'value':None,'status':'execution_failed','error':type(e).__name__+': '+str(e)}))
