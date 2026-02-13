# wechat_mcp/providers/hello/plugin.py
from core.registry import MCPTool
from providers.hello.tools.say import say


def register(registry, ctx):
    registry.register(
        MCPTool(
            name="hello.say",
            description="Return hello world",
            input_schema={"type": "object", "properties": {}, "additionalProperties": True},
            handler=say,
        )
    )
