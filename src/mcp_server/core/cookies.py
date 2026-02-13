# wechat_mcp/core/cookies.py
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple

try:
    from cryptography.fernet import Fernet, InvalidToken
except ModuleNotFoundError:  # pragma: no cover
    Fernet = None  # type: ignore
    InvalidToken = Exception  # type: ignore


@dataclass(frozen=True)
class CookieRecord:
    name: str
    cookie: str
    updated_at: str
    encrypted: bool = False


class CookieManager:
    def __init__(self, config: Dict[str, Any], base_dir: str | Path = ".") -> None:
        self._config = config
        self._cookies_cfg = config.get("cookies", {})
        self._backend = self._cookies_cfg.get("backend", "files")
        if self._backend != "files":
            raise ValueError(f"Unsupported cookies backend: {self._backend}")

        base_path = self._cookies_cfg.get("base_path", "./cookies")
        self._base_path = (Path(base_dir) / base_path).resolve()

        self._encrypt = bool(self._cookies_cfg.get("encrypt", False))
        self._key = self._resolve_key(self._cookies_cfg)
        if self._encrypt and not self._key:
            raise ValueError("Cookie encryption enabled but no key provided")
        if self._encrypt and Fernet is None:
            raise ModuleNotFoundError("cryptography is required for cookie encryption")
        self._fernet = Fernet(self._key) if self._key and Fernet is not None else None

    def get_cookie(self, platform: str, account: Optional[str] = None) -> str:
        record = self.get_cookie_record(platform, account)
        return record.cookie

    def get_cookie_record(self, platform: str, account: Optional[str] = None) -> CookieRecord:
        account, path = self._resolve_account_file(platform, account)
        data = self._read_json(path)
        cookie_value = data.get("cookie", "")
        encrypted = bool(data.get("encrypted", False))
        if encrypted:
            cookie_value = self._decrypt(cookie_value)
        updated_at = data.get("updated_at", "")
        return CookieRecord(name=account, cookie=cookie_value, updated_at=updated_at, encrypted=encrypted)

    def set_cookie(self, platform: str, account: str, cookie: str) -> CookieRecord:
        _, path = self._resolve_account_file(platform, account)
        updated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        encrypted = False
        cookie_value = cookie
        if self._encrypt:
            cookie_value = self._encrypt_value(cookie)
            encrypted = True
        data = {
            "name": account,
            "cookie": cookie_value,
            "updated_at": updated_at,
            "encrypted": encrypted,
        }
        self._write_json(path, data)
        return CookieRecord(name=account, cookie=cookie, updated_at=updated_at, encrypted=encrypted)

    def list_accounts(self, platform: str) -> Iterable[str]:
        platform_cfg = self._platform_cfg(platform)
        accounts_cfg = platform_cfg.get("accounts", {}) if platform_cfg else {}
        if accounts_cfg:
            return list(accounts_cfg.keys())
        platform_dir = self._base_path / platform
        if not platform_dir.exists():
            return []
        return sorted(p.stem for p in platform_dir.glob("*.json"))

    def _resolve_account_file(self, platform: str, account: Optional[str]) -> Tuple[str, Path]:
        platform_cfg = self._platform_cfg(platform)
        if account is None:
            account = platform_cfg.get("default_account", "default") if platform_cfg else "default"
        account_cfg = platform_cfg.get("accounts", {}).get(account, {}) if platform_cfg else {}
        relative = account_cfg.get("file", f"{platform}/{account}.json")
        return account, (self._base_path / relative).resolve()

    def _platform_cfg(self, platform: str) -> Dict[str, Any]:
        return self._cookies_cfg.get("platforms", {}).get(platform, {})

    @staticmethod
    def _resolve_key(cookies_cfg: Dict[str, Any]) -> Optional[bytes]:
        key_env = cookies_cfg.get("key_env", "")
        if key_env:
            env_value = os.getenv(key_env, "").strip()
            if env_value:
                return env_value.encode("utf-8")
        key_value = str(cookies_cfg.get("key", "")).strip()
        return key_value.encode("utf-8") if key_value else None

    def _encrypt_value(self, value: str) -> str:
        if not self._fernet:
            raise ValueError("Cookie encryption is not configured")
        token = self._fernet.encrypt(value.encode("utf-8"))
        return token.decode("ascii")

    def _decrypt(self, value: str) -> str:
        if not self._fernet:
            raise ValueError("Cookie encryption is not configured")
        try:
            token = value.encode("ascii")
        except UnicodeEncodeError as exc:
            raise ValueError("Invalid encrypted cookie payload") from exc
        try:
            decrypted = self._fernet.decrypt(token)
        except InvalidToken as exc:  # pragma: no cover - depends on runtime key
            raise ValueError("Failed to decrypt cookie payload") from exc
        return decrypted.decode("utf-8")

    @staticmethod
    def _read_json(path: Path) -> Dict[str, Any]:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    @staticmethod
    def _write_json(path: Path, data: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
