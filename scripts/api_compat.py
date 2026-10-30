"""用 OpenAI-compatible API 调用作者原有 prompt；不改 prompt 或采样参数。"""
import os
import time

def retry_call(fn, **kwargs):
    import openai
    for attempt in range(8):
        try:return fn(**kwargs)
        except (openai.error.ServiceUnavailableError,openai.error.RateLimitError,
                openai.error.Timeout,openai.error.APIConnectionError):
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
    return text, response, style, model
