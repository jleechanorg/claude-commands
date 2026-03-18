#!/usr/bin/env python3
"""Codex SessionStart hook: inject relevant mem0 memories before the session starts.

Reads the session's initial prompt/task from stdin, searches openclaw_mem0 qdrant,
and returns a context string to be prepended to the user prompt.

Codex Stop hook output format (v0.114.0):
  {"context": "..."} — appended to user prompt (ephemeral, not persisted)
  {"continue": true} — no context, proceed normally

Silently falls back to {"continue": true} on any error.
"""
from __future__ import annotations

import json
import os
import sys

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
USER_ID = "jleechan"

FALLBACK = json.dumps({"continue": True})


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        print(FALLBACK)
        sys.exit(0)

    try:
        data = json.loads(sys.stdin.read())
    except Exception:
        print(FALLBACK)
        sys.exit(0)

    # Extract query from session start payload — try common fields
    query = (
        data.get("task")
        or data.get("prompt")
        or data.get("message")
        or data.get("userMessage")
        or ""
    ).strip()

    if not query or len(query) < 10:
        print(FALLBACK)
        sys.exit(0)

    try:
        from mem0 import Memory  # type: ignore

        m = Memory.from_config(MEM0_CONFIG)
        raw = m.search(query, user_id=USER_ID, limit=TOP_K)
        results = raw.get("results", raw) if isinstance(raw, dict) else raw

        hits = [
            r for r in results
            if isinstance(r.get("score"), (int, float)) and r["score"] >= SCORE_THRESHOLD
        ]

        if not hits:
            print(FALLBACK)
            sys.exit(0)

        lines = ["## Relevant memories (from past sessions)"]
        for r in hits:
            mem = r.get("memory", r.get("data", "")).strip()
            score = r.get("score", 0)
            if mem:
                lines.append(f"- [{score:.2f}] {mem}")

        context = "\n".join(lines)
        print(json.dumps({"context": context}))

    except Exception:
        print(FALLBACK)

    sys.exit(0)


if __name__ == "__main__":
    main()
