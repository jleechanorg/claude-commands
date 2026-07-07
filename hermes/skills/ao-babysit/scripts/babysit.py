#!/usr/bin/env python3
"""
ao-babysit — Poll and steer an active AO worker tmux session.

Usage:
    babysit.py poll    --session SESSION --slack-channel CH --slack-thread-ts TS --task-summary TEXT
    babysit.py babysit --session SESSION --slack-channel CH --slack-thread-ts TS --task-summary TEXT [--poll-interval 300]
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK_HERMES", "")
STATE_DIR = Path.home() / ".hermes" / "skills" / "ao-babysit" / "state"
AO_SERVER_UUID = "9cc70dbf8ac4"  # embedded in tmux session names

# ── Slack ──────────────────────────────────────────────────────────────────────

def slack_post(channel: str, text: str, thread_ts: str = "") -> None:
    """Post a message to Slack via webhook."""
    if not SLACK_WEBHOOK:
        print(f"[slack] No webhook, skipping: {text[:80]}")
        return
    payload = {
        "channel": channel,
        "text": text,
    }
    if thread_ts:
        payload["thread_ts"] = thread_ts
    subprocess.run(
        ["curl", "-s", "-X", "POST", "--fail-with-body",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(payload), SLACK_WEBHOOK],
        capture_output=True, timeout=10
    )

# ── AO / tmux discovery ───────────────────────────────────────────────────────

def find_tmux_session(session_id: str) -> Optional[str]:
    """Return the full tmux session name (e.g. '9cc70dbf8ac4-ao-4250') or None."""
    result = subprocess.run(
        ["tmux", "list-sessions", "-F", "#{session_name}"],
        capture_output=True, text=True, timeout=5
    )
    if result.returncode != 0:
        return None
    for name in result.stdout.strip().split("\n"):
        if session_id in name:
            return name
    return None

def tmux_capture(session_name: str, lines: int = 50) -> str:
    """Capture the last N lines of a tmux pane."""
    # Try the main pane first
    result = subprocess.run(
        ["tmux", "capture-pane", "-t", session_name, "-p",
         "-S", f"-{lines}"],
        capture_output=True, text=True, timeout=10
    )
    if result.returncode == 0:
        return result.stdout
    # Fallback: try capturing without size limit
    result = subprocess.run(
        ["tmux", "capture-pane", "-t", session_name, "-p"],
        capture_output=True, text=True, timeout=10
    )
    return result.stdout if result.returncode == 0 else ""

# ── State ──────────────────────────────────────────────────────────────────────

def state_path(session_id: str) -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    return STATE_DIR / f"{session_id}.json"

def read_state(session_id: str) -> dict:
    p = state_path(session_id)
    if p.exists():
        return json.loads(p.read_text())
    return {
        "session_id": session_id,
        "first_seen": iso_now(),
        "last_seen": None,
        "last_output_hash": None,
        "poll_count": 0,
        "last_progress_post": None,
        "status": "unknown",
        "notes": [],
    }

def write_state(session_id: str, state: dict) -> None:
    state["last_seen"] = iso_now()
    state_path(session_id).write_text(json.dumps(state, indent=2))

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

# ── Detection heuristics ───────────────────────────────────────────────────────

DEAD_SIGNALS = [
    "connection refused",
    "session not found",
    "no such session",
    "error",
]

STUCK_PATTERNS = [
    re.compile(r"^(重复|repeated|looped|same|identical)\b", re.I),
    re.compile(r"(?:^|\n)\s*(?:grep|fgrep|rg|find)\s+[^\n]{80,}\n", re.M),  # long grep running
]

IDLE_SIGNALS = [
    "bypass permissions on",
    "shift+tab to cycle",
    "claude",
    "waiting",
    "running",
]

PROGRESS_SIGNALS = [
    "commit",
    "push",
    "git",
    "install",
    "building",
    "error",
    "fail",
    "pass",
    "test",
    "pr ",
    "pull request",
    "merge",
    "branch",
    "implement",
    "writing",
    "reading",
    "python",
    "typescript",
    "node",
]

PR_SIGNALS = [
    re.compile(r"https://github\.com/[\w-]+/[\w-]+/pull/\d+", re.I),
    re.compile(r"Successfully created PR", re.I),
    re.compile(r"gh pr (create|merge)", re.I),
]


def analyze_output(output: str, state: dict) -> dict:
    """
    Returns a dict with keys:
      - status: "alive" | "dead" | "stuck" | "idle" | "done"
      - summary: one-line description of current activity
      - detail: multi-line detail for Slack
      - nudge: optional nudge text to send via ao send
    """
    now = iso_now()
    output_lower = output.lower()
    lines = output.strip().split("\n")
    last_lines = [l.strip() for l in lines[-10:] if l.strip()]

    # ── Dead check ────────────────────────────────────────────────────────────
    for sig in DEAD_SIGNALS:
        if sig in output_lower:
            return {
                "status": "dead",
                "summary": f"Session appears dead — '{sig}' detected in terminal",
                "detail": "\n".join(last_lines[-5:]),
                "nudge": None,
            }

    # ── PR done check ─────────────────────────────────────────────────────────
    for pattern in PR_SIGNALS:
        if pattern.search(output):
            # Extract PR URL if present
            match = pattern.search(output)
            pr_info = match.group(0) if match else "PR detected"
            return {
                "status": "done",
                "summary": f"PR created: {pr_info}",
                "detail": "\n".join(last_lines[-5:]),
                "nudge": None,
            }

    # ── Stuck check ───────────────────────────────────────────────────────────
    # Check for repeated identical output (looping)
    if state.get("last_output_hash"):
        import hashlib
        current_hash = hashlib.md5(output.encode()).hexdigest()
        if current_hash == state["last_output_hash"]:
            # Same output as last poll — could be stuck
            for pattern in STUCK_PATTERNS:
                if pattern.search(output):
                    return {
                        "status": "stuck",
                        "summary": "Agent appears to be looping on the same step",
                        "detail": "\n".join(last_lines[-5:]),
                        "nudge": (
                            "I'm Hermes, an AI agent — not a human. "
                            "It looks like you're looping on the same step. "
                            "Stop searching/reading and take the next concrete action: "
                            "write the code, run the test, or push the branch. "
                            "What is the ONE thing you need to do right now?"
                        ),
                    }
        state["last_output_hash"] = current_hash

    # Check if output shows agent is working (progress signals)
    activity_score = sum(1 for sig in PROGRESS_SIGNALS if sig in output_lower)
    idle_score = sum(1 for sig in IDLE_SIGNALS if sig in output_lower)

    # Check timestamp of last terminal activity
    # If we see "bypass permissions on (shift+tab to cycle)" with no actual commands
    # running, it might be waiting at a prompt
    if "bypass permissions on" in output_lower and activity_score < 2:
        return {
            "status": "idle",
            "summary": "Agent is at a prompt, may be waiting",
            "detail": "\n".join(last_lines[-5:]),
            "nudge": (
                "I'm Hermes, an AI agent — not a human. "
                "Are you waiting at a prompt? If you need input to proceed, "
                "tell me what you need. If you're stuck, state the one blocker."
            ),
        }

    if activity_score >= 2:
        return {
            "status": "alive",
            "summary": "Working — processing terminal output",
            "detail": "\n".join(last_lines[-5:]),
            "nudge": None,
        }

    return {
        "status": "alive",
        "summary": "Active (terminal has content)",
        "detail": "\n".join(last_lines[-5:]),
        "nudge": None,
    }




# ── PR merged-state check (added 2026-07-03, fix for babysit-spam bug) ─────────

PR_URL_RE = re.compile(r"https://github\.com/([\w.-]+)/([\w.-]+)/pull/(\d+)")
PR_REF_RE = re.compile(r"\bPR\s*#?\s*(\d{3,5})\b", re.I)

def extract_pr_refs(text: str) -> list[dict]:
    """Extract (owner, repo, number) tuples from text containing PR URLs or 'PR #NNNN' refs."""
    refs: list[dict] = []
    seen: set[tuple[str, str, int]] = set()
    for m in PR_URL_RE.finditer(text):
        owner, repo, num = m.group(1), m.group(2), int(m.group(3))
        key = (owner, repo, num)
        if key not in seen:
            seen.add(key)
            refs.append({"owner": owner, "repo": repo, "number": num, "via": "url"})
    # Only do the bare-PR-number lookup if we have a hint about which repo
    # (we don't know the repo from "PR #7711" alone, so this is best-effort)
    for m in PR_REF_RE.finditer(text):
        num = int(m.group(1))
        # De-dup: skip if already found via URL
        if any(r["number"] == num for r in refs):
            continue
        refs.append({"owner": None, "repo": None, "number": num, "via": "ref"})
    return refs

def check_pr_terminal_state(pr_ref: dict) -> Optional[str]:
    """
    Return "MERGED", "CLOSED", "OPEN", or None if state cannot be determined.
    For refs without owner/repo, attempts $GITHUB_REPOSITORY by default
    (the most common babysit target per 2026-07-03 sweep).
    """
    owner = pr_ref.get("owner") or "jleechanorg"
    repo = pr_ref.get("repo") or "your-project.com"
    number = pr_ref["number"]
    try:
        result = subprocess.run(
            ["gh", "pr", "view", str(number), "--repo", f"{owner}/{repo}",
             "--json", "state"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0:
            return None
        return json.loads(result.stdout).get("state")
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None

def is_pr_terminal(text: str) -> tuple[bool, Optional[dict]]:
    """
    Check if any PR referenced in `text` is in a terminal state (MERGED or CLOSED).
    Returns (is_terminal, info) where info is the merged/closed PR details.
    Used by poll() to short-circuit babysit loops on dead PRs (bug-ref: 2026-07-03
    babysit-wa-2403-PR7711 fired 251 polls for 11 days after merge).
    """
    refs = extract_pr_refs(text)
    for ref in refs:
        state = check_pr_terminal_state(ref)
        if state in ("MERGED", "CLOSED"):
            return True, {"ref": ref, "state": state}
    return False, None

# ── ao send ──────────────────────────────────────────────────────────────────

def ao_send(session_id: str, message: str) -> bool:
    """Send a message to an AO worker via ao send."""
    result = subprocess.run(
        ["ao", "send", session_id, "--message", message],
        capture_output=True, text=True, timeout=15
    )
    return result.returncode == 0


# ── Main poll logic ────────────────────────────────────────────────────────────

def cronjob_remove(job_id: str) -> tuple[bool, str]:
    """
    Remove a cron job by ID via the `cronjob` CLI.

    Returns (success, output). On success, the parent cron is disabled and no
    further ticks fire. On failure, the babysit must still emit [SILENT] on
    subsequent ticks — the cronjob registry watcher will catch it within 30 min.

    Why this lives here (added 2026-07-05, v2): the babysit prompt template
    documents self-cancel via `cronjob action=remove`, but the babysit.py
    script never had a way to know its own job_id — so the documented
    self-cancel was unreachable. This helper closes the loop.
    """
    if not job_id:
        return False, "no --cron-job-id provided"
    try:
        r = subprocess.run(
            ["cronjob", "action=remove", f"job_id={job_id}"],
            capture_output=True, text=True, timeout=10,
        )
        ok = (r.returncode == 0)
        return ok, (r.stdout or r.stderr or "").strip()[:200]
    except FileNotFoundError:
        return False, "cronjob CLI not on PATH"
    except subprocess.TimeoutExpired:
        return False, "cronjob action=remove timed out"


def poll(session_id: str, slack_channel: str, slack_thread_ts: str,
         task_summary: str, cron_job_id: str = "") -> dict:
    """Single poll of a session. Returns analysis dict.

    Args:
        cron_job_id: If provided, the babysit will issue
            `cronjob action=remove job_id=<cron_job_id>` upon detecting a
            terminal PR (MERGED/CLOSED). This is the missing piece that
            turns the skill-documented self-cancel into an executable
            contract (added 2026-07-05, v2).
    """
    state = read_state(session_id)
    state["poll_count"] += 1

    # ── New: terminal-PR short-circuit (fix for 2026-07-03 babysit-spam bug) ──
    # If any PR referenced in task_summary is MERGED or CLOSED on GitHub, the
    # babysit's job is done. Post a single terminal message and exit. Without
    # this check, babysits spam Slack forever after merge because the worker
    # tmux session may still exist and analyze_output never sees a merge event.
    is_terminal, term_info = is_pr_terminal(task_summary)
    if is_terminal:
        ref = term_info["ref"]
        state["status"] = "terminal_pr"
        state["terminal_pr"] = term_info
        write_state(session_id, state)
        owner_repo = f"{ref['owner']}/{ref['repo']}" if ref.get("owner") else "$GITHUB_REPOSITORY"
        cancel_note = ""
        if cron_job_id:
            ok, out = cronjob_remove(cron_job_id)
            cancel_note = (
                f"\nSelf-cancel: `cronjob action=remove job_id={cron_job_id}` → "
                f"{'OK' if ok else 'FAILED'} ({out})"
            )
            if ok:
                state["cron_self_canceled"] = True
                state["cron_job_id"] = cron_job_id
                write_state(session_id, state)
        msg = (
            f"[terminal] *{session_id} — PR #{ref['number']} {term_info['state']}*\n"
            f"Repo: {owner_repo}\n"
            f"Task: {task_summary}\n"
            f"Polls run: {state['poll_count']}\n"
            f"_Babysit exiting: PR is in terminal state, no further monitoring._"
            f"{cancel_note}"
        )
        slack_post(slack_channel, msg, slack_thread_ts)
        return {"status": "terminal_pr", "state": state, "terminal_pr": term_info,
                "cron_self_canceled": bool(cancel_note and "OK" in cancel_note)}

    tmux_session = find_tmux_session(session_id)

    if not tmux_session:
        # Session gone — dead
        state["status"] = "dead"
        write_state(session_id, state)
        msg = (
            f"[alarm] *{session_id} died* (tmux session gone)\n"
            f"Task: {task_summary}\n"
            f"Polls: {state['poll_count']}\n"
            f"Last seen: {state['last_seen']}\n"
            f"_Notes:_\n" + "\n".join(f"• {n}" for n in state.get("notes", []))
        )
        slack_post(slack_channel, msg, slack_thread_ts)
        return {"status": "dead", "state": state}

    output = tmux_capture(tmux_session, lines=80)
    analysis = analyze_output(output, state)

    state["status"] = analysis["status"]
    if "notes" not in state:
        state["notes"] = []

    now_dt = datetime.now(timezone.utc)
    last_progress = state.get("last_progress_post")
    time_since_progress = 0
    if last_progress:
        last_dt = datetime.fromisoformat(last_progress.replace("Z", "+00:00"))
        time_since_progress = (now_dt - last_dt).total_seconds()

    if analysis["status"] == "done":
        msg = (
            f"[PR] *{session_id} done*\n"
            f"Task: {task_summary}\n"
            f"Result: {analysis['summary']}\n"
            f"Last output:\n```{analysis['detail']}```"
        )
        slack_post(slack_channel, msg, slack_thread_ts)
        state["last_progress_post"] = iso_now()
        write_state(session_id, state)
        return analysis

    elif analysis["status"] == "dead":
        msg = (
            f"[alarm] *{session_id} died*\n"
            f"Task: {task_summary}\n"
            f"Last output:\n```{analysis['detail']}```"
        )
        slack_post(slack_channel, msg, slack_thread_ts)
        write_state(session_id, state)
        return analysis

    elif analysis["status"] in ("stuck", "idle") and analysis["nudge"]:
        # Send nudge via ao send
        nudge = analysis["nudge"]
        nudge_ok = ao_send(session_id, nudge)
        note = f"[{iso_now()}] Nudge sent ({analysis['status']}), ao_send={'ok' if nudge_ok else 'failed'}"
        state["notes"].append(note)
        if len(state["notes"]) > 20:
            state["notes"] = state["notes"][-20:]

        msg = (
            f"[nudge] *{session_id} — {analysis['status']} — corrective nudge sent*\n"
            f"ao_send: {'ok' if nudge_ok else 'FAILED'}\n"
            f"Last output:\n```{analysis['detail']}```"
        )
        slack_post(slack_channel, msg, slack_thread_ts)
        state["last_progress_post"] = iso_now()
        write_state(session_id, state)
        return analysis

    elif time_since_progress >= 300 or state["poll_count"] == 1:
        # Progress update every 5 min
        msg = (
            f"[poll] *{session_id}* — {analysis['summary']}\n"
            f"Task: {task_summary}\n"
            f"Poll #{state['poll_count']} | Last: {state['last_seen']}\n"
            f"Last output:\n```{analysis['detail']}```"
        )
        slack_post(slack_channel, msg, slack_thread_ts)
        state["last_progress_post"] = iso_now()
        write_state(session_id, state)
        return analysis

    else:
        write_state(session_id, state)
        return analysis


# ── Babysitter loop ───────────────────────────────────────────────────────────

def babysit_loop(session_id: str, slack_channel: str, slack_thread_ts: str,
                 task_summary: str, poll_interval: int = 300,
                 cron_job_id: str = "") -> None:
    """Run the babysitter loop indefinitely."""
    print(f"Babysitting {session_id} every {poll_interval}s. Ctrl-C to stop.")
    while True:
        result = poll(session_id, slack_channel, slack_thread_ts, task_summary, cron_job_id=cron_job_id)
        if result["status"] in ("done", "dead", "terminal_pr"):
            print(f"Session {session_id} is {result['status']}. Exiting loop.")
            break
        print(f"[{iso_now()}] {result['summary']}")
        time.sleep(poll_interval)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="ao-babysit")
    sub = parser.add_subparsers(dest="cmd")

    poll_cmd = sub.add_parser("poll", help="Single poll + report")
    poll_cmd.add_argument("--session", required=True)
    poll_cmd.add_argument("--slack-channel", required=True)
    poll_cmd.add_argument("--slack-thread-ts", required=True)
    poll_cmd.add_argument("--task-summary", required=True)
    poll_cmd.add_argument("--cron-job-id", default="",
                          help="If provided, on terminal PR the babysit will "
                               "issue `cronjob action=remove job_id=<value>` "
                               "to self-cancel. This is the executable "
                               "companion to the skill-documented self-cancel "
                               "discipline (added 2026-07-05, v2).")

    babysit_cmd = sub.add_parser("babysit", help="Continuous babysitter loop")
    babysit_cmd.add_argument("--session", required=True)
    babysit_cmd.add_argument("--slack-channel", required=True)
    babysit_cmd.add_argument("--slack-thread-ts", required=True)
    babysit_cmd.add_argument("--task-summary", required=True)
    babysit_cmd.add_argument("--poll-interval", type=int, default=300)
    babysit_cmd.add_argument("--cron-job-id", default="",
                             help="If provided, on terminal PR the babysit will "
                                  "issue `cronjob action=remove job_id=<value>` "
                                  "to self-cancel.")

    args = parser.parse_args()

    if args.cmd == "poll":
        poll(args.session, args.slack_channel, args.slack_thread_ts,
             args.task_summary, cron_job_id=args.cron_job_id)
    elif args.cmd == "babysit":
        babysit_loop(args.session, args.slack_channel, args.slack_thread_ts,
                     args.task_summary, args.poll_interval,
                     cron_job_id=args.cron_job_id)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
