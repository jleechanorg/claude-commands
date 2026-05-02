#!/usr/bin/env python3
"""
PR Green Check Rate-Limit Optimization Hook

Attached to UserPromptSubmit: intercepts the "You appear to be idle" green-check
reminder and applies:
  1. State guard  — skip entirely if PR is MERGED/CLOSED
  2. Idempotent trigger — skip if no state transition since last check
  3. Exponential backoff with jitter — prevents burning rate-limit budget on
     repeated idle prompts while a blocker (e.g. CR rate-limit) is pending
  4. Transition-based re-check — resets backoff when CR review state changes

State is persisted per (owner/repo/pr) in /tmp/pr_green_check/.
Exit 0 always (non-blocking).
"""
from __future__ import annotations

import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

STATE_DIR = Path("/tmp/pr_green_check")
STATE_DIR.mkdir(exist_ok=True)

# Backoff parameters
INITIAL_DELAY_SEC = 60      # 1 min before first re-check
MAX_DELAY_SEC = 3600        # 1 hour cap
BACKOFF_MULTIPLIER = 2.0
JITTER_FRAC = 0.15         # ±15% jitter


def get_git_context() -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Return (owner, repo, pr_number, branch_name) from git remotes and current branch."""
    try:
        # Get remote URL
        remote = (
            subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                capture_output=True, text=True, timeout=5,
            ).stdout.strip()
            or subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True, text=True, timeout=5,
            ).stdout.strip()
        )
        if not remote:
            return None, None, None, None

        # Parse owner/repo from URL
        # Supports: https://github.com/owner/repo.git, git@github.com:owner/repo.git
        if "@" in remote and ":" in remote:
            # SSH format: git@github.com:owner/repo.git
            # after "@" is "github.com:owner/repo.git"; split(":")[1] gives "owner/repo.git"
            after_at = remote.split("@")[1]
            path_part = after_at.split(":")[1].split("/")[-2:]
        else:
            # HTTPS format
            path_part = remote.rstrip("/").replace(".git", "").split("/")[-2:]

        if len(path_part) < 2:
            return None, None, None, None
        owner, repo = path_part[-2].replace(".git", ""), path_part[-1].replace(".git", "")

        # Get current branch
        branch = (
            subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True, text=True, timeout=5,
            ).stdout.strip()
            or subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True, timeout=5,
            ).stdout.strip()
        )
        if not branch:
            return owner, repo, None, None

        # Extract PR number from branch name (e.g. "fix/auton-poller-131", "session/ao-670", "fix/phase2-p0-determinism")
        import re
        # 1. Try to match pr-NNN pattern (backwards-compatible for "pr-74" style)
        m = re.search(r'(?:pr-)(\d+)(?:/|$)', branch)
        if m:
            return owner, repo, m.group(1), branch
        # 2. Fallback: match any 2-4 digit run anywhere in branch name
        m = re.search(r'(\d{2,4})', branch)
        if m:
            return owner, repo, m.group(1), branch
        # 3. Last-resort fallback: look up open PR by head branch via REST API
        try:
            result = subprocess.run(
                ["gh", "api", f"repos/{owner}/{repo}/pulls",
                 "--method", "GET", "--field", f"head={owner}:{branch}", "--field", "state=open", "--jq", ".[0].number"],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0 and result.stdout.strip().isdigit():
                pr_by_branch = result.stdout.strip()
                return owner, repo, pr_by_branch, branch
        except Exception:
            pass
        return owner, repo, None, branch

    except Exception:
        return None, None, None, None


def pr_belongs_to_branch(owner: str, repo: str, pr_num: str, branch: str) -> bool:
    """Check if PR #pr_num's head.ref matches (any segment of) the current branch."""
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{owner}/{repo}/pulls/{pr_num}"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0:
            return False
        pr = json.loads(result.stdout)
        pr_branch = pr.get("head", {}).get("ref", "")
        # Accept exact match OR match of the branch's last segment (handles "session/wc-18" vs "wc-18")
        return pr_branch == branch or pr_branch == branch.split("/")[-1]
    except Exception:
        return False


def get_pr_state_via_rest(owner: str, repo: str, pr_num: str) -> dict:
    """Fetch PR state and CR review decision via GitHub REST API (never rate-limited)."""
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{owner}/{repo}/pulls/{pr_num}"],
            capture_output=True, text=True, timeout=15,
            env={**os.environ, "GITHUB_TOKEN": os.environ.get("GITHUB_TOKEN", "")},
        )
        if result.returncode != 0:
            return {}
        return json.loads(result.stdout)
    except Exception:
        return {}


