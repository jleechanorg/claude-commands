#!/usr/bin/env python3
"""
always_approve.py — Claude Code PreToolUse hook
Auto-approves all tool calls silently.
"""
import json
import sys

def main() -> int:
    sys.stdin.read()
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow"
        }
    }))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
