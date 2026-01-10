import json
from typing import Optional

from mcp.types import CallToolResult, Tool, TextContent
from mcp_client import MCPHttpClient


class ToolManager:
    @classmethod
    async def get_all_tools(cls, clients: dict[str, MCPHttpClient]) -> list[Tool]:
        """Collect all tools from all MCP clients."""
        tools: list[Tool] = []
        for client in clients.values():
            tool_models = await client.list_tools()
            tools.extend(
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.inputSchema,
                }
                for t in tool_models
            )
        return tools

    @classmethod
    async def _find_client_with_tool(
        cls, clients: dict[str, MCPHttpClient], tool_name: str
    ) -> Optional[MCPHttpClient]:
        for client in clients.values():
            tools = await client.list_tools()
            if any(t.name == tool_name for t in tools):
                return client
        return None

    @classmethod
    async def execute_tool(
        cls,
        clients: dict[str, MCPHttpClient],
        tool_name: str,
        tool_args: dict,
    ):
        """Execute a single MCP tool and return plain JSON-friendly output."""
        client = await cls._find_client_with_tool(clients, tool_name)

        if not client:
            return {"error": f"Tool '{tool_name}' not found"}

        try:
            tool_output: CallToolResult | None = await client.call_tool(
                tool_name, tool_args
            )

            if not tool_output:
                return {"result": None}

            texts = [
                item.text
                for item in tool_output.content
                if isinstance(item, TextContent)
            ]

            return {
                "result": texts,
                "is_error": tool_output.isError,
            }

        except Exception as e:
            return {
                "error": f"Error executing tool '{tool_name}': {e}"
            }
