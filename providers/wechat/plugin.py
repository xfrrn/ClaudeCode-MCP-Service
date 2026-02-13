# wechat_mcp/providers/wechat/plugin.py
from core.registry import MCPTool
from providers.wechat.tools.article_fetch import article_fetch
from providers.wechat.tools.mp_search import mp_search
from providers.wechat.tools.mp_list import mp_list


def register(registry, ctx):
    registry.register(
        MCPTool(
            name="wechat.article.fetch",
            description="Fetch a wechat article (not implemented)",
            input_schema={"type": "object", "properties": {}, "additionalProperties": True},
            handler=article_fetch,
        )
    )
    registry.register(
        MCPTool(
            name="wechat.mp.search_author",
            description="Search a wechat mp author (not implemented)",
            input_schema={"type": "object", "properties": {}, "additionalProperties": True},
            handler=mp_search,
        )
    )
    registry.register(
        MCPTool(
            name="wechat.mp.list_author_articles",
            description="List wechat mp author articles (not implemented)",
            input_schema={"type": "object", "properties": {}, "additionalProperties": True},
            handler=mp_list,
        )
    )
