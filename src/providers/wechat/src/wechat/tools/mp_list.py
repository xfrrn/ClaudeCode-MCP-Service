# wechat_mcp/providers/wechat/tools/mp_list.py
from typing import Dict, Any

from mcp_server.core.errors import ERROR_NOT_IMPLEMENTED
from mcp_server.core.response import fail_error


def mp_list(ctx, payload: Dict[str, Any]):
    return fail_error(ERROR_NOT_IMPLEMENTED)
