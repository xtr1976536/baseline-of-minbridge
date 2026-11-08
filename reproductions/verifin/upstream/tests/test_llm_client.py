import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from verifiqa.generation.llm_client import AnthropicClaudeClient, ChatMessage, LoggedLlmClient, VllmOpenAIClient, make_llm_client


class FakeClient:
    def chat(self, messages, temperature=0.0):
        return "fake response"


class LlmClientTests(unittest.TestCase):
    def test_make_claude_client(self):
        client = make_llm_client("claude", {"model": "claude-sonnet-4-20250514", "api_key_env": "NO_SUCH_KEY"})
        self.assertIsInstance(client, AnthropicClaudeClient)
        self.assertEqual(client.model, "claude-sonnet-4-20250514")

    def test_make_vllm_client(self):
        client = make_llm_client("vllm", {"model": "local-model"})
        self.assertIsInstance(client, VllmOpenAIClient)
        self.assertEqual(client.model, "local-model")

    def test_unknown_mode_raises(self):
        with self.assertRaises(ValueError):
            make_llm_client("unsupported")

    def test_logged_client_writes_jsonl(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "llm_calls.jsonl"
            client = LoggedLlmClient(FakeClient(), terminal=False, jsonl_path=path)
            response = client.chat([ChatMessage(role="user", content="hello")], stage="unit_test")
            self.assertEqual(response, "fake response")
            text = path.read_text(encoding="utf-8")
            self.assertIn('"stage": "unit_test"', text)
            self.assertIn('"content": "hello"', text)
            self.assertIn('"response": "fake response"', text)


if __name__ == "__main__":
    unittest.main()