def get_cr_review_decision_via_rest(owner: str, repo: str, pr_num: str) -> str:
    """Get the latest coderabbitai[bot] review state, or 'none' if no review."""
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{owner}/{repo}/pulls/{pr_num}/reviews", "--paginate"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0:
            return "none"
        reviews = json.loads(result.stdout)
        cr_reviews = [r for r in reviews if r.get("user", {}).get("login") == "coderabbitai[bot]"]
        if not cr_reviews:
            return "none"
        return cr_reviews[-1].get("state", "none")
    except Exception:
        return "none"


def state_file(owner: str, repo: str, pr_num: str) -> Path:
    return STATE_DIR / f"{owner}_{repo}_{pr_num}.json"


def read_state(fp: Path) -> dict:
    try:
        return json.loads(fp.read_text())
    except Exception:
        return {}


def write_state(fp: Path, data: dict) -> None:
    try:
        fp.write_text(json.dumps(data, indent=2))
    except Exception:
        pass


def jitter(delay: float) -> float:
    """Apply ±JITTER_FRAC jitter to delay."""
    spread = delay * JITTER_FRAC
    return delay + random.uniform(-spread, spread)


def exponential_backoff(state: dict) -> tuple[float, float]:
    """Returns (delay_sec, new_backoff_multiplier) using persisted backoff."""
    multiplier = state.get("backoff_multiplier", 1.0)
    delay = INITIAL_DELAY_SEC * multiplier
    delay = min(delay, MAX_DELAY_SEC)
    delay = jitter(delay)
    new_multiplier = min(multiplier * BACKOFF_MULTIPLIER, 32.0)
    return delay, new_multiplier


def main() -> None:
    owner, repo, pr_num, branch = get_git_context()
    if not all([owner, repo, pr_num]):
        sys.exit(0)  # Not in a PR context — skip

    # Guard: skip if the extracted PR number belongs to a DIFFERENT branch.
    # This prevents sessions on AO worktrees like "wc-18" from incorrectly matching
    # an unrelated closed PR #18 in the same repo.
    if branch and not pr_belongs_to_branch(owner, repo, pr_num, branch):
        # PR number was extracted from branch name but belongs to a different branch — not our PR
        sys.exit(0)

    fp = state_file(owner, repo, pr_num)
    state = read_state(fp)

    # ── 1. Fetch live PR state FIRST (before any state guard check) ─────────
    # Always hit the API to get current state — avoids persisting stale "OPEN" that
    # prevents the merged-closed guard from firing after auto-merge completes.
    pr_info = get_pr_state_via_rest(owner, repo, pr_num)
    if not pr_info:
        # 404 / not found — treat as CLOSED so the state guard below skips the hook
        current_pr_state = "CLOSED"
    else:
        current_pr_state = pr_info.get("state", "OPEN").upper()

    # ── 2. State guard: skip if PR is MERGED or CLOSED ────────────────────────
    if current_pr_state in ("MERGED", "CLOSED"):
        # Update persisted state so future invocations skip without API call
        state["pr_state"] = current_pr_state
        state["backoff_multiplier"] = 1.0
        write_state(fp, state)
        sys.exit(0)

    # ── 2b. Persist PR state ─────────────────────────────────────────────────────
    state["pr_state"] = current_pr_state
    write_state(fp, state)

    # ── 3. Transition-based trigger: CR review state changed → immediate ───────
    current_cr_state = get_cr_review_decision_via_rest(owner, repo, pr_num)
    prev_cr_state = state.get("cr_review_state", "none")

    if current_cr_state != prev_cr_state:
        # CR state transitioned — reset backoff and allow immediate check
        state["cr_review_state"] = current_cr_state
        state["backoff_multiplier"] = 1.0
        state["last_check_at"] = 0  # allows immediate check
        write_state(fp, state)
        sys.exit(0)  # Allow the green check to proceed

    # ── 4. Exponential backoff: skip if within backoff window ─────────────────
    now = time.time()
    last_check = state.get("last_check_at", 0)
    delay, new_multiplier = exponential_backoff(state)

    if last_check > 0 and (now - last_check) < delay:
        # Within backoff window — write skip flag so compose-commands.sh exits early
        skip_flag = STATE_DIR / f".skip_{owner}_{repo}_{pr_num}"
        skip_flag.write_text(json.dumps({
            "until": now + delay,
            "reason": f"backoff {delay:.0f}s",
            "pr_num": pr_num,
        }))
        sys.exit(0)  # Exit 0 — don't block subsequent hooks, but signal skip

    # ── 5. Allow check to proceed — update state ──────────────────────────────
    state["last_check_at"] = now
    state["backoff_multiplier"] = new_multiplier
    write_state(fp, state)

    sys.exit(0)


if __name__ == "__main__":
    main()
