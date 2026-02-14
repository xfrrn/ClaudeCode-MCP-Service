# wechat_mcp/core/registry.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict

from mcp_server.core.errors import ERROR_TOOL_NOT_FOUND, ERROR_TOOL_EXECUTION
from mcp_server.core.response import ok, fail_error


Handler = Callable[["AppContext", Dict[str, Any]], Any]


@dataclass
class MCPTool:
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Handler


class ToolRegistry:
    def __init__(self) -> None:
        self.tools: Dict[str, MCPTool] = {}

    def register(self, tool: MCPTool) -> None:
        if tool.name in self.tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self.tools[tool.name] = tool

    def invoke(self, name: str, payload: Dict[str, Any], ctx: "AppContext") -> Dict[str, Any]:
        tool = self.tools.get(name)
        if not tool:
            err = dict(ERROR_TOOL_NOT_FOUND)
            err["message"] = f"Tool not found: {name}"
            return fail_error(err)

        try:
            data = tool.handler(ctx, payload)
            if isinstance(data, dict) and set(data.keys()) == {"ok", "data", "error"}:
                return data
            return ok(data)
        except Exception as exc:
            return fail_error(ERROR_TOOL_EXECUTION, str(exc))
