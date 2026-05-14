#!/usr/bin/env python3
"""UserPromptSubmit hook: inject relevant mem0 memories before Claude sees the prompt.

Searches openclaw_mem0 qdrant store and returns top matches as additionalContext.
Silently exits 0 on any error — never blocks the prompt.
"""
from __future__ import annotations

import json
import os
import sys

# Config — mirrors openclaw-mem0 plugin settings
MEM0_CONFIG = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "host": "127.0.0.1",
            "port": 6333,
            "collection_name": "openclaw_mem0",
            "embedding_model_dims": 1536,
        },
    },
    "embedder": {
        "provider": "openai",
        "config": {
            "model": "text-embedding-3-small",
            "api_key": os.environ.get("OPENAI_API_KEY", ""),
        },
    },
    "llm": {
        "provider": "openai",
        "config": {
            "model": "gpt-4o-mini",
            "api_key": os.environ.get("OPENAI_API_KEY", ""),
        },
    },
    "version": "v1.1",
}

TOP_K = 6
SCORE_THRESHOLD = 0.35
USER_ID = "$USER"


def main() -> None:
    # Read hook input
    try:
        data = json.loads(sys.stdin.read())
    except Exception:
        sys.exit(0)

    prompt = data.get("prompt", "").strip()
    if not prompt or len(prompt) < 10:
        sys.exit(0)

    # Skip if OPENAI_API_KEY not set
    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit(0)

    try:
        from mem0 import Memory  # type: ignore

        m = Memory.from_config(MEM0_CONFIG)
        raw = m.search(prompt, user_id=USER_ID, limit=TOP_K)
        results = raw.get("results", raw) if isinstance(raw, dict) else raw

        # Filter by score threshold
        hits = [
            r for r in results
            if isinstance(r.get("score"), (int, float)) and r["score"] >= SCORE_THRESHOLD
        ]

        if not hits:
            sys.exit(0)

        lines = ["## Relevant memories (from past sessions)"]
        for r in hits:
            mem = r.get("memory", r.get("data", "")).strip()
            score = r.get("score", 0)
            if mem:
                lines.append(f"- [{score:.2f}] {mem}")

        context = "\n".join(lines)

        # Return as additionalContext (quiet injection, not shown as hook output)
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": context,
            }
        }))

    except Exception:
        pass  # Never block the prompt

    sys.exit(0)


if __name__ == "__main__":
    main()
