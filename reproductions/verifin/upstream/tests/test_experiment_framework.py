import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from verifiqa.answerers.pot import execute_safe_python
from verifiqa.experiments.registry import parse_methods
from verifiqa.experiments.runner import run_experiment, summarize_experiment_results
from verifiqa.types import FinanceBenchExample


class FakeLlm:
    def __init__(self, response):
        self.response = response
        self.call_index = 0

    def chat(self, messages, temperature=0.0, stage="unknown"):
        self.call_index += 1
        return self.response


class ExperimentFrameworkTests(unittest.TestCase):
    def test_parse_methods_maps_to_components(self):
        specs = parse_methods("rag_cot,oracle_pot")
        self.assertEqual([spec.name for spec in specs], ["rag_cot", "oracle_pot"])
        self.assertEqual(specs[0].evidence_mode, "rag")
        self.assertEqual(specs[0].answerer, "cot")
        self.assertEqual(specs[1].answerer, "pot")

    def test_safe_python_executes_arithmetic(self):
        value = execute_safe_python("revenue = 12\ncost = 7\nanswer = revenue - cost")
        self.assertEqual(value, 5.0)

    def test_safe_python_rejects_import(self):
        with self.assertRaises(ValueError):
            execute_safe_python("import os\nanswer = 1")

    def test_oracle_cot_experiment_writes_shared_schema(self):
        example = FinanceBenchExample(
            financebench_id="ex1",
            question="What is revenue minus cost?",
            answer="10",
            evidence=[
                {
                    "evidence_text": "Revenue was 15. Cost was 5.",
                    "doc_name": "DOC_10K",
                    "evidence_page_num": 1,
                }
            ],
            doc_name="DOC_10K",
        )
        with TemporaryDirectory() as tmp:
            results = run_experiment(
                examples=[example],
                method_names="oracle_cot",
                llm_client=FakeLlm("The answer is 10."),
                out_dir=Path(tmp),
            )
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].method, "oracle_cot")
            self.assertEqual(results[0].draft_answer, "The answer is 10.")
            self.assertTrue(results[0].correct)
            self.assertTrue((Path(tmp) / "results.jsonl").exists())
            summary = summarize_experiment_results(results)
            self.assertEqual(summary["methods"]["oracle_cot"]["answer_accuracy"], 1.0)


if __name__ == "__main__":
    unittest.main()
