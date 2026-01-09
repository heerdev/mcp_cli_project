from typing import List, Tuple

from core.chat import Chat
from mcp_client import MCPClient
from core.types import Message


class CliChat(Chat):
    def __init__(
        self,
        doc_client: MCPClient,
        clients: dict[str, MCPClient],
        llm_service,
    ):
        super().__init__(llm_service=llm_service, clients=clients)
        self.doc_client = doc_client

    # ---------- MCP document helpers ----------

    async def list_prompts(self):
        return await self.doc_client.list_prompts()

    async def list_docs_ids(self) -> list[str]:
        return await self.doc_client.read_resource("docs://documents")

    async def get_doc_content(self, doc_id: str) -> str:
        return await self.doc_client.read_resource(
            f"docs://documents/{doc_id}"
        )

    async def get_prompt(self, command: str, doc_id: str):
        return await self.doc_client.get_prompt(
            command, {"doc_id": doc_id}
        )

    # ---------- Query processing ----------

    async def _extract_resources(self, query: str) -> str:
        mentions = [word[1:] for word in query.split() if word.startswith("@")]
        if not mentions:
            return ""

        doc_ids = await self.list_docs_ids()
        mentioned_docs: list[Tuple[str, str]] = []

        for doc_id in doc_ids:
            if doc_id in mentions:
                content = await self.get_doc_content(doc_id)
                mentioned_docs.append((doc_id, content))

        return "".join(
            f'\n<document id="{doc_id}">\n{content}\n</document>\n'
            for doc_id, content in mentioned_docs
        )

    async def _process_command(self, query: str) -> bool:
        if not query.startswith("/"):
            return False

        words = query.split()
        if len(words) < 2:
            return True  # swallow invalid command

        command = words[0][1:]
        doc_id = words[1]

        prompt_messages = await self.get_prompt(command, doc_id)

        # Flatten prompt messages into plain text
        for msg in prompt_messages:
            role = "user" if msg["role"] == "user" else "assistant"
            content = msg.get("content", "")
            if isinstance(content, list):
                content = "\n".join(
                    item.get("text", "") for item in content if isinstance(item, dict)
                )
            self.messages.append(
                {"role": role, "content": str(content)}
            )

        return True

    async def _process_query(self, query: str):
        if await self._process_command(query):
            return

        added_resources = await self._extract_resources(query)

        prompt = f"""
The user has a question:
<query>
{query}
</query>

The following context may be useful:
<context>
{added_resources}
</context>

Answer the user's question directly and concisely.
Do NOT mention the context or documents explicitly.
"""

        self.messages.append(
            {"role": "user", "content": prompt.strip()}
        )
