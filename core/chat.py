from typing import Dict, List
import json

from mcp_client import MCPClient
from typing import List
from core.types import Message
from core.tools import ToolManager


class Chat:
    def __init__(self, llm_service, clients: dict[str, MCPClient]):
        self.llm = llm_service
        self.clients = clients
        self.messages: List[Message] = []
        self._system_initialized = False

    async def _process_query(self, query: str):
        self.messages.append({"role": "user", "content": query})

    async def _ensure_system_prompt(self):
        if self._system_initialized:
            return

        tools = await ToolManager.get_all_tools(self.clients)

        system_prompt = f"""
You are an AI assistant with access to tools.

When you need to call a tool, respond ONLY with valid JSON in this exact form:
{{
  "tool": "<tool_name>",
  "arguments": {{ ... }}
}}

Do NOT include any extra text.

Available tools:
{json.dumps(tools, indent=2)}
"""

        self.messages.insert(
            0, {"role": "system", "content": system_prompt.strip()}
        )
        self._system_initialized = True

    async def run(self, query: str) -> str:
        await self._ensure_system_prompt()
        await self._process_query(query)

        for _ in range(10):  # safety guard
            response_text = await self.llm.chat(self.messages)

            # Attempt tool call parsing
            try:
                parsed = json.loads(response_text)
                if not is_tool_call(parsed):
                    self.messages.append({"role": "assistant", "content": response_text})
                    return response_text
            
                if not isinstance(parsed, dict):
                    raise ValueError
                tool_name = parsed.get("tool")
                tool_args = parsed.get("arguments")

                if not tool_name or not isinstance(tool_args, dict):
                    raise ValueError
            except Exception:
                # Normal assistant response
                self.messages.append(
                    {"role": "assistant", "content": response_text}
                )
                return response_text

            # Execute tool
            tool_result = await ToolManager.execute_tool(
                self.clients, tool_name, tool_args
            )

            # Feed tool result back to model
            self.messages.append(
                {
                    "role": "user",
                    "content": (
                        f"TOOL RESULT ({tool_name}):\n"
                        f"{json.dumps(tool_result, indent=2)}"
                    ),
                }
            )

        return "Error: tool execution loop exceeded limit."
    
def is_tool_call(obj):
    return (
        isinstance(obj, dict)
        and "tool" in obj
        and "arguments" in obj
        and isinstance(obj["arguments"], dict)
    )