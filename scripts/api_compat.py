"""用 OpenAI-compatible API 调用作者原有 prompt；不改 prompt 或采样参数。"""
import os
import time

def retry_call(fn, **kwargs):
    import openai
    import requests
    for attempt in range(8):
        try:
            if 'messages' in kwargs:
                payload=dict(kwargs);timeout=payload.pop('request_timeout',120)
                response=requests.post(openai.api_base.rstrip('/')+'/chat/completions',
                    headers={'Authorization':'Bearer '+openai.api_key},json=payload,timeout=timeout)
                if response.status_code in (429,500,502,503,504):
                    print(f'API temporary HTTP {response.status_code}; retry {attempt+1}/8',flush=True)
                    raise openai.error.ServiceUnavailableError(f'Temporary model service failure HTTP {response.status_code}')
                response.raise_for_status()
                data=response.json()
                if not isinstance(data,dict) or not data.get('choices'):
                    raise openai.error.ServiceUnavailableError('Empty or malformed API response')
                if not isinstance(data['choices'],list) or not isinstance(data['choices'][0],dict):
                    raise openai.error.ServiceUnavailableError('Malformed choices')
                message=data['choices'][0].get('message') or {}
                if not isinstance(message.get('content'),str) or not message['content'].strip():
                    raise openai.error.ServiceUnavailableError('Missing model output in API response')
                return data
            return fn(**kwargs)
        except (openai.error.ServiceUnavailableError,openai.error.RateLimitError,
                openai.error.Timeout,openai.error.APIConnectionError,
                requests.exceptions.Timeout,requests.exceptions.ConnectionError,ValueError):
            if attempt==7:raise
            time.sleep(min(2**attempt,30))


def generate(prompt, reference_model, api_model=None, api_style="auto", max_tokens=1024,
             temperature=0.0, stop="------", request_timeout=120):
    import openai

    model = api_model or reference_model
    style = api_style
    if style == "auto":
        style = "completion" if reference_model.startswith(("text-", "code-")) else "chat"
    openai.api_key = os.environ["OPENAI_API_KEY"]
    openai.api_base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    common = dict(model=model, temperature=temperature, max_tokens=max_tokens,
                  top_p=1.0, stop=stop, request_timeout=request_timeout)
    if 'deepseek.com' in openai.api_base:
        common['thinking']={'type':'disabled'}
    if style == "completion":
        response = retry_call(openai.Completion.create,prompt=prompt, frequency_penalty=0.0,
                                            presence_penalty=0.0, **common)
        text = response["choices"][0]["text"]
    elif style == "chat":
        response = retry_call(openai.ChatCompletion.create,
            messages=[{"role": "user", "content": prompt}], **common)
        text = response["choices"][0]["message"]["content"]
    else:
        raise ValueError("api_style 必须为 auto、completion 或 chat")
    if hasattr(response, "to_dict_recursive"):
        response = response.to_dict_recursive()
    # Record the actual request without headers, credentials, or endpoint secrets.
    response['_minbridge_request'] = {
        'model': model, 'api_style': style, 'temperature': temperature,
        'max_tokens': max_tokens, 'top_p': 1.0, 'stop': stop,
        'messages': [{'role': 'user', 'content': prompt}] if style == 'chat' else None,
        'prompt': prompt if style == 'completion' else None,
    }
    usage = response.get('usage') or {}
    completion = usage.get('completion_tokens')
    reasoning = (usage.get('completion_tokens_details') or {}).get('reasoning_tokens', 0)
    # usage is provider-reported billing/accounting metadata, not an independent
    # measurement of returned text. Preserve mismatches; do not reject or regenerate
    # valid completions based only on this counter.
    if isinstance(completion, int) and isinstance(reasoning, int) and completion - reasoning > max_tokens:
        warning = {'kind':'provider_usage_above_requested_budget',
                   'reported_completion_tokens':completion,'reported_reasoning_tokens':reasoning,
                   'reported_difference':completion-reasoning,'requested_max_tokens':max_tokens,
                   'action':'retain original output unchanged; no truncation or regeneration'}
        try:
            import tiktoken
            warning['independent_text_tokens']={name:len(tiktoken.get_encoding(name).encode(text))
                for name in ('o200k_base','cl100k_base')}
            warning['tokenizer_note']='Diagnostic only; relay model tokenizer is not independently authenticated.'
        except ImportError:
            warning['tokenizer_note']='Independent tokenizer unavailable; raw usage and output retained.'
        response['_minbridge_audit_warnings']=[warning]
    return text.strip(), response, style, model
