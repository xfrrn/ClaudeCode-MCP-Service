# wechat_mcp/providers/wechat/plugin.py
from src.mcp_server.core.registry import MCPTool
from wechat.tools.article_fetch import article_fetch
from wechat.tools.mp_search import mp_search
from wechat.tools.mp_list import mp_list


def register(registry, ctx):
    registry.register(
        MCPTool(
            name="wechat.article.fetch",
            description="Fetch a wechat article (not implemented)",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "timeout": {"type": "integer", "minimum": 1, "maximum": 120},
                    "out_dir": {"type": "string"},
                    "save_files": {"type": "boolean"},
                },
                "required": ["url"],
            },
            handler=article_fetch,
        )
    )
    registry.register(
        MCPTool(
            name="wechat.mp.search_author",
            description="Search a wechat mp author",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "token": {"type": "string"},
                    "account": {"type": "string"},
                    "cookie": {"type": "string"},
                    "user_agent": {"type": "string"},
                    "timeout": {"type": "integer", "minimum": 1, "maximum": 120},
                },
                "required": ["query"],
            },
            handler=mp_search,
        )
    )
    registry.register(
        MCPTool(
            name="wechat.mp.list_author_articles",
            description="List wechat mp author articles",
            input_schema={
                "type": "object",
                "properties": {
                    "fakeid": {"type": "string"},
                    "token": {"type": "string"},
                    "begin": {"type": "integer", "minimum": 0},
                    "count": {"type": "integer", "minimum": 1, "maximum": 20},
                    "account": {"type": "string"},
                    "cookie": {"type": "string"},
                    "user_agent": {"type": "string"},
                    "timeout": {"type": "integer", "minimum": 1, "maximum": 120},
                },
                "required": ["fakeid"],
            },
            handler=mp_list,
        )
    )
