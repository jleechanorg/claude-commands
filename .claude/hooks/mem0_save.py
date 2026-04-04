#!/usr/bin/env python3
"""Stop hook: extract facts from the last exchange and save to mem0 + markdown.

Fires when Claude finishes a response. Uses mem0's LLM extraction (infer=True)
to distill facts from the last assistant message + prompt context.

Dual-writes to:
  1. Qdrant (openclaw_mem0 collection) — for semantic search via mem0_recall.py
  2. Markdown file in the project's auto-memory dir — for human-readable log

Guards:
- stop_hook_active=True → skip (prevent infinite loop)
- Short/trivial responses → skip
- Always exits 0 (never blocks)
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
from datetime import datetime, timezone

from mem0_config import MEM0_CONFIG, USER_ID  # type: ignore
MIN_RESPONSE_LEN = 100  # Skip trivial one-liners


def _project_memory_dir(transcript_path: str | None) -> pathlib.Path | None:
    """Derive the project auto-memory dir from the session transcript path.

    Claude stores sessions at:
      ~/.claude/projects/<escaped-cwd>/sessions/<session-id>.jsonl
    The memory dir lives at:
      ~/.claude/projects/<escaped-cwd>/memory/

    Walk up ancestors until we find the directory whose parent is named
    "projects" — that is the slug dir, regardless of nesting depth.
    """
    if not transcript_path:
        return None
    try:
        p = pathlib.Path(transcript_path)
        for ancestor in p.parents:
            if ancestor.parent.name == "projects":
                return ancestor / "memory"
    except Exception:
        pass
    return None


def _append_to_markdown(memory_dir: pathlib.Path, facts: list[str]) -> None:
    """Append extracted facts to mem0_extractions.md in the project memory dir."""
    memory_dir.mkdir(parents=True, exist_ok=True)
    md_path = memory_dir / "mem0_extractions.md"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"\n## {ts}"] + [f"- {f}" for f in facts] + [""]
    with open(md_path, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def main() -> None:
    try:
        data = json.loads(sys.stdin.read())
    except Exception:
        sys.exit(0)

    # Guard: already continuing due to a stop hook — skip to avoid loop
    if data.get("stop_hook_active"):
        sys.exit(0)

    # Skip if GROQ_API_KEY not set (used for LLM inference; embedder uses local Ollama)
    if not os.environ.get("GROQ_API_KEY"):
        sys.exit(0)

    last_message = data.get("last_assistant_message", "").strip()
    if len(last_message) < MIN_RESPONSE_LEN:
        sys.exit(0)

    # Skip pure code/tool-only responses (heuristic: no sentences)
    if last_message.count(". ") < 2 and last_message.count("\n") > 20:
        sys.exit(0)

    transcript_path = data.get("transcript_path")
    memory_dir = _project_memory_dir(transcript_path)

    try:
        from mem0 import Memory  # type: ignore

        m = Memory.from_config(MEM0_CONFIG)
        # Use infer=True: mem0 LLM extracts facts from the message
        result = m.add(last_message, user_id=USER_ID, infer=True)

        # Dual-write: also append extracted facts to markdown
        if memory_dir:
            results_list = (
                result.get("results", []) if isinstance(result, dict) else
                (result if isinstance(result, list) else [])
            )
            facts = [
                r.get("memory", r.get("data", ""))
                for r in results_list
                if r.get("event") in ("ADD", "UPDATE") and r.get("memory", r.get("data"))
            ]
            if facts:
                _append_to_markdown(memory_dir, facts)
    except Exception:
        pass  # Never block

    sys.exit(0)


if __name__ == "__main__":
    main()
