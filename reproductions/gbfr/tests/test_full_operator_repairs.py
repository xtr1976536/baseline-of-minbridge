import asyncio

import pytest

from gbfr.engine import GBFR
from gbfr.graph import Metric,MetricGraph
from gbfr.types import ProtocolError
from .helpers import ScriptedClient


def constraints(year=None,unit=None,currency=None):
    return {'temporal_scope':year,'entity_scope':None,'meta':{'currency':currency,'scale':None,'unit':unit}}


def test_engine_only_enables_date_to_year_for_an_explicit_year_question():
    c=constraints(unit='years')
    plan={'reasoning_type':'DirectRetrieval','operator':'sum','precision':'unknown',
          'subgoals':[{'metric':'Introduction year','constraints':c}]}
    class Client(ScriptedClient):
        async def complete(self,task,prompt):
            if task=='OPE.final':
                return '''def compute(vars):
    return {"value": f"April 9, {int(vars['v1'])}", "trace": {}}
'''
            return await super().complete(task,prompt)
    graph=MetricGraph([Metric('Introduction year',[],'','atomic',[])])
    def model():return GBFR(graph,Client(c,{'Introduction year':(2021,'Introduction year: 2021')},plan=plan),evidence_policy='paper')
    doc='The technology was introduced on April 9, 2021. Introduction year: 2021.'
    p=asyncio.run(model().predict('In which year was this technology introduced?',doc))
    assert p.status=='answered' and p.value==2021 and p.meta['unit']=='years'
    final=next(e for e in p.trace['events'] if e['operator']=='OPE.final')
    assert final['execution']['trace']['executor_protocol']['calendar_label_to_year']['original_value']=='April 9, 2021'
    with pytest.raises(ProtocolError,match='non-scalar text'):
        asyncio.run(model().predict('What was the introduction date?',doc))


@pytest.mark.parametrize('missing_price',[False,True])
def test_compound_outer_difference_uses_only_grounded_elementary_inputs(missing_price):
    specs=[('Inventory quantity','2021','count',None),('Unit price','2021','currency/unit','USD'),
           ('Inventory quantity','2022','count',None),('Unit price','2022','currency/unit','USD')]
    goals=[{'metric':m,'constraints':constraints(y,u,c)} for m,y,u,c in specs]
    plan={'reasoning_type':'ArithmeticCalculation','operator':'difference','precision':'unknown','subgoals':goals}
    evidence={('Inventory quantity','2021'):(100,'Inventory quantity: 100'),('Unit price','2021'):(3,'Unit price: 3'),
              ('Inventory quantity','2022'):(120,'Inventory quantity: 120'),('Unit price','2022'):(4,'Unit price: 4')}
    if missing_price:del evidence[('Unit price','2022')]
    class Client(ScriptedClient):
        async def complete(self,task,prompt):
            if task=='OPE.final':
                self.calls.append((task,prompt))
                return '''def compute(vars):
    old_total = vars["v1"] * vars["v2"]
    new_total = vars["v3"] * vars["v4"]
    return {"value": new_total - old_total, "trace": {"old": old_total, "new": new_total, "output_meta": {"currency": "USD", "scale": "ones", "unit": "currency"}}}
'''
            return await super().complete(task,prompt)
    client=Client(constraints(),evidence,plan=plan)
    doc='2021 Inventory quantity: 100, Unit price: 3 USD per unit. 2022 Inventory quantity: 120, Unit price: 4 USD per unit.'
    p=asyncio.run(GBFR(MetricGraph([Metric('Other',[],'','atomic',[])]),client,evidence_policy='paper').predict(
        'How much did the inventory value increase from 2021 to 2022 using quantities and unit prices?',doc))
    assert p.status==('abstained' if missing_price else 'answered')
    if not missing_price:assert p.value==180
    assert len([t for t,_ in client.calls if t=='OES'])==4
    assert not any(t in {'OPE.metric','Verify'} for t,_ in client.calls)
    assert sum(t=='OPE.final' for t,_ in client.calls)==(0 if missing_price else 1)
