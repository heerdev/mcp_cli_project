# main_http.py
import asyncio
import sys
from contextlib import AsyncExitStack
from dotenv import load_dotenv
from mcp_client import MCPStdioClient
from core.cli_chat import CliChat
from core.cli import CliApp
from core.localai import LocalAILLM

load_dotenv()

LOCALAI_ENDPOINT = "http://localhost:8080/v1/completions"
# MCP_HTTP_URL = "http://localhost:6274/"  # Your MCP server URL
# MCP_AUTH_TOKEN = None  # Auth disabled

async def main():
    llm_service = LocalAILLM(endpoint=LOCALAI_ENDPOINT)
    server_scripts = sys.argv[1:]
    clients = {}

    async with AsyncExitStack() as stack:
        # Use stdio client
        doc_client = await stack.enter_async_context(MCPStdioClient(command="uv", args=["run", "python", "mcp_server.py"]))
        clients["doc_client"] = doc_client

        # If you have other MCP servers, you can still launch them
        for i, server_script in enumerate(server_scripts):
            client_id = f"client_{i}_{server_script}"
            # Here we can add stdio clients
            client = await stack.enter_async_context(MCPStdioClient(command="uv", args=["run", "python", server_script]))
            clients[client_id] = client

        # Create chat client
        chat_client = CliChat(
            doc_client=doc_client,
            clients=clients,
            llm_service=llm_service
        )

        cli = CliApp(chat_client)
        await cli.initialize()
        await cli.run()

        # Close is handled by context

if __name__ == "__main__":
    asyncio.run(main())
