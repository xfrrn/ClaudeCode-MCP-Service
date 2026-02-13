# wechat_mcp/providers/wechat/tools/mp_list.py
from typing import Dict, Any

from core.response import fail


def mp_list(ctx, payload: Dict[str, Any]):
    return fail("not_implemented", "Not implemented", "Provide a real implementation in this tool")
