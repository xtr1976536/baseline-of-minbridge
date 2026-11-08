"""One GPT-4o for query, judge, and PoT, with durable per-stage caching."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
import time

import httpx

from .common import digest, read_json, write_json


class APIError(RuntimeError):
    def __init__(self, message, *, fatal=False):
        super().__init__(message)
        self.fatal = fatal


class ChatClient:
    def __init__(self, config, cache_dir, *, transport=None):
        self.config = config
        self.key = os.environ.get(config["api_key_env"], "")
        self.endpoint = os.environ.get(config.get("base_url_env", ""), config["base_url"]).rstrip("/")
        if not self.key or not self.endpoint:
            raise APIError(f"Set {config['api_key_env']} and a valid Base URL")
        if not self.endpoint.startswith(("https://", "http://localhost", "http://127.0.0.1")):
            raise APIError("Remote API endpoint must use HTTPS")
        parameters = config.get("parameters", {})
        if {"model", "messages", "stream", "n"} & parameters.keys():
            raise ValueError("Parameters cannot override protocol fields")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.http = httpx.AsyncClient(timeout=config.get("timeout_seconds", 180), transport=transport)
        self.semaphore = asyncio.Semaphore(config.get("concurrency", 2))
        self.rate_lock = asyncio.Lock()
        self.next_request = 0.0
        self.interval = 60 / max(config.get("requests_per_minute", 30), 1)

    async def close(self):
        await self.http.aclose()

    async def complete(self, messages, scope, *, response_format=None):
        body = {"model": self.config["model"], "messages": messages, "stream": False, "n": 1,
                **self.config.get("parameters", {})}
        if response_format is not None:
            if "response_format" in self.config.get("parameters", {}):
                raise ValueError("Stage response format conflicts with global parameters")
            body["response_format"] = response_format
        identity = digest({"endpoint": self.endpoint, "body": body, "scope": scope})
        path = self.cache_dir / f"{identity}.json"
        if path.exists():
            cached = read_json(path)
            if cached.get("identity") != identity or digest(cached["response"]) != cached.get("response_digest"):
                raise APIError("API cache checksum mismatch")
            return {**cached["response"], "cached": True}
        for attempt in range(self.config.get("retries", 3)+1):
            try:
                async with self.semaphore:
                    async with self.rate_lock:
                        now = time.monotonic()
                        delay = max(0, self.next_request-now)
                        self.next_request = max(now, self.next_request) + self.interval
                    if delay:
                        await asyncio.sleep(delay)
                    response = await self.http.post(self.endpoint + "/chat/completions", json=body,
                                                    headers={"Authorization": "Bearer " + self.key})
            except httpx.TransportError:
                if attempt == self.config.get("retries", 3):
                    raise APIError("API transport failed; no generated answer") from None
                await asyncio.sleep(min(2**attempt, 10))
                continue
            if response.status_code == 429 or response.status_code >= 500:
                if attempt < self.config.get("retries", 3):
                    await asyncio.sleep(min(2**attempt, 10))
                    continue
            if not response.is_success:
                # Stop the run on invalid credentials, endpoint/model, or exhausted
                # quota; do not spend requests repeating a permanent error per row.
                try:
                    payload = response.json()
                    error = payload.get("error", payload)
                    code = str(error.get("code", "")) if isinstance(error, dict) else ""
                except (ValueError, AttributeError):
                    code = ""
                quota = any(term in code.lower() for term in ["quota", "balance", "credit", "funds"])
                fatal = response.status_code in (400, 401, 402, 403, 404) or quota
                raise APIError(f"API returned HTTP {response.status_code}", fatal=fatal)
            try:
                raw = response.json()
                choice = raw["choices"][0]
                if choice.get("finish_reason") != "stop":
                    raise APIError("Completion was truncated, refused, or incomplete")
                content = choice["message"]["content"]
                if not isinstance(content, str) or not content.strip():
                    raise APIError("Completion lacks nonempty text content")
                result = {"content": content, "usage": raw.get("usage", {}),
                          "model_returned": raw.get("model"), "system_fingerprint": raw.get("system_fingerprint"),
                          "request_model": body["model"]}
            except (ValueError, KeyError, TypeError, IndexError):
                raise APIError("Invalid Chat Completions response") from None
            write_json(path, {"identity": identity, "response_digest": digest(result), "response": result})
            return {**result, "cached": False}
        raise APIError("API retry budget exhausted")
