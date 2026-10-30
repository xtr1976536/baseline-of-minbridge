"""Paper-derived DSA deterministic executor (Sections 3.4, Appendices A-C).
Not trained DCRC weights. No Python eval/exec and no answer generation.
"""
import operator,re
from decimal import Decimal
OPS={'add':operator.add,'subtract':operator.sub,'multiply':operator.mul,'divide':operator.truediv,'exp':operator.pow,'greater':lambda a,b:'yes' if a>b else 'no'}
def number(v):
 s=str(v).strip().replace(',','').replace('$','')
 if s.startswith('(') and s.endswith(')'):s='-'+s[1:-1]
 return Decimal(s.rstrip('%'))/(100 if s.endswith('%') else 1)
def execute(ir):
 tasks=ir['tasks'];pool=ir['pool'];bound={};accepted=set();audit=[]
 for task in tasks:
  values=set()
  for evidence in pool:
   decision=evidence['decisions'].get(task,evidence['decisions'].get('ALL'))
   if decision is None:continue
   if decision['tag'] not in ('ACCEPT','REJECT'):raise ValueError('Invalid decision tag')
   audit.append({'task':task,'evidence':evidence['id'],**decision})
   if decision['tag']=='ACCEPT':
    value=number(evidence['val']);values.add(value);accepted.add(value)
  if not values:raise ValueError('MISSING: '+task)
  if len(values)>1:raise ValueError('CONFLICT: '+task)
  bound[task]=values.pop()
 results=[]
 def resolve(s):
  s=s.strip()
  if s in bound:return bound[s]
  if s.startswith('#'):
   i=int(s[1:])
   if i<0 or i>=len(results):raise ValueError('Invalid step reference')
   return results[i]
  if s.startswith('const_'):return number(s[6:].replace('m','-',1) if s[6:].startswith('m') else s[6:])
  value=number(s)
  if value not in accepted:raise ValueError('Operand not bound to accepted evidence: '+s)
  return value
 logic=ir['logic'];pos=0
 for match in re.finditer(r'([a-z_]+)\(([^()]*)\)',logic):
  if logic[pos:match.start()].strip(' ,\n'):raise ValueError('Invalid program syntax')
  op,args=match.groups();args=[resolve(s) for s in args.split(',')]
  if op not in OPS or len(args)!=2:raise ValueError('Unknown operator or arity')
  results.append(OPS[op](*args));pos=match.end()
 if logic[pos:].strip(' ,\n') or not results:raise ValueError('Invalid program syntax')
 value=results[-1]
 return {'answer':str(round(value,5)) if isinstance(value,Decimal) else value,'audit':audit,'steps':[str(x) for x in results]}
