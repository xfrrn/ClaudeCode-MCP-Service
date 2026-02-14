# wechat_mcp/core/response.py
from typing import Any, Dict

from mcp_server.core.errors import ERROR_TOOL_EXECUTION


def ok(data: Any = None) -> Dict[str, Any]:
    return {
        "ok": True,
        "data": data,
        "error": None,
    }


def fail(code: str, message: str, hint: str = "") -> Dict[str, Any]:
    return {
        "ok": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "hint": hint,
        },
    }


def fail_error(error: Dict[str, Any], hint: str = "") -> Dict[str, Any]:
    merged_hint = hint or error.get("hint", "")
    return fail(
        error.get("code", ERROR_TOOL_EXECUTION["code"]),
        error.get("message", ERROR_TOOL_EXECUTION["message"]),
        merged_hint,
    )
