#!/usr/bin/env python3
"""UserPromptSubmit hook: inject relevant mem0 memories before Claude sees the prompt.

Searches hermes_mem0 qdrant store and returns top matches as additionalContext.
Silently exits 0 on any error — never blocks the prompt.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time

from mem0_config import MEM0_CONFIG, USER_ID, mem0_hooks_enabled  # type: ignore

# Throttle: minimum seconds between searches (avoids spamming Qdrant/Ollama on
# rapid multi-turn edits). Stored as a mtime on a temp file.
_THROTTLE_SECS = 30
_THROTTLE_FILE = os.path.join(os.path.expanduser("~"), ".cache", "mem0_recall_last")

# bd-992w mem0 recall tuning. Rollback: TOP_K=6, SCORE_THRESHOLD=0.35
TOP_K = 3
SCORE_THRESHOLD = 0.60

# Patterns that identify stale CR-review-state injection memories.
# These are embedded by the CR hook UserPromptSubmit fires and should NOT
# be re-injected on subsequent prompts — the agent must re-check live CR state.
_CR_MEM_DENYLIST = [
    re.compile(r"code review status is CHANGES_REQUESTED"),
    re.compile(r"PR has undergone \d+\+ rounds of CR feedback"),
    re.compile(r"Waiting for CR to respond"),
    re.compile(r"Already posted.*@coderabbitai"),
    re.compile(r"Previously posted @coderabbitai review"),
    re.compile(r"Awaiting re-review after"),
    re.compile(r"CHANGES_REQUESTED.*CR approved", re.IGNORECASE),
    re.compile(r"CR.*CHANGES_REQUESTED.*already.*handled", re.IGNORECASE),
    # Specific stale memories from prior CR injection sessions
    re.compile(r"Posted a review request to @coderabbitai for the pull request"),
    re.compile(r"Has a pending review for @coderabbitai"),
    re.compile(r"Expects a code review from CR"),
    re.compile(r"Waiting for CR to respond to the @coderabbitai review commands on PR"),
    re.compile(r"Posted a request for formal re-review to @coderabbitai"),
    re.compile(r"The code review status is CHANGES_REQUESTED, awaiting re-review after \d+ fixes"),
    re.compile(r"Already posted.*coderabbitai.*in the prior cycle"),
    re.compile(r"Waiting for CR to respond to the @coderabbitai review commands on PRs"),
    # Full CR instruction template text (the actual injection payload)
    re.compile(r"STEP 1.*verify reviewDecision.*STEP 2.*verify CR review state", re.DOTALL),
]


def main() -> None:
    # Read hook input
    try:
        data = json.loads(sys.stdin.read())
    except Exception:
        sys.exit(0)

    prompt = data.get("prompt", "").strip()

    # Skip short prompts and slash commands (fast path — no Qdrant/Ollama cost)
    if not prompt or len(prompt) < 20:
        sys.exit(0)
    if prompt.startswith("/"):
        sys.exit(0)

    # Skip if mem0 cannot run (fail-open: never block prompt on gate errors)
    try:
        if not mem0_hooks_enabled():
            sys.exit(0)
    except Exception as exc:
        print(f"[mem0_recall] mem0_hooks_enabled failed: {exc}", file=sys.stderr)
        sys.exit(0)

    # Throttle: skip if last recall ran within _THROTTLE_SECS
    try:
        os.makedirs(os.path.dirname(_THROTTLE_FILE), exist_ok=True)
        now = time.time()
        if os.path.exists(_THROTTLE_FILE):
            last_run = os.path.getmtime(_THROTTLE_FILE)
            if now - last_run < _THROTTLE_SECS:
                sys.exit(0)
        # Touch file to record this run (do it before the search so concurrent calls
        # also throttle even if the search is slow)
        open(_THROTTLE_FILE, "w").close()
    except Exception:
        pass  # throttle is best-effort; never block the prompt

    try:
        from mem0 import Memory  # type: ignore

        m = Memory.from_config(MEM0_CONFIG)
        raw = m.search(prompt, user_id=USER_ID, limit=TOP_K)
        results = raw.get("results", raw) if isinstance(raw, dict) else raw

        # Filter by score threshold AND denylist (drop stale CR state injection memories)
        hits = [
            r for r in results
            if isinstance(r.get("score"), (int, float)) and r["score"] >= SCORE_THRESHOLD
        ]

        def is_stale_cr_memory(mem_text: str) -> bool:
            return any(pat.search(mem_text) for pat in _CR_MEM_DENYLIST)

        stale_count = 0
        lines = ["## Relevant memories (from past sessions)"]
        for r in hits:
            mem = r.get("memory", r.get("data", "")).strip()
            score = r.get("score", 0)
            if not mem:
                continue
            if is_stale_cr_memory(mem):
                stale_count += 1
                continue
            lines.append(f"- [{score:.2f}] {mem}")

        # Exit early only when there are truly no valid memories to show
        if len(lines) == 1:  # only header = no valid memories
            sys.exit(0)

        # Report how many stale entries were skipped (after exit guard so it never
        # inflates len(lines) and defeats the early-exit)
        if stale_count > 0:
            lines.append(f"- (skipped {stale_count} stale CR-denylist memory entries)")

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
