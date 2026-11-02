import json,sys
sys.dont_write_bytecode=True
from protocol import ROOT,VENDOR,instantiate,check_corr,manifest
calls=[]
def call(**kwargs):
 calls.append(kwargs)
 return 'def solution():\n    return 1' if len(calls)==1 else '# It is correct\ndef solution():\n    return 1'
import os
os.chdir(VENDOR);logs=instantiate(call)('fixture',4,'rich',0.7)
assert len(logs)==1 and len(calls)==2
assert calls[0]['prompt']==(VENDOR/'data/prompt/gsm/init.txt').read_text()+'# Q: fixture\n# solution using Python:\n'
assert calls[0]['max_tokens']==300 and calls[1]['max_tokens']==600
assert calls[0]['stop_token']=='\n\n' and calls[1]['stop_token']=='### END'
assert calls[0]['temperature']==calls[1]['temperature']==0.7
calls.clear()
def repeat(**kwargs):
 calls.append(kwargs);return 'def solution():\n    return 1' if len(calls)==1 else '# Needs refinement\ndef solution():\n    return 2'
logs=instantiate(repeat)('fixture',4,'rich',0.7)
assert len(logs)==4 and len(calls)==5
assert len(calls[2]['prompt'])>len(calls[1]['prompt'])
assert check_corr(1.0005,1) and not check_corr(1.002,1)
report={'status':'PASS','original_class_methods_and_loop_extracted':True,'prompt_exact':True,'early_stop':True,'four_round_cap':True,'history_growth':True,'original_numeric_tolerance':True,'manifest':manifest(),'important':'Official cumulative any-correct uses gold only in evaluation, not generation; report separately from final answer.'}
(ROOT/'results/protocol_audit.json').write_text(json.dumps(report,indent=2));print('Protocol checks PASS')
