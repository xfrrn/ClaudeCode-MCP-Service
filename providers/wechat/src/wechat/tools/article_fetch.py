# wechat_mcp/providers/wechat/tools/article_fetch.py
from typing import Dict, Any

from mcp_server.core.response import fail


def article_fetch(ctx, payload: Dict[str, Any]):
    return fail("not_implemented", "Not implemented", "Provide a real implementation in this tool")
