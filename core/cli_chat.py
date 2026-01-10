from typing import List, Tuple
from core.chat import Chat
from mcp_client import MCPHttpClient # <- HTTP client
from core.types import Message

class CliChat(Chat):
    def __init__(self, doc_client: MCPHttpClient, clients: dict[str, MCPHttpClient], llm_service):
        super().__init__(llm_service=llm_service, clients=clients)
        self.doc_client = doc_client

    async def list_docs_ids(self) -> list[str]:
        return await self.doc_client.list_docs()

    async def get_doc_content(self, doc_id: str) -> str:
        return await self.doc_client.get_doc(doc_id)

    async def get_prompt(self, command: str, doc_id: str):
        # Assuming your MCP server has a prompt endpoint
        # Otherwise, return empty list for now
        return []

    async def list_prompts(self):
        # For now, return empty list as no prompts are defined
        return []
