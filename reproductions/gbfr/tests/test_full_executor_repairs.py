"""Representation failures observed during the paused R19 full run."""
import asyncio
import json

import pytest

from gbfr.executor import execute
from gbfr.types import ProtocolError


CODE='''def compute(vars):
    amount = vars["a"] - vars["b"]
    return {"value": amount, "trace": {"inputs": [vars["a"], vars["b"]]}}
'''


@pytest.mark.parametrize('suffix,change',[(' }','extraneous_terminal_brace'),('\u23ce','terminal_return_glyph')])
def test_complete_program_with_one_extraneous_terminal_token_keeps_arithmetic(suffix,change):
    p=CODE.rstrip()+suffix
    r=asyncio.run(execute(p,{'a':12,'b':19}))
    assert r['value']==-7 and r['trace']['inputs']==[12,19]
    assert r['trace']['executor_protocol']['program_representation']==[change]
    assert r['trace']['executor_protocol']['effective_program']==CODE.rstrip()


def test_sole_json_code_field_is_unwrapped_without_adding_a_helper_or_value():
    r=asyncio.run(execute(json.dumps({'code':CODE}),{'a':6,'b':2}))
    assert r['value']==4
    assert r['trace']['executor_protocol']['program_representation']==['sole_json_code_field']
    assert r['trace']['executor_protocol']['effective_program']==CODE.strip()


@pytest.mark.parametrize('program',[
    CODE.rstrip()+' } }',
    'def compute(vars):\n    return {"value": vars["a"], "trace": {}',
    'def compute(vars):\n    return {"value": vars["a"] vars["b"], "trace": {}}',
    json.dumps({'code':CODE,'answer':123}),
    json.dumps({'code':'import os\ndef compute(vars):\n    return None'}),
])
def test_representation_adapter_does_not_guess_missing_syntax_or_accept_unsafe_code(program):
    with pytest.raises(ProtocolError):asyncio.run(execute(program,{'a':6,'b':2}))


@pytest.mark.parametrize('label,year',[
    ('September 28, 2018',2018),('year ended June 25, 2017',2017),
    ('30/9/2019',2019),('December 27, 2019',2019),('2019-12-27',2019),('FY 2019',2019),
])
def test_explicit_year_request_uses_only_the_year_of_one_complete_selected_label(label,year):
    code='def compute(vars):\n    return '+repr({'value':label,'trace':{'output_meta':{'currency':'USD','scale':'million','unit':'shares'}}})
    with pytest.raises(ProtocolError,match='non-scalar'):asyncio.run(execute(code,{}))
    r=asyncio.run(execute(code,{},allow_year_result=True))
    assert r['value']==year
    assert r['trace']['output_meta']=={'currency':None,'scale':None,'unit':'years'}
    assert r['trace']['executor_protocol']['calendar_label_to_year']['original_value']==label


@pytest.mark.parametrize('label',[
    '2019 and 2018','Both years','Neither year','Cannot determine','None',
    '2018/2019','2019-2020','FY2019/20','year ended 2018 or 2019','February 30, 2019',
    'Expected year 2019','2019 was the largest',
])
def test_year_adapter_never_selects_from_multiple_or_invalid_answers(label):
    code='def compute(vars):\n    return '+repr({'value':label,'trace':{}})
    with pytest.raises(ProtocolError,match='non-scalar'):asyncio.run(execute(code,{},allow_year_result=True))


def test_literal_string_join_is_safe_but_does_not_make_a_multiple_answer_scalar():
    code='''def compute(vars):
    years = [y for y, n in {"2018": vars["a"], "2019": vars["b"]}.items() if n > 0]
    return {"value": " and ".join(years), "trace": {"matching_years": years}}
'''
    assert asyncio.run(execute(code,{'a':3,'b':-2},allow_year_result=True))['value']==2018
    with pytest.raises(ProtocolError,match='non-scalar'):asyncio.run(execute(code,{'a':3,'b':2},allow_year_result=True))
    with pytest.raises(ProtocolError):asyncio.run(execute(code.replace('" and ".join(years)','vars.__class__.join(years)'),{'a':3,'b':2}))
