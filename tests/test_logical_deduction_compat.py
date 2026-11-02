import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from logical_deduction_compat import normalize_query_labels

class LabelTests(unittest.TestCase):
    def test_only_labels_change(self):
        raw='Domain:\n1: oldest\nVariables:\nx [IN] [1, 2]\nConstraints:\nx == 2\nQuery:\n(A) x == 2 ::: option\n(B) y == 2'
        fixed,n=normalize_query_labels(raw)
        self.assertEqual(n,2)
        self.assertEqual(fixed,raw.replace('(A) x','A) x').replace('(B) y','B) y'))
        self.assertEqual(normalize_query_labels(fixed),(fixed,0))
    def test_multiple_programs_never_selected(self):
        raw='Domain:\nQuery:\n(A) x == 2\nDomain:\nQuery:\n(B) y == 2'
        self.assertEqual(normalize_query_labels(raw),(raw,0))
    def test_constraints_and_comments_unchanged(self):
        raw='Constraints:\n(A) x == 1\nQuery:\nA) x == 1 ::: (B) is a comment'
        self.assertEqual(normalize_query_labels(raw),(raw,0))
    def test_no_missing_or_malformed_labels_repaired(self):
        for raw in ['Query:\nx == 1','Query:\n(A)no-space','Query:\nA. x == 1']:
            self.assertEqual(normalize_query_labels(raw),(raw,0))
if __name__=='__main__':unittest.main()

class LayoutTests(unittest.TestCase):
    def test_inline_heading_only(self):
        from logical_deduction_compat import normalize_csp_surface
        raw='Domain: 1: left, 2: right\nVariables: x [IN] [1,2]\nVariables: y [IN] [1,2]\nConstraints: x < y\nQuery: (A) x == 1\nQuery: (B) y == 1'
        fixed,edits=normalize_csp_surface(raw)
        self.assertEqual(fixed,'Domain:\n1: left, 2: right\nVariables:\nx [IN] [1,2]\ny [IN] [1,2]\nConstraints:\nx < y\nQuery:\nA) x == 1\nB) y == 1')
        self.assertEqual(edits['label_edits'],2)
        self.assertEqual(normalize_csp_surface(fixed)[0],fixed)
    def test_multiple_and_backwards_programs_unchanged(self):
        from logical_deduction_compat import normalize_csp_layout
        for raw in ['Domain:\nVariables:\nConstraints:\nQuery:\nDomain:', 'Domain:\nVariables:\nVariables:\nConstraints:\nQuery:', 'Domain: 1\nVariables: x\nConstraints: x == 1\nVariables: y\nQuery: A) x == 1']:
            self.assertEqual(normalize_csp_layout(raw),(raw,0))
