"""Provider adapters with persistent request/response audit and transport-only retries."""
from __future__ import annotations
from dataclasses import asdict
import json
import os
from pathlib import Path
import time
import httpx
from verifiqa.generation.llm_client import strip_reasoning
from .common import fingerprint, write_json

class ApiError(RuntimeError): pass

class Client:
    def __init__(self, config, cache, dataset, transport=None):
        self.config, self.cache, self.dataset = config, Path(cache), dataset
        self.transport = transport

    def payload(self, messages, *, stage, temperature=0, max_tokens=None):
        c = self.config
        params = {**c.get('parameters', {}), **c.get('dataset_parameters', {}).get(self.dataset, {})}
        budget = params.pop('max_tokens', max_tokens or c.get('max_tokens', 4096))
        payload = {'model': c['model'], 'messages': [asdict(m) if hasattr(m, '__dataclass_fields__') else dict(m) for m in messages]}
        if c['provider'] == 'anthropic':
            payload['max_tokens'] = budget
        else:
            payload[c.get('token_parameter', 'max_tokens')] = budget
        if c.get('temperature', 0) is not None:
            payload['temperature'] = c.get('temperature', temperature)
        payload.update(params)
        return payload

    def chat(self, messages, temperature=0, stage='unknown', max_tokens=None, **kwargs):
        c = self.config
        base = os.environ.get(c.get('base_url_env', ''), c.get('base_url', '')).rstrip('/')
        if not base: raise ApiError('missing_endpoint:'+c['model'])
        payload = self.payload(messages, stage=stage, temperature=temperature, max_tokens=max_tokens)
        key = fingerprint({'base_url': base, 'provider': c['provider'], 'payload': payload, 'stage': stage})
        path = self.cache/(key+'.json')
        if path.exists(): return json.loads(path.read_text(encoding='utf-8'))['text']
        api_key = os.environ.get(c.get('api_key_env', ''), '')
        if not api_key and not c.get('allow_empty_key', False):
            raise ApiError('missing_api_key_env:'+c.get('api_key_env', ''))
        headers = {'Content-Type': 'application/json', 'User-Agent': 'VeriFin-reproduction/0.1'}
        if c['provider'] == 'anthropic':
            headers.update({'x-api-key': api_key, 'anthropic-version': '2023-06-01'})
            endpoint = base+'/messages'
        else:
            headers['Authorization'] = 'Bearer '+(api_key or 'EMPTY')
            endpoint = base+'/chat/completions'
        for attempt in range(c.get('retries', 3)+1):
            try:
                with httpx.Client(timeout=c.get('timeout_seconds', 240), transport=self.transport) as http:
                    r = http.post(endpoint, headers=headers, json=payload)
                if r.status_code >= 400:
                    if r.status_code not in {408,429,500,502,503,504} or attempt == c.get('retries',3):
                        # Provider bodies can echo credentials; never persist/print them.
                        raise ApiError('provider_http_'+str(r.status_code))
                    time.sleep(min(2**attempt, 16)); continue
                data = r.json()
                if c['provider'] == 'anthropic':
                    if data.get('stop_reason') == 'max_tokens': raise ApiError('truncated_response')
                    text = ''.join(x['text'] for x in data['content'] if x.get('type') == 'text')
                else:
                    choice = data['choices'][0]
                    if choice.get('finish_reason') == 'length': raise ApiError('truncated_response')
                    text = choice['message']['content']
                if not isinstance(text, str) or not text.strip(): raise ApiError('empty_response')
                text = strip_reasoning(text)
                write_json(path, {'request_hash':key,'endpoint':endpoint,'stage':stage,'request':payload,
                                 'text':text,'usage':data.get('usage'), 'response_id':data.get('id'),
                                 'reported_model':data.get('model'), 'system_fingerprint':data.get('system_fingerprint')})
                return text
            except (httpx.TransportError, httpx.TimeoutException):
                if attempt == c.get('retries',3): raise ApiError('transport_retries_exhausted') from None
                time.sleep(min(2**attempt,16))
        raise ApiError('provider_retries_exhausted')
