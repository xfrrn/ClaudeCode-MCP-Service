# wechat_mcp/providers/wechat/tools/mp_search.py
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from pydantic import BaseModel, Field, ValidationError

from mcp_server.core.cookies import CookieManager
from mcp_server.core.errors import (
    ERROR_COOKIE_NOT_FOUND,
    ERROR_INVALID_INPUT,
    ERROR_TOOL_EXECUTION,
)
from mcp_server.core.response import fail_error
from wechat.tools.wechat_auth import fetch_token


HOME_REFERER = (
    "https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN&token={token}"
)
DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/119.0.0.0 Safari/537.36"
)


class MpSearchIn(BaseModel):
    query: str = Field(min_length=1)
    token: Optional[str] = None
    account: Optional[str] = None
    cookie: Optional[str] = None
    user_agent: str = Field(default=DEFAULT_UA)
    timeout: int = Field(default=30, ge=1, le=120)


def _resolve_cookie(
    ctx, account: Optional[str], cookie: Optional[str]
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    if cookie:
        return cookie, None
    try:
        manager = CookieManager(ctx.config)
        record = manager.get_cookie_record("wechat", account)
        return (
            record.cookie,
            {
                "account": record.name,
                "updated_at": record.updated_at,
                "encrypted": record.encrypted,
            },
        )
    except Exception as exc:
        ctx.logger.warning(f"cookie load failed: {exc}")
        return None, None


def mp_search(ctx, payload: Dict[str, Any]):
    try:
        data = MpSearchIn.model_validate(payload)
    except ValidationError as e:
        return fail_error(ERROR_INVALID_INPUT, str(e))

    cookie, cookie_meta = _resolve_cookie(ctx, data.account, data.cookie)
    if not cookie:
        return fail_error(ERROR_COOKIE_NOT_FOUND, "wechat cookie missing")

    token = data.token
    token_source = "input"
    if not token:
        token = fetch_token(ctx, cookie, data.user_agent, data.timeout)
        token_source = "auto" if token else "missing"

    if not token:
        return fail_error(ERROR_TOOL_EXECUTION, "token missing or invalid; check cookie")

    params = {
        "action": "search_biz",
        "begin": 0,
        "count": 5,
        "query": data.query,
        "token": token,
        "lang": "zh_CN",
        "f": "json",
        "ajax": "1",
    }
    headers = {
        "Cookie": cookie,
        "User-Agent": data.user_agent,
        "Referer": HOME_REFERER.format(token=token),
        "Accept": "application/json, text/plain, */*",
    }

    try:
        resp = ctx.http.get(
            "https://mp.weixin.qq.com/cgi-bin/searchbiz",
            params=params,
            headers=headers,
            timeout=data.timeout,
        )
    except Exception as exc:
        return fail_error(ERROR_TOOL_EXECUTION, str(exc))

    if resp.status_code != 200:
        return fail_error(ERROR_TOOL_EXECUTION, f"status {resp.status_code}")

    try:
        payload_json = resp.json()
    except Exception:
        payload_json = {"raw": resp.text}

    fakeid = None
    try:
        fakeid = payload_json.get("list", [{}])[0].get("fakeid")
    except Exception:
        fakeid = None

    output: Dict[str, Any] = {
        "ok": True,
        "data": {
            "query": data.query,
            "fakeid": fakeid,
            "raw": payload_json,
        },
        "meta": {
            "crawl_time": datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "source": "wechat",
            "tool": "wechat.mp.search_author",
            "version": "1.0",
            "token_source": token_source,
        },
    }

    if cookie_meta:
        output["meta"]["cookie"] = cookie_meta

    return output
