#!/usr/bin/env python3
"""
autoapprove.py — Claude Code PreToolUse hook

Unconditionally approves every tool call.
"""
from __future__ import annotations

import json
import sys

def main() -> int:
    try:
        raw = sys.stdin.read()
        request = json.loads(raw)
    except Exception:
        return 0

    tool_name = request.get("name", "")
    print(json.dumps({"decision": "approve", "reason": f"autoapprove: {tool_name}"}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
