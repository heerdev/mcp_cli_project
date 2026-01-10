# mcp_server.py
from os import name
from mcp.server.fastmcp import FastMCP
from pydantic import Field

# Initialize MCP server
mcp = FastMCP("DocumentMCP", host="127.0.0.1", port=6274)

# In-memory document store
docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures.",
    "outlook.pdf": "This document presents the projected future performance of the system.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
}

# -------------------- TOOLS --------------------

@mcp.tool(
    name="read_doc",
    description="Reads the contents of a document given its ID.",
)
def read_doc(doc_id: str = Field(description="The ID of the document to read")):
    if doc_id not in docs:
        raise ValueError(f"Document {doc_id} not found")
    return docs[doc_id]


@mcp.tool(
    name="edit_doc",
    description="Edits the contents of a document given its ID and new content.",
)
def edit_doc(
    doc_id: str = Field(description="The ID of the document to edit"),
    new_content: str = Field(description="The new content for the document")
):
    if doc_id not in docs:
        raise ValueError(f"Document {doc_id} not found")
    docs[doc_id] = new_content
    return f"Document {doc_id} updated successfully."


# -------------------- RESOURCES --------------------

@mcp.resource("docs://deposition.md")
def get_deposition():
    return docs["deposition.md"]

@mcp.resource("docs://report.pdf")
def get_report():
    return docs["report.pdf"]

@mcp.resource("docs://financials.docx")
def get_financials():
    return docs["financials.docx"]

@mcp.resource("docs://outlook.pdf")
def get_outlook():
    return docs["outlook.pdf"]

@mcp.resource("docs://plan.md")
def get_plan():
    return docs["plan.md"]

@mcp.resource("docs://spec.txt")
def get_spec():
    return docs["spec.txt"]

if __name__ == "__main__":
    # Use "stdio" for MCPClient, optional "http" for LocalAI / web clients
    mcp.run()
    # For HTTP transport (optional), uncomment:
    # mcp.run(transport="sse")
