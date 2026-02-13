# wechat_mcp/mcp_server.py
import contextlib
import importlib
import sys
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from mcp_server.core.context import AppContext
from mcp_server.core.registry import MCPTool, ToolRegistry


def load_plugins(registry: ToolRegistry, ctx: AppContext, providers_dir: Path) -> None:
    if not providers_dir.exists():
        return

    for entry in providers_dir.iterdir():
        if not entry.is_dir():
            continue
        module_name = f"{entry.name}.plugin"
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            # Allow local dev without installing workspace package
            src_path = entry / "src"
            if src_path.exists():
                sys.path.insert(0, str(src_path))
                module = importlib.import_module(module_name)
            else:
                continue
        if hasattr(module, "register"):
            module.register(registry, ctx)


def build_context(config_path: Path) -> AppContext:
    return AppContext.from_config(config_path)


class ToolCall(BaseModel):
    tool: str
    input: Dict[str, Any] = {}


def register_mcp_tools(mcp: FastMCP, registry: ToolRegistry, ctx: AppContext) -> None:
    def make_tool(tool: MCPTool):
        @mcp.tool(name=tool.name, description=tool.description)
        def _tool(**kwargs):
            return tool.handler(ctx, kwargs)

        return _tool

    for tool in registry.tools.values():
        make_tool(tool)


def create_app(config_path: Path | None = None) -> FastAPI:
    cfg = Path("config.example.toml") if config_path is None else config_path
    ctx = build_context(cfg)
    registry = ToolRegistry()
    repo_root = Path(__file__).resolve().parents[2]
    load_plugins(registry, ctx, repo_root / "providers")

    mcp = FastMCP("ClaudeCode-MCP", json_response=True, streamable_http_path="/")
    register_mcp_tools(mcp, registry, ctx)

    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI):
        async with mcp.session_manager.run():
            yield

    app = FastAPI(title="MCP Server", version="0.1.0", lifespan=lifespan)

    @app.get("/tools")
    def list_tools() -> Dict[str, Any]:
        return {"tools": sorted(registry.tools.keys())}

    @app.post("/call")
    def call_tool(req: ToolCall) -> Dict[str, Any]:
        resp = registry.invoke(req.tool, req.input, ctx)
        if not resp.get("ok"):
            raise HTTPException(status_code=400, detail=resp)
        return resp

    app.mount("/mcp/", mcp.streamable_http_app())

    return app


app = create_app()
