"""Minimal MCP (HTTP JSON-RPC) client for local/preview server testing.

These helpers intentionally do NOT talk to any LLM provider APIs directly.
They exercise WorldArchitect via its MCP surface area (`/mcp`).
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MCPResponse:
    raw: dict[str, Any]

    @property
    def result(self) -> Any:
        return self.raw.get("result")

    @property
    def error(self) -> Any:
        return self.raw.get("error")


class MCPClient:
    def __init__(self, base_url: str, *, timeout_s: float = 60.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_s = timeout_s

    @property
    def mcp_url(self) -> str:
        if self._base_url.endswith("/mcp"):
            return self._base_url
        return f"{self._base_url}/mcp"

    @property
    def health_url(self) -> str:
        if self._base_url.endswith("/health"):
            return self._base_url
        if self._base_url.endswith("/mcp"):
            return f"{self._base_url[:-4]}/health"
        return f"{self._base_url}/health"

    def wait_healthy(self, *, timeout_s: float = 30.0, interval_s: float = 0.25) -> None:
        deadline = time.time() + timeout_s
        last_error: str | None = None

        while time.time() < deadline:
            try:
                data = self._http_json(self.health_url, method="GET", body=None)
                if isinstance(data, dict) and data.get("status") == "healthy":
                    return
                last_error = f"unhealthy payload: {data}"
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)
            time.sleep(interval_s)

        raise RuntimeError(f"MCP server not healthy after {timeout_s}s: {last_error}")

    def rpc(self, method: str, params: dict[str, Any] | None = None, *, rpc_id: int = 1) -> MCPResponse:
        payload = {"jsonrpc": "2.0", "id": rpc_id, "method": method, "params": params or {}}
        raw = self._http_json(
            self.mcp_url,
            method="POST",
            body=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        if not isinstance(raw, dict):
            raise RuntimeError(f"Unexpected MCP response type: {type(raw)}")
        return MCPResponse(raw=raw)

    def tools_list(self) -> list[dict[str, Any]]:
        resp = self.rpc("tools/list", rpc_id=int(time.time() * 1000))
        if resp.error:
            raise RuntimeError(f"tools/list error: {resp.error}")
        tools = (resp.result or {}).get("tools")
        if not isinstance(tools, list):
            raise RuntimeError(f"tools/list returned unexpected payload: {resp.raw}")
        return tools

    def tools_call(self, name: str, arguments: dict[str, Any]) -> Any:
        resp = self.rpc(
            "tools/call",
            params={"name": name, "arguments": arguments},
            rpc_id=int(time.time() * 1000),
        )
        if resp.error:
            raise RuntimeError(f"tools/call error: {resp.error}")
        result = resp.result
        if not isinstance(result, dict):
            raise RuntimeError(f"tools/call returned unexpected payload: {resp.raw}")
        return result

    @staticmethod
    def parse_text_content(content: Any) -> str:
        if isinstance(content, list) and content:
            first = content[0]
            if isinstance(first, dict) and isinstance(first.get("text"), str):
                return first["text"]
        return ""

    @staticmethod
    def parse_json_text_content(content: Any) -> dict[str, Any]:
        text = MCPClient.parse_text_content(content)
        if not text:
            return {}
        return json.loads(text)

    def _http_json(
        self,
        url: str,
        *,
        method: str,
        body: bytes | None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        req = urllib.request.Request(url, data=body, method=method)
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)

        try:
            with urllib.request.urlopen(req, timeout=self._timeout_s) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8") if exc.fp else ""
            raise RuntimeError(f"HTTP {exc.code} {exc.reason}: {raw}") from exc
