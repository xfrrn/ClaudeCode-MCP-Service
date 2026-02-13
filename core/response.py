# wechat_mcp/core/response.py
from typing import Any, Dict


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
