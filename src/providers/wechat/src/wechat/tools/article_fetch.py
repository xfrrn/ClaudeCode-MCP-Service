import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag
from pydantic import BaseModel, Field, HttpUrl, ValidationError

from mcp_server.core.errors import ERROR_INVALID_INPUT, ERROR_TOOL_EXECUTION
from mcp_server.core.response import fail_error


def _safe_filename(value: str, max_length: int = 120) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|]", "_", value or "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ._")
    return cleaned[:max_length] or "untitled"


def _normalize_image_url(url: str) -> str:
    if url.startswith("//"):
        return f"https:{url}"
    return url


def _convert_tag_to_markdown(tag: Tag, img_counter: Dict[str, int]) -> str:
    markdown_str = ""

    if tag.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
        level = int(tag.name[1])
        markdown_str = f"{'#' * level} {tag.get_text(strip=True)}\n\n"

    elif tag.name in ["p", "section", "div"]:
        for child in tag.children:
            if isinstance(child, NavigableString):
                markdown_str += str(child)
            elif isinstance(child, Tag) and child.name == "img":
                img_src = child.get("data-src") or child.get("src") or ""
                img_src = _normalize_image_url(str(img_src))
                alt_text = str(child.get("alt") or "image")
                img_counter["value"] += 1
                markdown_str += f"![{alt_text}]({img_src})\n"
            elif isinstance(child, Tag) and child.name == "br":
                markdown_str += "\n"
            elif isinstance(child, Tag):
                markdown_str += _convert_tag_to_markdown(child, img_counter)
        markdown_str += "\n\n"

    elif tag.name == "blockquote":
        content = tag.get_text(separator="\n", strip=True)
        markdown_str = "".join([f"> {line}\n" for line in content.split("\n")]) + "\n"

    elif tag.name == "pre":
        code_content = tag.get_text()
        markdown_str = f"```\n{code_content.strip()}\n```\n\n"

    elif tag.name == "a":
        link_text = tag.get_text(strip=True)
        href = tag.get("href", "")
        markdown_str = f"[{link_text}]({href})"

    elif tag.name == "strong":
        markdown_str = f"**{tag.get_text(strip=True)}**"

    else:
        markdown_str = tag.get_text()

    return markdown_str


def _normalize_publish_time(raw_value: str) -> str:
    if not raw_value:
        return ""
    value = raw_value.strip()
    if value.isdigit():
        try:
            timestamp = int(value)
        except ValueError:
            return ""
        if timestamp > 10_000_000_000:
            timestamp = int(timestamp / 1000)
        return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    return value


class ArticleFetchIn(BaseModel):
    url: HttpUrl
    timeout: int = Field(default=30, ge=1, le=120)
    out_dir: str = Field(default="./wechat_articles")
    save_files: bool = Field(default=True)


def article_fetch(ctx, payload: Dict[str, Any]):
    try:
        data = ArticleFetchIn.model_validate(payload)
    except ValidationError as e:
        return fail_error(ERROR_INVALID_INPUT, str(e))

    headers = {
        "Referer": "https://mp.weixin.qq.com/",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0.0.0 Safari/537.36"
        ),
    }

    try:
        resp = ctx.http.get(str(data.url), headers=headers, timeout=data.timeout)
    except Exception as exc:
        return fail_error(ERROR_TOOL_EXECUTION, str(exc))

    if resp.status_code != 200:
        return fail_error(ERROR_TOOL_EXECUTION, f"status {resp.status_code}")

    resp.encoding = resp.apparent_encoding
    if re.search("当前环境异常，完成验证后即可继续访问", resp.text):
        return fail_error(ERROR_TOOL_EXECUTION, "verification required")

    html = resp.text
    soup = BeautifulSoup(html, "html.parser")

    content_node = soup.find("div", class_="rich_media_content") or soup.find(
        "div", id="js_content"
    )
    content = content_node.get_text("\n", strip=True) if content_node else ""

    title_node = soup.find("h1", {"class": "rich_media_title", "id": "activity-name"})
    title = title_node.get_text(strip=True) if title_node else ""

    author_node = soup.find("a", {"id": "js_name"})
    author = author_node.get_text(strip=True) if author_node else ""

    biz_match = re.search(r"var biz\\s*=\\s*\"(.*?)\";", html)
    biz = ""
    if biz_match:
        biz = biz_match.group(1).replace('" || "', "").replace('"', "")

    time_match = re.search(r"var createTime = '(.*?)';", html)
    create_time = time_match.group(1) if time_match else ""
    publish_time_iso = _normalize_publish_time(create_time)

    markdown_content = ""
    img_counter = {"value": 0}
    if isinstance(content_node, Tag):
        markdown_parts = []
        for tag in content_node.find_all(recursive=False):
            if isinstance(tag, Tag):
                markdown_parts.append(_convert_tag_to_markdown(tag, img_counter))
        markdown_content = "".join(markdown_parts).strip()

    output: Dict[str, Any] = {
        "ok": True,
        "data": {
            "title": title,
            "author": author,
            "publish_time": publish_time_iso,
            "biz": biz,
            "url": str(data.url),
            "content_html": content,
            "content_markdown": markdown_content,
            "images_count": img_counter["value"],
            "word_count": len(markdown_content),
            "summary": None,
        },
        "meta": {
            "crawl_time": datetime.utcnow().isoformat() + "Z",
            "source": "wechat",
            "tool": "wechat.article.fetch",
            "version": "1.0",
        },
    }

    if data.save_files:
        out_dir = Path(data.out_dir).resolve()
        json_dir = out_dir / "json"
        md_dir = out_dir / "md"
        json_dir.mkdir(parents=True, exist_ok=True)
        md_dir.mkdir(parents=True, exist_ok=True)

        base_name = _safe_filename(f"{author}-{title}-{create_time}")
        markdown_path = md_dir / f"{base_name}.md"
        with markdown_path.open("w", encoding="utf-8") as f:
            if title:
                f.write(f"# {title}\n\n")
            if author:
                f.write(f"**Author:** {author}\n\n")
            if publish_time_iso:
                f.write(f"**Published:** {publish_time_iso}\n\n")
            f.write(markdown_content)

        output["meta"]["markdown_file"] = str(markdown_path)

        json_path = json_dir / f"{base_name}.json"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

    return output
