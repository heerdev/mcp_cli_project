import httpx
from typing import List, Dict


class OllamaLLM:
    def __init__(self, model: str, host: str = "http://localhost:11434"):
        self.model = model
        self.host = host.rstrip("/")

    async def chat(self, messages: List[Dict]) -> str:
        prompt = "\n".join(
            f"{m['role']}: {m['content']}" for m in messages
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.host}/api/generate",
                json=payload,
                timeout=300,
            )
            response.raise_for_status()
            data = response.json()

        # ✅ FIX HERE
        return data["response"]
