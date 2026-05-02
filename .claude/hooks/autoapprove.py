#!/usr/bin/env python3
"""
autoapprove.py — Claude Code PreToolUse hook

Evaluates each tool call and approves if it passes the autoapprove policy.
Deny-and-exit on parse errors (fail-closed).
"""
from __future__ import annotations

import json
import sys

ALLOWED_TOOLS = frozenset({
    "Read", "Glob", "Grep", "Bash", "Edit", "Write", "TaskCreate",
    "TaskUpdate", "TaskList", "TaskGet", "Agent", "WebFetch", "WebSearch",
})

def _deny(tool_name: str, reason: str) -> None:
    print(json.dumps({"decision": "deny", "reason": f"[autoapprove] {reason}: {tool_name}"}))
    print(json.dumps({"decision": "deny", "reason": f"[autoapprove] {reason}: {tool_name}"}), file=sys.stderr)

def main() -> int:
    try:
        raw = sys.stdin.read()
        request = json.loads(raw)
    except json.JSONDecodeError as e:
        _deny("<unknown>", f"JSON parse error: {e}")
        return 1
    except Exception as e:
        _deny("<unknown>", f"stdin read error: {e}")
        return 1

    tool_name = request.get("name", "")
    if tool_name in ALLOWED_TOOLS:
        print(json.dumps({"decision": "approve", "reason": f"autoapprove: {tool_name}"}))
        return 0

    _deny(tool_name, "tool not in allowlist")
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
