#!/usr/bin/env python3
"""
autoapprove.py — Claude Code PreToolUse hook

Auto-approves tool calls only when CLAUDE_AUTOAPPROVE=1 is set.
Without the flag, always deny to preserve the permission boundary.
"""
from __future__ import annotations

import json
import os
import sys


def main() -> int:
    try:
        raw = sys.stdin.read()
        request = json.loads(raw)
    except Exception:
        return 0

    if os.getenv("CLAUDE_AUTOAPPROVE") != "1":
        tool_name = request.get("name", "")
        print(json.dumps({"decision": "block", "reason": f"manual approval required: {tool_name}"}))
        return 0

    tool_name = request.get("name", "")
    print(json.dumps({"decision": "approve", "reason": f"autoapprove (env-gated): {tool_name}"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
