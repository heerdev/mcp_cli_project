import httpx
from typing import List
from core.types import Message

class LocalAILLM:
    def __init__(
        self,
        endpoint: str = "http://localhost:8080/v1/completions",
        model: str = "LiquidAI.LFM2-2.6B-Transcript-GGUF",
        max_tokens: int = 512,
    ):
        self.endpoint = endpoint
        self.model = model
        self.max_tokens = max_tokens

    async def chat(self, messages: List[Message]) -> str:
        prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
        payload = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens": self.max_tokens,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(self.endpoint, json=payload)
            response.raise_for_status()
            data = response.json()
            print("LocalAI response data:", data)

        # Extract text from LocalAI response (support multiple formats)
        if "choices" in data and len(data["choices"]) > 0:
            choice = data["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                return choice["message"]["content"]
            if "text" in choice:
                return choice["text"]
            if "content" in choice:
                return choice["content"]

        return "No text returned"
