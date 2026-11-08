import unittest

from verifiqa.dataset_finqa import _convert, _doc_name_from_filename


class FinqaDatasetTests(unittest.TestCase):
    def test_page_filename_maps_to_canonical_10k_doc_name(self):
        item = {
            "filename": "AAPL/2021/page_42.pdf-3",
            "pre_text": ["supporting sentence"],
            "post_text": [],
            "table": [["year", "value"], ["2021", "10"]],
            "qa": {
                "question": "What was the value?",
                "exe_ans": "10",
                "gold_inds": {"table_1": "unused"},
            },
        }

        example = _convert(item)

        self.assertIsNotNone(example)
        self.assertEqual(example.doc_name, "AAPL_2021_10K")
        self.assertEqual(example.company, "AAPL")
        self.assertTrue(example.evidence)
        self.assertTrue(all(ev["doc_name"] == "AAPL_2021_10K" for ev in example.evidence))

    def test_nonstandard_filename_falls_back_unchanged(self):
        self.assertEqual(_doc_name_from_filename("custom-doc"), "custom-doc")


if __name__ == "__main__":
    unittest.main()
