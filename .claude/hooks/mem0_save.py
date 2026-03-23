#!/usr/bin/env python3
"""Stop hook: extract facts from the last exchange and save to mem0.

Fires when Claude finishes a response. Uses mem0's LLM extraction (infer=True)
to distill facts from the last assistant message + prompt context.

Guards:
- stop_hook_active=True → skip (prevent infinite loop)
- Short/trivial responses → skip
- Always exits 0 (never blocks)
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

USER_ID = os.environ.get("USER", "unknown")
MIN_RESPONSE_LEN = 100  # Skip trivial one-liners


def main() -> None:
    try:
        data = json.loads(sys.stdin.read())
    except Exception:
        sys.exit(0)

    # Guard: already continuing due to a stop hook — skip to avoid loop
    if data.get("stop_hook_active"):
        sys.exit(0)

    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit(0)

    last_message = data.get("last_assistant_message", "").strip()
    if len(last_message) < MIN_RESPONSE_LEN:
        sys.exit(0)

    # Skip pure code/tool-only responses (heuristic: no sentences)
    if last_message.count(". ") < 2 and last_message.count("\n") > 20:
        sys.exit(0)

    try:
        from mem0 import Memory  # type: ignore

        m = Memory.from_config(MEM0_CONFIG)
        # Use infer=True: mem0 LLM extracts facts from the message
        result = m.add(last_message, user_id=USER_ID, infer=True)
        # Normalize result — some versions return dict with "results" key
        _ = result  # fire-and-forget
    except Exception:
        pass  # Never block

    sys.exit(0)


if __name__ == "__main__":
    main()
