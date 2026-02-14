# wechat_mcp/README.md

# MCP Server (Minimal Template, uv workspace)

## Architecture

- `src/mcp_server/main.py` loads configuration, builds `AppContext`, auto-discovers plugins, and routes tool calls.
- `src/mcp_server/core/` contains registry, context, response helpers, and a simple HTTP client.
- `src/providers/<name>/` are workspace packages; each provides `plugin.py` and `tools/` as a standalone package.

## Directory

```
ClaudeCode-MCP-Service/
├── pyproject.toml
├── uv.lock
├── src/
│ └── mcp_server/
│   ├── main.py
│   └── core/
│     ├── registry.py
│     ├── context.py
│     ├── errors.py
│     ├── response.py
│     └── http_client.py
├── src/providers/
│ ├── hello/
│ │ ├── pyproject.toml
│ │ └── src/hello/
│ │   ├── plugin.py
│ │   └── tools/
│ │     └── say.py
│ └── wechat/
│   ├── pyproject.toml
│   └── src/wechat/
│     ├── plugin.py
│     └── tools/
│       ├── article_fetch.py
│       ├── mp_search.py
│       └── mp_list.py
├── config.example.toml
└── README.md
```

## Run (uv)

```bash
uv sync --all-packages
uv run uvicorn mcp_server.main:app --reload --host 0.0.0.0 --port 8000
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

1. Create a new workspace package under `src/providers/<plugin>/`.
2. Put code in `src/providers/<plugin>/src/<plugin>/plugin.py` and `tools/`.
3. Add the provider path to `[tool.uv.workspace].members` in `pyproject.toml`.
4. Run `uv sync`. No core change required; the server auto-discovers plugins.

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
