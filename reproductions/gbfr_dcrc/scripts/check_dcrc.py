from dcrc_executor import execute
ir={'tasks':{'T1':{},'T2':{}},'pool':[{'id':'E1','val':'96.50','decisions':{'T1':{'tag':'ACCEPT','why':'[Exact_Match]'}}},{'id':'E2','val':'150.30','decisions':{'T2':{'tag':'ACCEPT','why':'[Exact_Match]'}}}], 'logic':'subtract(96.50, const_100), divide(#0, const_100), subtract(150.30, const_100), divide(#2, const_100), subtract(#1, #3)'}
assert float(execute(ir)['answer']) == -0.538
for logic in ['add(999, 96.50)','add(#0, 96.50)','__import__(os)']:
 try:execute({**ir,'logic':logic})
 except (ValueError,ArithmeticError):pass
 else:raise AssertionError(logic)
print('Appendix C example and ungrounded/forward-reference/invalid-program rejection: PASS')
