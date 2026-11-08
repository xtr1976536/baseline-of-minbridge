from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


# Reasoning-tuned models (e.g. TheFinAI/Fino1-8B) prepend a chain-of-thought and
# wrap structured output in markdown fences. The downstream JSON parsers do
# json.loads() on the raw string, so a "## Thinking" preamble or a ```json fence
# raises JSONDecodeError (a ValueError). Normalise the reply before returning.
_THINK_TAG = re.compile(r"<think(?:ing)?>.*?</think(?:ing)?>", re.IGNORECASE | re.DOTALL)
_THINK_HEADER = re.compile(
    r"^\s*#{1,6}\s*(?:thinking|thought|reasoning)\b.*?(?=\n\s*#{1,6}\s+\S)",
    re.IGNORECASE | re.DOTALL,
)
_ANSWER_HEADER = re.compile(
    r"^\s*#{1,6}\s*(?:response|answer|final(?:\s+answer)?|output|result)\b[:\s]*",
    re.IGNORECASE,
)
_FENCE = re.compile(r"```[a-zA-Z0-9_-]*\s*\n?(.*?)\n?```", re.DOTALL)


def strip_reasoning(text: str) -> str:
    """Remove <think> blocks / '## Thinking' preambles and unwrap code fences.

    Conservative: only strips a leading reasoning section when a later header
    follows it, and only unwraps a fence when exactly one is present, so plain
    replies (e.g. "$89,311 million") pass through untouched.
    """
    if not text:
        return text
    out = _THINK_TAG.sub("", text)
    m = _THINK_HEADER.match(out)
    if m:
        out = _ANSWER_HEADER.sub("", out[m.end():], count=1)
    fences = _FENCE.findall(out)
    if len(fences) == 1 and out.strip().startswith("```"):
        out = fences[0]
    return out.strip()


@dataclass
class ChatMessage:
    role: str
    content: str


class LlmError(RuntimeError):
    pass


