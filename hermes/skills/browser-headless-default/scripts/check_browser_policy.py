#!/usr/bin/env python3
"""Detect forbidden headed-browser actions in tool plans or logs."""
from __future__ import annotations

import re
import sys

# Case-insensitive forbidden patterns (headed / visible browser)
FORBIDDEN_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("show_browser", re.compile(r"\bshow_browser\b", re.I)),
    ("hide_browser_false", re.compile(r"headless\s*:\s*false", re.I)),
    ("headed_flag", re.compile(r"--headed\b", re.I)),
    ("headed_mode", re.compile(r"\bheaded\s+mode\b", re.I)),
    ("visible_browser", re.compile(r"\bvisible\s+browser\b", re.I)),
    ("claude_in_chrome_localhost", re.compile(
        r"claude-in-chrome.*(?:localhost|127\.0\.0\.1)", re.I | re.S
    )),
]

# Explicit user opt-in — if present, headed may be allowed (caller decides)
OPT_IN_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bshow\s+browser\b", re.I),
    re.compile(r"\bheaded\s+mode\b", re.I),
    re.compile(r"\bvisible\s+browser\b", re.I),
    re.compile(r"\bi want to see the window\b", re.I),
]


def find_forbidden(text: str) -> list[str]:
    hits: list[str] = []
    for name, pat in FORBIDDEN_PATTERNS:
        if pat.search(text or ""):
            hits.append(name)
    return hits


def user_opted_into_headed(user_text: str) -> bool:
    return any(p.search(user_text or "") for p in OPT_IN_PATTERNS)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: check_browser_policy.py <text-or-file-path|-", file=sys.stderr)
        return 2
    arg = sys.argv[1]
    if arg == "-":
        body = sys.stdin.read()
    else:
        try:
            with open(arg, encoding="utf-8") as f:
                body = f.read()
        except OSError:
            body = arg
    hits = find_forbidden(body)
    if hits:
        print("FORBIDDEN:", ", ".join(hits))
        return 1
    print("OK: no headed-browser violations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
