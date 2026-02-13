# wechat_mcp/core/context.py
from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore
    try:  # Python <3.11
        import tomli as tomllib  # type: ignore
    except ModuleNotFoundError:  # pragma: no cover
        tomllib = None  # type: ignore

from core.http_client import HttpClient


@dataclass
class AppContext:
    config: Dict[str, Any]
    http: HttpClient
    logger: logging.Logger
    db: sqlite3.Connection

    @staticmethod
    def from_config(config_path: Path) -> "AppContext":
        config: Dict[str, Any] = {}
        if config_path.exists() and tomllib is not None:
            config = tomllib.loads(config_path.read_text(encoding="utf-8"))

        logger = logging.getLogger("wechat_mcp")
        if not logger.handlers:
            logging.basicConfig(level=logging.INFO)

        db_path = AppContext._resolve_db_path(config, config_path)
        db = sqlite3.connect(db_path)
        http = HttpClient()

        return AppContext(config=config, http=http, logger=logger, db=db)

    @staticmethod
    def _resolve_db_path(config: Dict[str, Any], config_path: Path) -> str:
        db_config = config.get("database", {})
        path = db_config.get("sqlite_path", "./mcp_service.sqlite3")
        base = config_path.parent if config_path.is_file() else Path(".")
        return str((base / path).resolve())
