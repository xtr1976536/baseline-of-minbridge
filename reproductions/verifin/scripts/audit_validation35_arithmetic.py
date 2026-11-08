"""Independent rational-arithmetic and source-fact replay; no LLM calls."""
from pathlib import Path
from fractions import Fraction
from decimal import Decimal,localcontext
import ast
import json
from vf_repro.common import read_jsonl,write_json
from vf_repro.grounding import conversion


def calculate(formula,values):
    def walk(n):
        if isinstance(n,ast.Name):return values[n.id]
        if isinstance(n,ast.Constant):return Fraction(str(n.value))
        if isinstance(n,ast.UnaryOp):return -walk(n.operand) if isinstance(n.op,ast.USub) else walk(n.operand)
        if isinstance(n,ast.BinOp):
            a,b=walk(n.left),walk(n.right)
            if isinstance(n.op,ast.Add):return a+b
            if isinstance(n.op,ast.Sub):return a-b
            if isinstance(n.op,ast.Mult):return a*b
            if isinstance(n.op,ast.Div):return a/b
            if isinstance(n.op,ast.Pow) and b.denominator==1:return a**int(b)
        if isinstance(n,ast.Call) and n.func.id in {'abs','min','max'}:
            args=[walk(x) for x in n.args];return {'abs':abs,'min':min,'max':max}[n.func.id](*args)
        raise ValueError('independent_replay_unsupported_expression')
    return walk(ast.parse(formula,mode='eval').body)


def main():
    root=Path(__file__).resolve().parent.parent;out=root/'runs/validation35-v1'
    rows=read_jsonl(out/'GPT-5.6-Sol/FinanceBench/predictions.jsonl');assert len(rows)==35
    data={r['id']:r for r in read_jsonl(root/'data/main/FinanceBench.jsonl')}
    filings={};replayed=[];lines=['# Source-fact and independent arithmetic audit','',
        'All candidates and verdicts are unchanged. Rational arithmetic below is independent of Z3; it verifies arithmetic and filed-fact identity, not the correctness of the financial interpretation.','',
        '| ID | Status | Reference | Initial candidate answer |','|---|---|---|---|']
    for r in rows:
        sid=r['id'];s=r['result'];d=data[sid]
        answer=r['raw_answer'].replace('|','/').replace('\n',' ')
        lines.append(f'| {sid} | {s["status"]} | {d["gold"]["answer"]} | {answer} |')
        if s['status'] not in {'VERIFIED','VIOLATED'}:continue
        a=s['audit'];doc=d['doc_name']
        if doc not in filings:filings[doc]=json.loads((root/'data/filings'/(doc+'.json')).read_text(encoding='utf-8'))
        filed=filings[doc]
        for b in a['bindings']:
            matches=[f for f in filed['facts'] if f['id']==b['source_fact_id'] and f['concept']==b['concept'] and f['period']==b['period']]
            assert matches and all(Decimal(f['value'])*conversion(f['unit'],b['unit'])==Decimal(b['value']) for f in matches)
            assert b['source_sha256']==filed['instance_sha256'] and b['accession']==filed['accession']
        values={b['role']:Fraction(b['value']) for b in a['bindings']}
        claimed=Fraction(s['claimed_value']);tau=Fraction(a['tolerance'])
        tree=ast.parse(a['plan']['formula'],mode='eval').body
        if isinstance(tree,ast.Call) and tree.func.id in {'cagr','cagr_percent'}:
            end,start,n=[calculate(ast.unparse(x),values) for x in tree.args]
            assert start>0 and end>0 and n.denominator==1 and n>0
            factor=100 if tree.func.id=='cagr_percent' else 1
            lo=max(Fraction(0),1+(claimed-tau)/factor);hi=1+(claimed+tau)/factor;ratio=end/start
            accepted=hi>0 and lo**int(n)<=ratio<=hi**int(n)
            exact='('+str(ratio)+')^(1/'+str(n)+') -> growth display factor '+str(factor)
            with localcontext() as ctx:
                ctx.prec=60;d=Decimal(ratio.numerator)/Decimal(ratio.denominator)
                decimal=str((d**(Decimal(1)/Decimal(n.numerator))-1)*factor)
        else:
            expected=calculate(a['plan']['formula'],values);accepted=abs(expected-claimed)<=tau;exact=str(expected)
            with localcontext() as ctx:
                ctx.prec=40;decimal=str(Decimal(expected.numerator)/Decimal(expected.denominator))
        assert accepted==(s['status']=='VERIFIED')
        replayed.append({'id':sid,'source_facts_replayed':len(a['bindings']),'formula':a['plan']['formula'],
            'expected_exact':exact,'expected_decimal':decimal,'claim':str(claimed),'tau':str(tau),'decision_matched':True})
    write_json(out/'independent_arithmetic.json',{'replayed':len(replayed),'all_matched':True,'cases':replayed})
    (out/'candidate_review.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'replayed':len(replayed),'all_source_facts_and_decisions_matched':True}))


if __name__=='__main__':main()
