import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'upstream/Logic-LLM/models'))
from logic_final import (UPSTREAM, DATASETS, FORMAT_FILE, build_prompt, strip_markdown,
                         cot_answer, validate_rows, format_constraint)
from evaluate_logic_experiment import evaluate, load_author_solver
from run_logic_experiment import read_records, record_path, snapshots

class MarkdownTests(unittest.TestCase):
    def test_common_answer_markup(self):
        for raw in ('**A) True**', '`A) True`', '### A) True', '- **A) True**', '```text\nA) True\n```', '__A) True__'):
            self.assertEqual(strip_markdown(raw), 'A) True')
    def test_no_semantic_answer_inference(self):
        self.assertEqual(strip_markdown('Unknown'), 'Unknown')
        self.assertEqual(strip_markdown('Reasoning mentions A and B.'), 'Reasoning mentions A and B.')
    def test_author_phrase_and_raw_preserved(self):
        raw='Reason.\nThe correct option is: **B) False**'
        row=cot_answer(raw)
        self.assertEqual(row['raw_output'],raw)
        self.assertEqual(row['raw_predicted_answer'],'**B) False**')
        self.assertEqual(row['predicted_answer'],'B) False')
    def test_empty(self):
        self.assertEqual(strip_markdown(None),'')

class FidelityTests(unittest.TestCase):
    def test_templates_equal_author_builders_all_datasets(self):
        from logic_program import LogicProgramGenerator
        spec=importlib.util.spec_from_file_location('author_baseline_test',UPSTREAM/'baselines/gpt3_baseline.py')
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        methods={'ProntoQA':'prompt_prontoqa','ProofWriter':'prompt_proofwriter','FOLIO':'prompt_folio','LogicalDeduction':'prompt_logicaldeduction','AR-LSAT':'prompt_arlsat'}
        for dataset in DATASETS:
            rows=json.loads((UPSTREAM/f'data/{dataset}/dev.json').read_text())
            from logic_final import prompt_files
            program,cot=prompt_files(dataset)
            generator=object.__new__(LogicProgramGenerator);generator.prompt_template=program.read_text()
            baseline=object.__new__(mod.GPT3_Reasoning_Graph_Baseline)
            for row in (rows[0],rows[len(rows)//2],rows[-1]):
                expected=getattr(generator,methods[dataset])(row)
                self.assertEqual(build_prompt(dataset,'program',row),format_constraint(dataset)+'\n\n'+expected)
                self.assertEqual(build_prompt(dataset,'cot',row),baseline.prompt_LSAT(cot.read_text(),row))
    def test_author_files_unchanged(self):
        for rel in ['models/symbolic_solvers/pyke_solver/pyke_solver.py','models/symbolic_solvers/csp_solver/csp_solver.py','models/symbolic_solvers/z3_solver/sat_problem_solver.py','models/evaluation.py','models/backup_answer_generation.py']:
            self.assertEqual((UPSTREAM/rel).read_bytes(),subprocess.check_output(['git','show','HEAD:'+rel],cwd=UPSTREAM))
    def test_only_author_solver_classes(self):
        names=['Pyke_Program','Pyke_Program','FOL_Prover9_Program','CSP_Program','LSAT_Z3_Program']
        for dataset,name in zip(DATASETS,names):
            self.assertEqual(load_author_solver(dataset).__name__,name)
            self.assertTrue(load_author_solver(dataset).__module__.startswith('symbolic_solvers.'))
    def test_constraint_exactly_the_approved_text(self):
        self.assertEqual(format_constraint('ProofWriter'),"For the final problem, output only the plain-text logic program, following the example's exact headings and syntax. No Markdown, blank lines within sections, or additional explanation.")
        ld=format_constraint('LogicalDeduction')
        self.assertIn('Domain:',ld)
        self.assertIn('Variables:',ld)
        self.assertIn('Constraints:',ld)
        self.assertIn('Query:',ld)
        self.assertIn('A), B)',ld)
        self.assertNotIn('(A)',ld)
        ar=format_constraint('AR-LSAT')
        self.assertIn('# Declarations, # Constraints, and # Options',ar)
        self.assertIn('one sort per disjoint universe',ar)
        self.assertIn('helper functions',ar)

class FallbackTests(unittest.TestCase):
    def test_parse_failure_uses_markdown_cleaned_cot(self):
        row=json.loads((UPSTREAM/'data/ProofWriter/dev.json').read_text())[0]
        program={**row,'raw_logic_programs':['not a program']}
        cot={'id':row['id'],'answer':row['answer'],'question':row['question'],'raw_output':'The correct option is: **'+row['answer']+')**','predicted_answer':'unused'}
        old=Path.cwd();os.chdir(UPSTREAM)
        try:results,summary=evaluate('ProofWriter',[program],[cot],[row])
        finally:os.chdir(old)
        self.assertEqual(summary['fallback_count'],1)
        self.assertEqual(summary['accuracy'],1.)
        self.assertEqual(summary['raw_author_accuracy_without_cleanup'],0.)
        self.assertEqual(results[0]['flag'],'parsing error')
        self.assertEqual(results[0]['raw_predicted_answer'],'**'+row['answer']+')**')
    def test_unknown_solver_output_unchanged(self):
        # The final evaluator must not "repair" a successful C response based on gold.
        row=json.loads((UPSTREAM/'data/ProofWriter/dev.json').read_text())[0]
        class Solver:
            flag=True
            def __init__(self,*args):pass
            def execute_program(self):return 'C',''
            def answer_mapping(self,value):return value
        old=Path.cwd();os.chdir(UPSTREAM)
        try:
            with patch('evaluate_logic_experiment.load_author_solver',return_value=Solver):
                results,summary=evaluate('ProofWriter',[{**row,'raw_logic_programs':['x']}],[{'id':row['id'],'answer':row['answer'],'predicted_answer':'A'}],[row])
        finally:os.chdir(old)
        self.assertEqual(results[0]['predicted_answer'],'C')
        self.assertEqual(summary['fallback_count'],0)

class CheckpointTests(unittest.TestCase):
    def test_invalid_identity(self):
        for rows in ([],[{'id':'foreign'}],[{'id':'a'},{'id':'a'}],[{'id':'a','answer':'B'}]):
            with self.assertRaises(ValueError):validate_rows(rows,[{'id':'a','answer':'A'}])
    def test_record_recovers_both_log_and_output(self):
        row=json.loads((UPSTREAM/'data/ProofWriter/dev.json').read_text())[0]
        with tempfile.TemporaryDirectory() as folder:
            run=Path(folder);(run/'program/records').mkdir(parents=True)
            record={'dataset':'ProofWriter','stage':'program','row':{**row,'raw_logic_programs':['test']},'log':{'id':row['id'],'prompt':build_prompt('ProofWriter','program',row),'response':{'test':True}}}
            record_path(run,'program',row['id']).write_text(json.dumps(record))
            self.assertEqual(snapshots(run,'program',[row]),1)
            self.assertEqual(json.loads((run/'program/programs.json').read_text())[0]['id'],row['id'])
            self.assertEqual(json.loads((run/'program/api.jsonl').read_text())['id'],row['id'])
    def test_changed_prompt_record_rejected(self):
        row=json.loads((UPSTREAM/'data/ProofWriter/dev.json').read_text())[0]
        with tempfile.TemporaryDirectory() as folder:
            run=Path(folder);(run/'program/records').mkdir(parents=True)
            record_path(run,'program',row['id']).write_text(json.dumps({'dataset':'ProofWriter','row':row,'log':{'id':row['id'],'prompt':'wrong'}}))
            with self.assertRaises(ValueError):read_records(run,'program',[row])

if __name__=='__main__':unittest.main()

class RunnerIntegrationTests(unittest.TestCase):
    def test_fresh_generation_records_evaluation_and_zero_call_resume(self):
        import contextlib,io,shutil
        import run_logic_experiment as runner
        fixtures=json.loads((UPSTREAM/'outputs/logic_programs/ProofWriter_dev_gpt-4.json').read_text())[:2]
        prompts={}
        for row in fixtures:
            prompts[build_prompt('ProofWriter','program',row)]=row['raw_logic_programs'][0]
            prompts[build_prompt('ProofWriter','cot',row)]='The correct option is: **A**'
        def fake_generate(prompt,reference,model,style,max_tokens,temperature,stop,timeout):
            raw=prompts[prompt]
            response={'choices':[{'message':{'content':raw},'finish_reason':'stop'}],
                      '_minbridge_request':{'model':model,'api_style':style,'temperature':temperature,'max_tokens':max_tokens,'top_p':1.,'stop':stop,'messages':[{'role':'user','content':prompt}],'prompt':None}}
            return raw,response,style,model
        before=set((ROOT/'results').glob('logic-final-ProofWriter-*'))
        with tempfile.TemporaryDirectory() as tmp:
            ids=Path(tmp)/'ids.json';ids.write_text(json.dumps([r['id'] for r in fixtures]))
            argv=['run','--dataset','ProofWriter','--sample-ids',str(ids),'--model','offline-fixture','--workers','2']
            try:
                with patch.dict(os.environ,{'OPENAI_API_KEY':'offline-dummy','OPENAI_BASE_URL':'https://example.invalid/v1'}),patch('requests.post',side_effect=AssertionError('Unexpected network')):
                    with patch.object(sys,'argv',argv),patch.object(runner,'generate',side_effect=fake_generate) as mock,contextlib.redirect_stdout(io.StringIO()):
                        runner.main()
                    self.assertEqual(mock.call_count,4)
                    created=set((ROOT/'results').glob('logic-final-ProofWriter-*'))-before
                    self.assertEqual(len(created),1);run=created.pop()
                    s=json.loads((run/'summary.json').read_text());self.assertEqual(s['requests_verified'],{'program':2,'cot':2});self.assertEqual(s['interpreter'],'author-code')
                    with patch.object(sys,'argv',argv+['--resume',str(run)]),patch.object(runner,'generate',side_effect=AssertionError('Resume regenerated outputs')),contextlib.redirect_stdout(io.StringIO()):
                        runner.main()
            finally:
                for folder in set((ROOT/'results').glob('logic-final-ProofWriter-*'))-before:shutil.rmtree(folder)
