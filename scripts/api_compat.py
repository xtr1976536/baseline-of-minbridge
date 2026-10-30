"""用 OpenAI-compatible API 调用作者原有 prompt；不改 prompt 或采样参数。"""
import os


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
    if style == "completion":
        response = openai.Completion.create(prompt=prompt, frequency_penalty=0.0,
                                            presence_penalty=0.0, **common)
        text = response["choices"][0]["text"]
    elif style == "chat":
        response = openai.ChatCompletion.create(
            messages=[{"role": "user", "content": prompt}], **common)
        text = response["choices"][0]["message"]["content"]
    else:
        raise ValueError("api_style 必须为 auto、completion 或 chat")
    if hasattr(response, "to_dict_recursive"):
        response = response.to_dict_recursive()
    return text, response, style, model
