import json

import requests

from typing import List, Dict





class LLMClient:
    def __init__(self, api_url: str):
        self.api_url = api_url

    def chat(self, messages: List[Dict[str, str]], model: str = "command-r7b",
             temperature: float = 0.7, max_tokens: int = 1000) -> dict:
        try:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise e