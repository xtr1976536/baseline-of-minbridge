import ast,json,sys,subprocess
sys.dont_write_bytecode=True
from protocol import ROOT,VENDOR,official,guard
sys.path.insert(0,str(VENDOR))
from tool import finqa_equal,floatify_ans
checks={};manifest={}
for task in ['finqa','convfinqa','tatqa']:
 demo,builder,rows,meta=official(task);tree=ast.parse((VENDOR/meta['script']).read_text())
 # Ensure extracted prompt is exactly the literal upstream, including typo and whitespace.
 prompt=next(n.value.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['prompt_4shot','prompt_8shot'] for t in n.targets))
 assert demo==prompt;assert len(rows)=={'finqa':1147,'convfinqa':421,'tatqa':1668}[task]
 assert builder(rows[0]).endswith('#Python\n') if task!='tatqa' else 'Quesetion:' in builder(rows[0])
 manifest[task]=meta;checks[task+'_prompt_and_data']='PASS'
assert finqa_equal(0.0,0.0,False);assert floatify_ans(False) is False
for code in ['ans = 1/0','while True: pass','ans = False','ans = 0','ans = 94']:
 r=subprocess.run([sys.executable,str(ROOT/'scripts/execute_worker.py')],input=json.dumps({'task':'finqa','code':code}),text=True,capture_output=True,timeout=15)
 assert r.returncode==0,r.stderr
 value=json.loads(r.stdout)['value'];expected={'ans = False':False,'ans = 0':0.0,'ans = 94':94.0}.get(code)
 assert value==expected,(code,value)
for code in ['import os\nans=os.listdir()','ans = open("/etc/passwd").read()']:
 try:guard(code)
 except ValueError:pass
 else:raise AssertionError('guard missed '+code)
checks['worker_zero_false_timeout_division_and_guard']='PASS'
report={'checks':checks,'manifest':manifest,'paper_table2_greedy_reference_percent':{'finqa':64.5,'convfinqa':64.6,'tatqa':69.0},'known_gaps':['ConvFinQA repository dev421 vs paper labelled Test421; not interchangeable with unlabelled test_turn1521','SC repo temperature0.5 K30 vs paper0.4 K40; SC not run','Original Codex replaced; results are alternate-backbone','No all-eight-dataset claim; financial scope first']}
(ROOT/'results/protocol_audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(checks))
