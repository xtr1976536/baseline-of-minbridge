"""No paid calls or browser use: verify author definitions and API failure handling."""
import ast,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1]

class ReActRuntimeTests(unittest.TestCase):
    def test_exported_definitions_equal_author_notebooks(self):
        for task,title in [('hotpotqa','hotpotqa'),('fever','FEVER'),('alfworld','alfworld'),('webshop','WebShop')]:
            expected={}
            for cell in json.loads((ROOT/f'upstream/ReAct/{title}.ipynb').read_text())['cells']:
                if cell['cell_type']=='code':
                    for node in ast.parse(''.join(cell['source'])).body:
                        if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name!='llm':expected[node.name]=ast.dump(node,include_attributes=False)
            actual={n.name:ast.dump(n,include_attributes=False) for n in ast.parse((ROOT/f'configs/react-{task}-author-extracted.py').read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name!='llm'}
            self.assertEqual(expected,actual,task)
    def call_llm(self,generate,folder):
        node=next(n for n in ast.parse((ROOT/'scripts/run_react.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='llm')
        from types import SimpleNamespace
        namespace={'a':SimpleNamespace(reference_model='text-davinci-002',model='offline-fixture',api_mode='chat',task='hotpotqa'),'generate':generate,'run':folder,'json':json,'config':{'api_calls':0}}
        exec(compile(ast.Module(body=[node],type_ignores=[]),'react-llm-test','exec'),namespace)
        return namespace['llm']
    def test_permanent_error_is_not_repeated(self):
        generate=Mock(side_effect=RuntimeError('authentication/payment'))
        with tempfile.TemporaryDirectory() as folder:
            llm=self.call_llm(generate,Path(folder))
            with self.assertRaises(RuntimeError):llm('unchanged prompt\nAction 1:')
        self.assertEqual(generate.call_count,1)
    def test_empty_response_never_becomes_an_action(self):
        generate=Mock(return_value=('',{'choices':[]},'chat','offline-fixture'))
        with tempfile.TemporaryDirectory() as folder:
            llm=self.call_llm(generate,Path(folder))
            with self.assertRaises(RuntimeError):llm('original prompt\nAction 1:')
    def test_author_tokens_and_stop_preserved(self):
        generate=Mock(return_value=('Finish[test]',{'choices':[]},'chat','offline-fixture'))
        with tempfile.TemporaryDirectory() as folder:
            llm=self.call_llm(generate,Path(folder));self.assertEqual(llm('original prompt\nAction 1:',['\n']),'Finish[test]')
        self.assertTrue(generate.call_args.args[0].endswith('original prompt\nAction 1:'))
        self.assertEqual(generate.call_args.args[1:],('text-davinci-002','offline-fixture','chat',100,0,['\n'],90))

if __name__=='__main__':unittest.main()

class ParallelPartitionTests(unittest.TestCase):
    def test_completed_including_wrong_answers_never_regenerate(self):
        import sys
        sys.path.insert(0,str(ROOT/'scripts'))
        from run_hotpotqa_parallel import split_pending
        shards=split_pending(list(range(500)),set(range(34)))
        flat=[i for shard in shards for i in shard]
        self.assertEqual(len(flat),466);self.assertEqual(set(flat),set(range(34,500)))
        self.assertEqual(len(flat),len(set(flat)))
    def test_fresh_partition(self):
        import sys
        sys.path.insert(0,str(ROOT/'scripts'))
        from run_hotpotqa_parallel import split_pending
        self.assertEqual([len(s) for s in split_pending(list(range(500)),set())],[125]*4)
