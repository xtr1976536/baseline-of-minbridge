import unittest

from verifiqa.generation.answer_generator import AnswerGenerator
from verifiqa.types import EvidenceChunk


class FakeAnswerLlm:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def chat(self, messages, temperature=0.0, stage="unknown"):
        self.calls.append({"messages": messages, "temperature": temperature, "stage": stage})
        return self.response


class AnswerGeneratorTests(unittest.TestCase):
    def test_prompt_requires_single_strict_json_object(self):
        llm = FakeAnswerLlm('{"answer": "24.26"}')
        generator = AnswerGenerator(llm)

        answer = generator.generate(
            "What is the fixed asset turnover?",
            [EvidenceChunk("chunk", "doc", None, "Revenue was 6489. PP&E was 253 and 282.")],
        )

        self.assertEqual(answer, "24.26")
        prompt = llm.calls[0]["messages"][0].content
        self.assertIn("Return exactly one JSON object and nothing else", prompt)
        self.assertIn("parseable by json.loads", prompt)
        self.assertIn("no second JSON object", prompt)
        self.assertIn("Do not output ```json", prompt)
        self.assertIn("numeric final answer", prompt)
        self.assertIn("OCR/tokenization artifacts", prompt)
        self.assertIn("value / percentage", prompt)

    def test_uses_first_json_object_when_model_adds_extra_object(self):
        llm = FakeAnswerLlm(
            '{"answer": "24.26"}\n'
            '{"debug": "extra object the prompt told the model not to emit"}'
        )

        answer = AnswerGenerator(llm).generate(
            "What is the fixed asset turnover?",
            [EvidenceChunk("chunk", "doc", None, "Revenue was 6489. PP&E was 267.5.")],
        )

        self.assertEqual(answer, "24.26")

    def test_uses_json_object_inside_surrounding_text(self):
        llm = FakeAnswerLlm('Here is the answer:\n{"answer": "24.26"}\nDone.')

        answer = AnswerGenerator(llm).generate(
            "What is the fixed asset turnover?",
            [EvidenceChunk("chunk", "doc", None, "Revenue was 6489. PP&E was 267.5.")],
        )

        self.assertEqual(answer, "24.26")


if __name__ == "__main__":
    unittest.main()
