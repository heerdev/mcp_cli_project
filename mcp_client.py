
import asyncio
from typing import Any
import httpx
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from mcp.client.stdio import StdioServerParameters


class MCPStdioClient:
    """
    Simple stdio-based MCP client.
    """

    def __init__(self, command: str, args: list[str]):
        self.command = command
        self.args = args
        self.session = None
        self.stdio_context = None

    async def __aenter__(self):
        server_params = StdioServerParameters(command=self.command, args=self.args)
        self.stdio_context = stdio_client(server_params)
        read, write = await self.stdio_context.__aenter__()
        self.session = ClientSession(read, write)
        await self.session.__aenter__()
        await self.session.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.__aexit__(exc_type, exc_val, exc_tb)
        if self.stdio_context:
            await self.stdio_context.__aexit__(exc_type, exc_val, exc_tb)

    async def list_tools(self):
        result = await self.session.list_tools()
        return result.tools

    async def call_tool(self, name: str, arguments: dict):
        result = await self.session.call_tool(name, arguments)
        return result.content

    async def list_resources(self):
        result = await self.session.list_resources()
        return result.resources

    async def read_resource(self, uri: str):
        result = await self.session.read_resource(uri)
        return result.content


class MCPHttpClient:
    """
    Simple HTTP-based MCP client to call tools, list docs, or prompts.
    """

    def __init__(self, base_url: str = "http://127.0.0.1:6274", auth_token: str = '19b3b6eaf79b238eca8c274466f89ee632036584f3707b9cb0bb81f8aab3853'):
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.client = httpx.AsyncClient(timeout=30.0)
        self.request_id = 0
        self.session_id = None
        self.initialized = False

    async def _send_request(self, method: str, params: dict) -> dict:
        # Skip initialization for stateless HTTP
        self.request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params
        }
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        resp = await self.client.post(f"{self.base_url}/mcp", json=payload, headers=headers)
        resp.raise_for_status()
        result = resp.json()
        if "error" in result:
            raise Exception(f"MCP error: {result['error']}")
        return result["result"]

    async def _initialize(self):
        """Initialize the MCP session."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "mcp-cli", "version": "1.0"}
            }
        }
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        resp = await self.client.post(f"{self.base_url}/mcp", json=payload, headers=headers)
        resp.raise_for_status()
        result = resp.json()
        if "error" in result:
            raise Exception(f"MCP initialization error: {result['error']}")
        
        # Extract session ID from response headers
        self.session_id = resp.headers.get("mcp-session-id")
        self.initialized = True
        
        # Send initialized notification
        await self._send_notification("notifications/initialized", {})

    async def _send_notification(self, method: str, params: dict):
        """Send a notification (no response expected)."""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        if self.session_id:
            headers["mcp-session-id"] = self.session_id
        await self.client.post(f"{self.base_url}/mcp", json=payload, headers=headers)

    async def list_tools(self) -> list[dict[str, Any]]:
        result = await self._send_request("tools/list", {})
        return result.get("tools", [])

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        result = await self._send_request("tools/call", {"name": tool_name, "arguments": arguments})
        return result

    async def list_docs(self) -> list[str]:
        result = await self._send_request("resources/list", {})
        return [r["uri"] for r in result.get("resources", [])]

    async def get_doc(self, doc_id: str) -> str:
        result = await self._send_request("resources/read", {"uri": f"docs://{doc_id}"})
        return result.get("contents", [{}])[0].get("text", "")

    async def close(self):
        await self.client.aclose()


# --------------- Testing ------------------
async def main():
    client = MCPHttpClient()  # MCP server HTTP URL

    print("Available tools:")
    tools = await client.list_tools()
    print(tools)

    print("\nDocuments:")
    docs = await client.list_docs()
    print(docs)

    if docs:
        doc_content = await client.get_doc(docs[0])
        print(f"\nContent of {docs[0]}:\n{doc_content}")

    # Example tool call
    if "read_doc" in [t["name"] for t in tools]:
        result = await client.call_tool("read_doc", {"doc_id": docs[0]})
        print(f"\nTool result for read_doc:\n{result}")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
