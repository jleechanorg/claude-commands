from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any
from urllib.parse import urlparse


@dataclass(slots=True)
class BrowserStep:
    action: str
    selector: str | None = None
    value: str | None = None
    url: str | None = None
    milliseconds: int | None = None


@dataclass(slots=True)
class EndpointSignature:
    name: str
    method: str
    url_template: str
    host: str
    query_keys: list[str] = field(default_factory=list)
    request_header_keys: list[str] = field(default_factory=list)
    request_body_keys: list[str] = field(default_factory=list)
    response_header_keys: list[str] = field(default_factory=list)
    sample_status_codes: list[int] = field(default_factory=list)
    sample_content_types: list[str] = field(default_factory=list)
    request_content_type: str = "json"  # "json" or "form" — primary encoding
    observed_request_content_types: list[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EndpointCatalog:
    site: str
    source_har: str
    notes: list[str]
    endpoints: list[EndpointSignature]
    llm_provider: str | None = None
    llm_model: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "site": self.site,
            "source_har": self.source_har,
            "notes": list(self.notes),
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "endpoints": [endpoint.to_dict() for endpoint in self.endpoints],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EndpointCatalog":
        endpoints = [EndpointSignature(**item) for item in payload.get("endpoints", [])]
        return cls(
            site=payload["site"],
            source_har=payload["source_har"],
            notes=list(payload.get("notes", [])),
            endpoints=endpoints,
            llm_provider=payload.get("llm_provider"),
            llm_model=payload.get("llm_model"),
        )


class WsOpcode(Enum):
    CONTINUATION = 0x0
    TEXT = 0x1
    BINARY = 0x2
    CLOSE = 0x8
    PING = 0x9
    PONG = 0xA


@dataclass(slots=True)
class WebSocketFrame:
    """A single WebSocket frame (sent or received)."""
    timestamp: float
    connection_id: str
    direction: str  # "sent" or "received"
    opcode: int
    payload: str  # raw bytes decoded as utf-8, empty string if binary undecoded
    size: int
    is_binary: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "connection_id": self.connection_id,
            "direction": self.direction,
            "opcode": self.opcode,
            "payload": self.payload,
            "size": self.size,
            "is_binary": self.is_binary,
        }


@dataclass(slots=True)
class WebSocketConnection:
    """A single WebSocket connection lifecycle."""
    connection_id: str
    url: str
    created_at: float
    closed_at: float | None = None
    request_headers: dict[str, str] | None = None
    response_headers: dict[str, str] | None = None
    frames: list[WebSocketFrame] = field(default_factory=list)

    @property
    def host(self) -> str:
        return urlparse(self.url).netloc

    @property
    def is_firestore(self) -> bool:
        return "firestore.googleapis.com" in self.url

    def summarize(self) -> dict[str, Any]:
        return {
            "connection_id": self.connection_id,
            "url": self.url,
            "host": self.host,
            "frame_count": len(self.frames),
            "total_bytes": sum(f.size for f in self.frames),
            "is_firestore": self.is_firestore,
            "created_at": self.created_at,
            "closed_at": self.closed_at,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "connection_id": self.connection_id,
            "url": self.url,
            "created_at": self.created_at,
            "closed_at": self.closed_at,
            "request_headers": self.request_headers,
            "response_headers": self.response_headers,
            "frame_count": len(self.frames),
            "is_firestore": self.is_firestore,
        }


@dataclass(slots=True)
class FirestoreRpcCall:
    """A parsed Firestore WebSocket RPC call."""
    call_id: int
    action: str  # "listen" | "unlisten" | "rpc" | "snapshot" | "health" | "unknown"
    target_id: int | None
    stream_token: str | None
    raw_payload: dict[str, Any] | None
    raw_text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "call_id": self.call_id,
            "action": self.action,
            "target_id": self.target_id,
            "stream_token": self.stream_token,
            "raw_payload": self.raw_payload,
            "raw_text": self.raw_text,
        }


def parse_firestore_message(text: str) -> list[FirestoreRpcCall]:
    """Parse Firebase Firestore WebSocket JSON messages.

    Firestore WebSocket messages wrap protobuf-like data in JSON with:
    - a: action type (number: 1=listen, 2=unlisten, 3=rpc, ...)
    - t: stream token (base64)
    - d: data payload
    - r: reference count?

    Returns parsed FirestoreRpcCall objects.
    """
    calls = []
    try:
        msg = json.loads(text)
    except json.JSONDecodeError:
        return calls

    # Handle array of messages (common case: many messages batched)
    messages = msg if isinstance(msg, list) else [msg]
    for idx, m in enumerate(messages):
        if not isinstance(m, dict):
            continue
        action_num = m.get("a", m.get("action"))
        if action_num is None:
            continue
        try:
            action_num = int(action_num)
        except (ValueError, TypeError):
            action_num = -1

        action_map = {
            1: "listen",
            2: "unlisten",
            3: "rpc",
            4: "snapshot",
            5: "health",
            6: "handshake",
        }
        action = action_map.get(action_num, "unknown")

        target_id = None
        if isinstance(m.get("d"), dict):
            # Firestore target
            target_id = m["d"].get("target", m["d"].get("targetId"))

        stream_token = m.get("t") or m.get("streamToken")

        calls.append(FirestoreRpcCall(
            call_id=idx,
            action=action,
            target_id=target_id,
            stream_token=stream_token,
            raw_payload=m,
            raw_text=text[:500],
        ))
    return calls

@dataclass(slots=True)
class WebSocketCaptureResult:
    """Result of a WebSocket capture session."""
    connections: list[WebSocketConnection]
    firestore_calls: list[FirestoreRpcCall]
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "connections": [c.to_dict() for c in self.connections],
            "firestore_calls": [c.to_dict() for c in self.firestore_calls],
            "notes": list(self.notes),
        }
