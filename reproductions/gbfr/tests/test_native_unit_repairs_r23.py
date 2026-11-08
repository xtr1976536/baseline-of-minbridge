"""Native quantities versus unknown aggregate scales; protocol dataflow only."""
from .test_refusal_repairs_r22 import Client,goal,run,prompt,MONEY

def test_native_individual_count_times_per_share_price_can_change_display_scale():
    gs=[goal('Individual shares purchased',unit='shares'),goal('Price per share',unit='currency/share')]
    class Native(Client):
        async def json(self,task,p):
            result=await super().json(task,p)
            if task=='OES' and result['found']:
                b=result['var_bindings']['v1'];is_price='Price' in b['metric']
                b['observed_meta']={'currency':'USD' if is_price else None,'scale':'ones',
                                    'unit':'currency/share' if is_price else 'shares'}
                result['notes']='Source specifies individual shares and USD per share; native units.'
            return result
    c=Native(gs,{'Individual shares purchased':(12,'Individual shares purchased: 12'),
                 'Price per share':(3,'Price per share: USD 3 per share')},
             'vars["v1"] * vars["v2"] / 1000000',{'currency':'USD','scale':'million','unit':None},
             operator='product',reasoning='ArithmeticCalculation')
    p=run(c,'What was the purchase value in millions of dollars?',
          'Individual shares purchased: 12. Price per share: USD 3 per share.')
    assert p.value==0.000036 and p.meta['scale']=='million'
    assert all(e['meta']['scale']=='ones' for e in prompt(c,'OPE.final').data['evidences'])
    for task in ['OQA','OES','OPE.final']:
        assert 'Such source unit semantics can establish native ones' in prompt(c,task).instructions

def test_unrelated_aggregate_does_not_get_native_ones_from_currency_alone():
    c=Client([goal('Tax liability',scale='million')],{'Tax liability':(80,'Tax liability: $80')},
             'vars["v1"]',MONEY,observed={'currency':'$','scale':None,'unit':None})
    p=run(c,'What is the tax liability in millions?', 'Tax liability: $80. Reporting scale not provided.')
    assert p.value==80 and p.meta['scale'] is None
    assert prompt(c,'OPE.final').data['evidences'][0]['meta']['scale'] is None
    assert 'does not establish ones for an unrelated aggregate monetary table' in prompt(c,'OPE.final').instructions
