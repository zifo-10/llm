from typing import List, Dict

import requests


class LLMClient:
    def __init__(self, api_url: str):
        self.api_url = api_url

    def chat(self, messages: List[Dict[str, str]], model: str = "command-r7b",
             temperature: float = 0.2, max_tokens: int = 800) -> dict:
        try:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": 0.1,
            }

            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise e
