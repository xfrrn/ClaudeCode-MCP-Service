# wechat_mcp/providers/hello/tools/say.py
from typing import Dict, Any


def say(ctx, payload: Dict[str, Any]):
    return "hello world"
