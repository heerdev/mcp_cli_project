from typing import TypedDict, Literal, Any


class Message(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str


class ToolCall(TypedDict):
    tool: str
    arguments: dict[str, Any]


class ToolResult(TypedDict):
    name: str
    result: Any
