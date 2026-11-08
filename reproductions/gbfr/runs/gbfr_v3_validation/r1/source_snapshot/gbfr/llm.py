"""Configurable chat-completions transport, bounded concurrency and exact cache."""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import time

import httpx

from .types import ProtocolError, dumps


class APIError(RuntimeError):
    def __init__(self,message,*,status_code=None):
        super().__init__(message)
        self.status_code=status_code


def parse_json(text: str) -> dict:
    # A surrounding code fence is syntactic formatting, not another reasoning attempt.
    text = re.sub(r"^```(?:json)?\s*\n?(.*?)\n?```$", r"\1", text.strip(), flags=re.S)
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProtocolError("Operator did not return a single valid JSON object") from exc
    if not isinstance(obj, dict):
        raise ProtocolError("Operator response must be an object")
    return obj


def unwrap_codex_commentary(content: str) -> str:
    """Only strip the gateway's observed {recipients,message} preamble.

    Never select an arbitrary last JSON object or repair model values. Unknown
    prose and multiple ordinary objects remain protocol errors.
    """
    remaining=content.lstrip()
    while remaining.startswith('{'):
        try:
            obj,end=json.JSONDecoder().raw_decode(remaining)
        except (ValueError,RecursionError):
            break
        rest=remaining[end:].lstrip()
        if (isinstance(obj,dict) and set(obj)=={'recipients','message'}
                and obj['recipients']==['user'] and isinstance(obj['message'],str) and rest):
            remaining=rest
        else:
            break
    return remaining


class ChatClient:
    def __init__(self, config: dict, cache_dir: Path, *, transport=None):
        self.config = config
        self.model = config["model"]
        self.base_url = os.environ.get(config.get("base_url_env", ""), config.get("base_url", ""))
        self.api_key = os.environ.get(config["api_key_env"], "")
        if not self.api_key:
            raise APIError(f"Missing environment variable {config['api_key_env']}")
        if not self.base_url:
            raise APIError("Missing endpoint base_url")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.semaphore = asyncio.Semaphore(config.get("concurrency", 8))
        self.http = httpx.AsyncClient(timeout=config.get("timeout_seconds", 180), transport=transport)
        self.records: list[dict] = []
        self.locks: dict[str, asyncio.Lock] = {}
        self.fatal_error: APIError | None=None

    async def close(self):
        await self.http.aclose()

    async def complete(self, task: str, prompt: str, *, json_mode=False) -> str:
        # Identical concurrent requests share one cached response, including when
        # the provider samples stochastically. No competing temporary-file writes.
        identity = dumps([self.model, self.base_url, self.config.get("parameters", {}), prompt,
                          self.config.get('json_response_format') if json_mode else None])
        key = hashlib.sha256(identity.encode()).hexdigest()
        async with self.locks.setdefault(key, asyncio.Lock()):
            return await self._complete(task, prompt,json_mode=json_mode)

    async def _complete(self, task: str, prompt: str, *, json_mode=False) -> str:
        parameters = dict(self.config.get("parameters", {}))
        if json_mode and self.config.get('json_response_format'):
            parameters['response_format']=self.config['json_response_format']
        if {"model", "messages", "stream", "n"} & parameters.keys():
            raise APIError("parameters cannot override model/messages/stream/n")
        messages=[{'role':'user','content':prompt}]
        if self.config.get('system_message'):
            messages.insert(0,{'role':'system','content':self.config['system_message']})
        body = {"model": self.model, "messages": messages,
                "stream": False, "n": 1, **parameters}
        identity = dumps({"endpoint": self.base_url.rstrip("/"), "body": body})
        key = hashlib.sha256(identity.encode()).hexdigest()
        path = self.cache_dir / (key + ".json")
        if path.exists():
            cached = json.loads(path.read_text(encoding="utf-8"))
            self.records.append({"task": task, "cache_key": key, "cached": True, "usage": cached.get("usage", {})})
            return unwrap_codex_commentary(cached['content']) if self.config.get('unwrap_codex_commentary') else cached['content']
        if self.fatal_error is not None:
            raise self.fatal_error
        start = time.monotonic()
        for attempt in range(self.config.get("retries", 3) + 1):
            try:
                async with self.semaphore:
                    if self.fatal_error is not None:
                        raise self.fatal_error
                    response = await self.http.post(
                        self.base_url.rstrip("/") + "/chat/completions", json=body,
                        headers={"Authorization": "Bearer " + self.api_key},
                    )
            except httpx.TransportError as exc:
                if attempt == self.config.get("retries", 3):
                    raise APIError(f"Transport failure ({type(exc).__name__}); no abstention recorded") from None
                await asyncio.sleep(min(2**attempt, 10))
                continue
            if response.status_code == 429 or response.status_code >= 500:
                if attempt < self.config.get("retries", 3):
                    await asyncio.sleep(min(2**attempt, 10))
                    continue
            if not response.is_success:
                # Do not log provider bodies, headers, or secrets.
                error=APIError(f"Chat API returned HTTP {response.status_code}; task={task}",status_code=response.status_code)
                if response.status_code in {401,402,403}:
                    self.fatal_error=error
                raise error
            try:
                raw = response.json()
                choice = raw["choices"][0]
                if choice.get("finish_reason") != "stop":
                    raise APIError(f"Incomplete completion: {choice.get('finish_reason')}")
                content = choice["message"]["content"]
                if not isinstance(content, str) or not content.strip():
                    raise APIError("Empty completion")
            except (ValueError, KeyError, IndexError, TypeError) as exc:
                raise APIError("Invalid chat-completions response") from exc
            final_content=unwrap_codex_commentary(content) if self.config.get('unwrap_codex_commentary') else content
            record = {"content": final_content, "usage": raw.get("usage", {}),
                      "model_returned": raw.get("model"), "system_fingerprint": raw.get("system_fingerprint"),
                      "request_model": self.model, "seconds": time.monotonic()-start}
            if final_content!=content:
                record['raw_content']=content
            tmp = path.with_suffix(".tmp")
            tmp.write_text(dumps(record), encoding="utf-8")
            tmp.replace(path)
            self.records.append({"task": task, "cache_key": key, "cached": False,
                                 "usage": record["usage"], "seconds": record["seconds"]})
            return final_content
        raise APIError("Retry budget exhausted")

    async def json(self, task: str, prompt: str) -> dict:
        return parse_json(await self.complete(task, prompt,json_mode=True))
