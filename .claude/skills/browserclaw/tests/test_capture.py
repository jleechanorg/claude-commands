from __future__ import annotations

import time
from unittest.mock import patch

from browserclaw.capture import _WsCaptureSession
from browserclaw.models import WebSocketConnection


def test_ws_created_at_uses_wall_clock_not_cdp_timestamp() -> None:
    session = _WsCaptureSession(cdp=None)
    cdp_monotonic_ts = 1234567890.123
    wall_clock_ts = 1700000000.5

    with patch("browserclaw.capture.time") as mock_time:
        mock_time.time.return_value = wall_clock_ts
        session._on_created({
            "requestId": "ws-1",
            "url": "wss://example.com/socket",
            "timestamp": cdp_monotonic_ts,
            "initiator": {},
        })

    conn = session.connections["ws-1"]
    assert conn.created_at == wall_clock_ts
    assert conn.created_at != cdp_monotonic_ts


def test_ws_destroyed_at_uses_wall_clock_not_cdp_timestamp() -> None:
    conn = WebSocketConnection(
        connection_id="ws-2",
        url="wss://example.com/socket",
        created_at=1700000000.0,
    )
    session = _WsCaptureSession(cdp=None)
    session.connections["ws-2"] = conn

    cdp_monotonic_ts = 1234567895.0
    wall_clock_ts = 1700000005.0

    with patch("browserclaw.capture.time") as mock_time:
        mock_time.time.return_value = wall_clock_ts
        session._on_destroyed({
            "requestId": "ws-2",
            "timestamp": cdp_monotonic_ts,
        })

    assert conn.closed_at == wall_clock_ts
    assert conn.closed_at != cdp_monotonic_ts


def test_ws_frame_timestamps_use_wall_clock() -> None:
    conn = WebSocketConnection(
        connection_id="ws-3",
        url="wss://example.com/socket",
        created_at=1700000000.0,
    )
    session = _WsCaptureSession(cdp=None)
    session.connections["ws-3"] = conn

    wall_clock_ts = 1700000002.0
    cdp_monotonic_ts = 1234567892.0

    with patch("browserclaw.capture.time") as mock_time:
        mock_time.time.return_value = wall_clock_ts
        session._on_frame_sent({
            "requestId": "ws-3",
            "timestamp": cdp_monotonic_ts,
            "response": {
                "opcode": 1,
                "payloadData": "hello",
                "payloadLength": 5,
            },
        })

    assert len(conn.frames) == 1
    assert conn.frames[0].timestamp == wall_clock_ts
    assert conn.frames[0].timestamp != cdp_monotonic_ts
