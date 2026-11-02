import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from logical_deduction_cot import extract_ld_cot
class ExtractionTests(unittest.TestCase):
    def test_explicit_formats(self):
        for raw in ['Reasoning.\n**Answer: C) choice**','The correct answer is **C**.','Reasoning. Therefore C) choice','The correct option is: C']:
            self.assertEqual(extract_ld_cot(raw,3)['predicted_answer'],'C')
    def test_abstain(self):
        for raw in ['A) first, B) second','The answer is G.','No unique answer','A and B are variables', 'The answer is a station wagon', 'The option is a plausible guess']:
            self.assertEqual(extract_ld_cot(raw,3)['predicted_answer'],'')
    def test_delimiter_priority(self):
        self.assertEqual(extract_ld_cot('A) is impossible. The correct option is: B',3)['predicted_answer'],'B')
    def test_raw_kept(self):
        raw='**Answer: A) foo**';r=extract_ld_cot(raw,3)
        self.assertEqual(r['raw_output'],raw)
        self.assertEqual(r['markdown_only_predicted_answer'],'Answer: A) foo')
    def test_other_datasets_original_function_unchanged(self):
        from logic_final import cot_answer
        self.assertEqual(cot_answer('Reasoning. Answer: C) foo')['predicted_answer'],'Reasoning. Answer: C) foo')
if __name__=='__main__':unittest.main()
