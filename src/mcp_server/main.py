# wechat_mcp/mcp_server.py
import importlib
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from mcp_server.core.context import AppContext
from mcp_server.core.registry import ToolRegistry


def load_plugins(registry: ToolRegistry, ctx: AppContext, providers_dir: Path) -> None:
    if not providers_dir.exists():
        return

    for entry in providers_dir.iterdir():
        if not entry.is_dir():
            continue
        plugin_path = entry / "plugin.py"
        if not plugin_path.exists():
            continue

        module_name = f"{entry.name}.plugin"
        module = importlib.import_module(module_name)
        if hasattr(module, "register"):
            module.register(registry, ctx)


def build_context(config_path: Path) -> AppContext:
    return AppContext.from_config(config_path)


class ToolCall(BaseModel):
    tool: str
    input: Dict[str, Any] = {}


def create_app(config_path: Path | None = None) -> FastAPI:
    cfg = Path("config.example.toml") if config_path is None else config_path
    ctx = build_context(cfg)
    registry = ToolRegistry()
    repo_root = Path(__file__).resolve().parents[2]
    load_plugins(registry, ctx, repo_root / "providers")

    app = FastAPI(title="MCP Server", version="0.1.0")

    @app.get("/tools")
    def list_tools() -> Dict[str, Any]:
        return {"tools": sorted(registry.tools.keys())}

    @app.post("/call")
    def call_tool(req: ToolCall) -> Dict[str, Any]:
        resp = registry.invoke(req.tool, req.input, ctx)
        if not resp.get("ok"):
            raise HTTPException(status_code=400, detail=resp)
        return resp

    return app


app = create_app()
