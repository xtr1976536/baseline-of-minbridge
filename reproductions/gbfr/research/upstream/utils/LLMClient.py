import os
import yaml
import logging

logger = logging.getLogger("GBFR")


class LLMResponse:
    def __init__(self, content: str):
        self.content = content


class LLMWrapper:
    def __init__(self, model_name: str = "openai", config_path: str = None):
        self.model_name = model_name
        self.config_path = config_path
        self._client = None
        self.model_id = None
        self.base_url = None
        self.api_key = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI

                if self.config_path is None:
                    possible_paths = [
                        os.path.join(os.path.dirname(__file__), '..', 'llm_config.yaml'),
                        os.path.join(os.path.dirname(__file__), 'llm_config.yaml'),
                        './llm_config.yaml',
                    ]
                    for path in possible_paths:
                        if os.path.exists(path):
                            self.config_path = path
                            break

                if self.config_path is None or not os.path.exists(self.config_path):
                    raise FileNotFoundError(f"Cannot find LLM config file: {self.config_path}")

                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                llm_config = config.get('llm_config', {})
                if self.model_name not in llm_config:
                    available = list(llm_config.keys())
                    raise ValueError(f"Unknown model config: {self.model_name}, available: {available}")

                model_config = llm_config[self.model_name]
                self.model_id = model_config['model_name']
                self.base_url = model_config['url']
                self.api_key = model_config['api_key']

                self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            except Exception as e:
                logger.warning(f"Failed to initialize LLM client: {e}")
                self._client = None
        return self._client

    def invoke(self, prompt, system_prompt: str = None, temperature: float = 0.1,
               max_tokens: int = 16384) -> LLMResponse:
        if isinstance(prompt, list):
            messages = prompt
        else:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

        client = self._get_client()
        if client is None:
            return LLMResponse("Mock response - LLM not configured")

        try:
            if self.model_name.startswith('qwen') or self.model_name == 'kimi':
                response = client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                temperature=temperature,
                extra_body={"enable_thinking": False}
            )
            else:
                response = client.chat.completions.create(
                    model=self.model_id,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            content = response.choices[0].message.content
            return LLMResponse(content)
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise


def create_llm(model_name: str = "openai") -> LLMWrapper:
    return LLMWrapper(model_name=model_name)