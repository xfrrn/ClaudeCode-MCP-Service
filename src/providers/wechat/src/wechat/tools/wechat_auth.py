# wechat_mcp/providers/wechat/tools/wechat_auth.py
import re
from typing import Optional


WX_HOME = "https://mp.weixin.qq.com/cgi-bin/home"


def extract_token_from_html(html: str) -> Optional[str]:
    if not html:
        return None
    match = re.search(r"[?&]token=(\d+)", html)
    if match:
        return match.group(1)
    match = re.search(r"\btoken\b\s*[:=]\s*['\"](\d+)['\"]", html)
    if match:
        return match.group(1)
    return None


def fetch_token(ctx, cookie: str, user_agent: str, timeout: int) -> Optional[str]:
    headers = {
        "Cookie": cookie,
        "User-Agent": user_agent,
        "Referer": "https://mp.weixin.qq.com/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    try:
        resp = ctx.http.get(WX_HOME, headers=headers, timeout=timeout, allow_redirects=True)
    except Exception as exc:
        ctx.logger.warning(f"token fetch failed: {exc}")
        return None

    if resp.status_code != 200:
        ctx.logger.warning(f"token fetch status={resp.status_code}")
        return None

    token = extract_token_from_html(resp.url or "")
    if token:
        return token
    return extract_token_from_html(resp.text)
