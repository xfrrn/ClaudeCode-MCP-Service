# wechat_mcp/providers/wechat/tools/mp_list.py
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

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


class MpListIn(BaseModel):
    fakeid: str = Field(min_length=1)
    token: Optional[str] = None
    begin: int = Field(default=0, ge=0)
    count: int = Field(default=5, ge=1, le=20)
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


def _extract_items(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    publish_page = raw.get("publish_page")
    if not publish_page:
        return items
    try:
        page_obj = json.loads(publish_page)
    except Exception:
        return items

    for pub in page_obj.get("publish_list", []):
        try:
            info_obj = json.loads(pub.get("publish_info", "{}"))
        except Exception:
            continue
        for appmsg in info_obj.get("appmsgex", []):
            title = appmsg.get("title")
            link = appmsg.get("link")
            if title and link:
                link = str(link).replace("\\/", "/").replace("\\\\/", "/")
            items.append(
                {
                    "title": title or "",
                    "url": link or "",
                    "digest": appmsg.get("digest", ""),
                    "cover": appmsg.get("cover", ""),
                    "update_time": appmsg.get("update_time", ""),
                }
            )
    return items


def mp_list(ctx, payload: Dict[str, Any]):
    try:
        data = MpListIn.model_validate(payload)
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
        "sub": "list",
        "sub_action": "list_ex",
        "begin": data.begin,
        "count": data.count,
        "fakeid": data.fakeid,
        "token": token,
        "lang": "zh_CN",
        "f": "json",
        "ajax": 1,
    }
    headers = {
        "Cookie": cookie,
        "User-Agent": data.user_agent,
        "Referer": HOME_REFERER.format(token=token),
        "Accept": "application/json, text/plain, */*",
    }

    try:
        resp = ctx.http.get(
            "https://mp.weixin.qq.com/cgi-bin/appmsgpublish",
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

    items = _extract_items(payload_json) if isinstance(payload_json, dict) else []

    output: Dict[str, Any] = {
        "ok": True,
        "data": {
            "fakeid": data.fakeid,
            "begin": data.begin,
            "count": data.count,
            "items": items,
            "raw": payload_json,
        },
        "meta": {
            "crawl_time": datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "source": "wechat",
            "tool": "wechat.mp.list_author_articles",
            "version": "1.0",
            "token_source": token_source,
        },
    }

    if cookie_meta:
        output["meta"]["cookie"] = cookie_meta

    return output
