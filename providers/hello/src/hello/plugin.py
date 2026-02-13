# wechat_mcp/providers/hello/plugin.py
from src.mcp_server.core.registry import MCPTool
from hello.tools.say import say


def register(registry, ctx):
    registry.register(
        MCPTool(
            name="hello.say",
            description="Return hello world",
            input_schema={"type": "object", "properties": {}, "additionalProperties": True},
            handler=say,
        )
    )