class VllmOpenAIClient:
    """Small OpenAI-compatible chat client for a local vLLM server."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000/v1",
        model: str = "Qwen/Qwen2.5-7B-Instruct",
        api_key: str = "EMPTY",
        timeout: float = 180.0,
        max_tokens: int = 1024,
        max_retries: int = 4,
        retry_backoff: float = 2.0,
        strip_reasoning: bool = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.strip_reasoning = strip_reasoning

    def chat(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.0,
        stage: str = "unknown",
        max_tokens: Optional[int] = None,
    ) -> str:
        output_tokens = int(max_tokens) if max_tokens is not None else self.max_tokens
        payload = {
            "model": self.model,
            "messages": [message.__dict__ for message in messages],
            "temperature": temperature,
            "max_tokens": output_tokens,
        }
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                # Some hosted OpenAI-compatible endpoints (e.g. the HuggingFace
                # router) sit behind Cloudflare, which 403s the default
                # "Python-urllib" User-Agent. Send an explicit one.
                "User-Agent": "verifiqa/1.0",
            },
            method="POST",
        )
        # Hosted routers (e.g. HuggingFace + featherless-ai) intermittently return
        # transient errors when a model is cold or overloaded. Retry those with
        # exponential backoff; fail fast on non-transient errors (auth, bad request).
        _TRANSIENT = {408, 429, 500, 502, 503, 504}
        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    data = json.loads(response.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as exc:
                last_exc = LlmError(f"vLLM request failed: HTTP Error {exc.code}: {exc.reason}")
                if exc.code not in _TRANSIENT or attempt == self.max_retries:
                    raise last_exc from exc
            except (urllib.error.URLError, TimeoutError) as exc:
                last_exc = LlmError(f"vLLM request failed: {exc}")
                if attempt == self.max_retries:
                    raise last_exc from exc
            time.sleep(self.retry_backoff * (2 ** attempt))
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LlmError(f"Unexpected vLLM response shape: {data}") from exc
        return strip_reasoning(content) if self.strip_reasoning else content


class AnthropicClaudeClient:
    """Small Anthropic Messages API client for Claude experiments."""

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        api_key: Optional[str] = None,
        api_key_env: str = "ANTHROPIC_API_KEY",
        base_url: str = "https://api.anthropic.com/v1",
        anthropic_version: str = "2023-06-01",
        timeout: float = 60.0,
        max_tokens: int = 1024,
        max_retries: int = 4,
        retry_backoff: float = 2.0,
    ):
        self.model = model
        self.api_key = api_key or os.environ.get(api_key_env, "")
        self.api_key_env = api_key_env
        self.base_url = base_url.rstrip("/")
        self.anthropic_version = anthropic_version
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

    def chat(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.0,
        stage: str = "unknown",
        max_tokens: Optional[int] = None,
        output_config: Optional[dict] = None,
    ) -> str:
        if not self.api_key:
            raise LlmError(f"Missing Anthropic API key. Set {self.api_key_env}.")
        output_tokens = int(max_tokens) if max_tokens is not None else self.max_tokens
        system_parts = [message.content for message in messages if message.role == "system"]
        user_messages = [
            {
                "role": "assistant" if message.role == "assistant" else "user",
                "content": message.content,
            }
            for message in messages
            if message.role != "system"
        ]
        payload = {
            "model": self.model,
            "messages": user_messages,
            "max_tokens": output_tokens,
            "temperature": temperature,
        }
        if output_config is not None:
            payload["output_config"] = output_config
        if system_parts:
            payload["system"] = "\n\n".join(system_parts)
        request = urllib.request.Request(
            f"{self.base_url}/messages",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": self.anthropic_version,
            },
            method="POST",
        )
        # The Anthropic API and the network path to it intermittently return transient
        # errors (rate limits, 5xx, DNS blips). Retry those with exponential backoff;
        # fail fast on non-transient errors (bad request, auth, not-found).
        _TRANSIENT = {408, 429, 500, 502, 503, 504}
        for attempt in range(self.max_retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    data = json.loads(response.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                last_exc = LlmError(f"Claude request failed: HTTP {exc.code}: {body}")
                if exc.code not in _TRANSIENT or attempt == self.max_retries:
                    raise last_exc from exc
            except (urllib.error.URLError, TimeoutError) as exc:
                last_exc = LlmError(f"Claude request failed: {exc}")
                if attempt == self.max_retries:
                    raise last_exc from exc
            time.sleep(self.retry_backoff * (2 ** attempt))
        try:
            return "".join(part.get("text", "") for part in data["content"] if part.get("type") == "text")
        except (KeyError, TypeError) as exc:
            raise LlmError(f"Unexpected Claude response shape: {data}") from exc


class LoggedLlmClient:
    """Logs every LLM input/output to stderr and optionally JSONL."""

    def __init__(
        self,
        inner,
        terminal: bool = True,
        jsonl_path: Optional[Path] = None,
        reset_jsonl: bool = True,
    ):
        self.inner = inner
        self.terminal = terminal
        self.jsonl_path = jsonl_path
        self.call_index = 0
        if self.jsonl_path is not None:
            self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
            if reset_jsonl and self.jsonl_path.exists():
                self.jsonl_path.unlink()

    def chat(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.0,
        stage: str = "unknown",
        max_tokens: Optional[int] = None,
        output_config: Optional[dict] = None,
    ) -> str:
        self.call_index += 1
        call_id = self.call_index
        started = time.time()
        self._print_start(call_id, stage, messages, temperature, max_tokens)
        kwargs = {"temperature": temperature}
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if output_config is not None:
            kwargs["output_config"] = output_config
        try:
            response = self.inner.chat(messages, **kwargs)
        except Exception as exc:
            duration = time.time() - started
            record = {
                "call_id": call_id,
                "stage": stage,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "messages": [_message_dict(message) for message in messages],
                "response": "",
                "error": f"{type(exc).__name__}: {exc}",
                "duration_seconds": duration,
            }
            self._write_record(record)
            self._print_error(call_id, stage, exc, duration)
            raise
        duration = time.time() - started
        record = {
            "call_id": call_id,
            "stage": stage,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [_message_dict(message) for message in messages],
            "response": response,
            "error": "",
            "duration_seconds": duration,
        }
        self._write_record(record)
        self._print_response(call_id, stage, response, duration)
        return response

    def _write_record(self, record: Dict[str, object]) -> None:
        if self.jsonl_path is None:
            return
        with self.jsonl_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")

    def _print_start(
        self,
        call_id: int,
        stage: str,
        messages: List[ChatMessage],
        temperature: float,
        max_tokens: Optional[int],
    ) -> None:
        if not self.terminal:
            return
        sys.stderr.write(f"\n\n========== LLM CALL {call_id}: {stage} INPUT ==========\n")
        sys.stderr.write(f"temperature: {temperature}\n")
        if max_tokens is not None:
            sys.stderr.write(f"max_tokens: {max_tokens}\n")
        for index, message in enumerate(messages, start=1):
            sys.stderr.write(f"\n--- message {index} role={message.role} ---\n")
            sys.stderr.write(message.content)
            if not message.content.endswith("\n"):
                sys.stderr.write("\n")
        sys.stderr.write(f"========== END LLM CALL {call_id}: {stage} INPUT ==========\n")
        sys.stderr.flush()

    def _print_response(self, call_id: int, stage: str, response: str, duration: float) -> None:
        if not self.terminal:
            return
        sys.stderr.write(f"\n========== LLM CALL {call_id}: {stage} OUTPUT ({duration:.2f}s) ==========\n")
        sys.stderr.write(response)
        if not response.endswith("\n"):
            sys.stderr.write("\n")
        sys.stderr.write(f"========== END LLM CALL {call_id}: {stage} OUTPUT ==========\n")
        sys.stderr.flush()

    def _print_error(self, call_id: int, stage: str, exc: Exception, duration: float) -> None:
        if not self.terminal:
            return
        sys.stderr.write(f"\n========== LLM CALL {call_id}: {stage} ERROR ({duration:.2f}s) ==========\n")
        sys.stderr.write(f"{type(exc).__name__}: {exc}\n")
        sys.stderr.write(f"========== END LLM CALL {call_id}: {stage} ERROR ==========\n")
        sys.stderr.flush()


def _message_dict(message: ChatMessage) -> Dict[str, str]:
    return {"role": message.role, "content": message.content}


def make_llm_client(mode: str = "claude", config: Optional[Dict[str, str]] = None):
    config = config or {}
    if mode == "vllm":
        return VllmOpenAIClient(
            base_url=config.get("base_url", "http://localhost:8000/v1"),
            model=config.get("model", "Qwen/Qwen2.5-7B-Instruct"),
            api_key=config.get("api_key", "EMPTY"),
            timeout=float(config.get("timeout", 180)),
            max_tokens=int(config.get("max_tokens", 2048)),
            max_retries=int(config.get("max_retries", 4)),
            retry_backoff=float(config.get("retry_backoff", 2.0)),
            strip_reasoning=bool(config.get("strip_reasoning", True)),
        )
    if mode in {"claude", "anthropic"}:
        return AnthropicClaudeClient(
            base_url=config.get("base_url", "https://api.anthropic.com/v1"),
            model=config.get("model", "claude-sonnet-4-20250514"),
            api_key=config.get("api_key"),
            api_key_env=config.get("api_key_env", "ANTHROPIC_API_KEY"),
            timeout=float(config.get("timeout", 60)),
            max_tokens=int(config.get("max_tokens", 2048)),
            max_retries=int(config.get("max_retries", 4)),
            retry_backoff=float(config.get("retry_backoff", 2.0)),
        )
    raise ValueError(f"Unsupported LLM mode: {mode}")
