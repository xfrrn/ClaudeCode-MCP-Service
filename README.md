# wechat_mcp/README.md
# MCP Server (Minimal Template)

## Architecture
- `mcp_server.py` loads configuration, builds `AppContext`, auto-discovers plugins, and routes tool calls.
- `core/` contains registry, context, response helpers, and a simple HTTP client.
- `providers/<name>/` defines a plugin with `plugin.py` and a `tools/` package.

## Directory
```
ClaudeCode-MCP-Service/
├── mcp_server.py
├── core/
│ ├── registry.py
│ ├── context.py
│ ├── errors.py
│ ├── response.py
│ └── http_client.py
├── providers/
│ ├── hello/
│ │ ├── plugin.py
│ │ └── tools/
│ │ └── say.py
│ └── wechat/
│ ├── plugin.py
│ └── tools/
│ ├── article_fetch.py
│ ├── mp_search.py
│ └── mp_list.py
├── config.example.toml
├── requirements.txt
└── README.md
```

## Run
```bash
pip install -r requirements.txt
uvicorn mcp_server:app --reload --host 0.0.0.0 --port 8000
```

## API
- `GET /tools` list all tools.
- `POST /call` call a tool with JSON body:
```json
{
  "tool": "hello.say",
  "input": {}
}
```

## Add New Plugin
1. Create `providers/<plugin>/plugin.py` and `providers/<plugin>/tools/`.
2. Implement tools and register them in `register(registry, ctx)`.
3. No core change required; the server auto-discovers plugins.

## Add New Tool
- Define a handler: `def handler(ctx, payload): ...`.
- Build an `MCPTool` with `name`, `description`, `input_schema`, `handler`.
- Register it in the plugin's `register` function.

## AppContext
`AppContext` provides shared resources: `config`, `http`, `logger`, `db` (SQLite). You can expand it to include MySQL or other services later.

## Notes
- Tool output is normalized by the registry to:
```
{
  "ok": bool,
  "data": any,
  "error": {"code": str, "message": str, "hint": str}
}
```
- The wechat tools are stubs returning a default not-implemented response.
