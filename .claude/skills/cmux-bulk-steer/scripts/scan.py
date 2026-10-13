#!/usr/bin/env python3
"""cmux-bulk-steer — canonical fleet scanner (Phase 1+2 of the skill).

One hardened implementation of the read-all + classify + dedupe surface so every
cycle runs the SAME logic instead of a re-written inline heredoc. Encodes the
lessons that kept regressing when the classifier was ad hoc:

  * CHURN is detected from the CURRENT state (last ~20 lines), and wins over
    historical text.
  * QUOTA/DEAD is detected from the CURRENT-state tail only (last ~10 lines,
    footers excluded) — a directive that merely mentions "quota", or an old
    quota error deep in scrollback, must NOT classify a working surface dead.
  * Footer lines ("? for shortcuts", "Ask Codex to do anything", "esc to
    cancel") are never treated as a parked question.
  * A session that exited to a plain shell (jleechan@…$ and no active marker)
    is FINISHED, not parked/idle-agent.
  * Reads the FULL available buffer (--scrollback --lines 1500) before deciding.

Usage:
  python3 scan.py                 # human summary
  python3 scan.py --json          # machine-readable
  python3 scan.py --parked-only   # just the parked questions
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

SCROLLBACK_LINES = 1500

CHURN_RE = re.compile(
    r"Working\s*\(|Worked for|Thinking|Pursuing goal|Reticulating|"
    r"Precipitating|Photosyn|esc to cancel|⠋|⠙|⠸|⠴|⠼|⠏"
)
DEAD_RE = re.compile(r"quota reached|rate-limit-options|weekly limit|usage limit", re.I)
SHELL_RE = re.compile(r"jleechan@[^\n]*\$\s*$")
FOOTER_RE = re.compile(r"\? for shortcuts|Ask Codex to do anything|esc to cancel$|GPT-\d")
PARK_RE = re.compile(r"Want me to|Which\?|awaiting|pending your", re.I)
QUESTION_RE = re.compile(r"[a-z0-9\)\?]\?\s*$")


def surfaces() -> list[tuple[str, str, str]]:
    tree = subprocess.run(["cmux", "tree", "--all"], capture_output=True, text=True).stdout
    out: list[tuple[str, str, str]] = []
    ws = None
    wn = ""
    for line in tree.splitlines():
        m = re.search(r'workspace (workspace:\d+) "(.*?)"', line)
        if m:
            ws, wn = m.group(1), m.group(2)
        m = re.search(r"surface (surface:\d+) \[(terminal)\]", line)
        if m and ws:
            out.append((ws, wn, m.group(1)))
    return out


def capture(ws: str, sf: str) -> list[str]:
    out = subprocess.run(
        ["cmux", "capture-pane", "--workspace", ws, "--surface", sf,
         "--scrollback", "--lines", str(SCROLLBACK_LINES)],
        capture_output=True, text=True,
    ).stdout
    return [l.rstrip() for l in out.splitlines() if l.strip()]


def classify(lines: list[str]) -> tuple[str, str]:
    if not lines:
        return "EMPTY", ""
    last = lines[-1]
    nonfooter = [l for l in lines if not FOOTER_RE.search(l)]
    tail20 = "\n".join(lines[-20:])
    tail_state = "\n".join(nonfooter[-10:])

    if DEAD_RE.search(tail_state):
        m = DEAD_RE.search(tail_state)
        return "DEAD", m.group(0)
    if CHURN_RE.search(tail20):
        return "CHURN", (CHURN_RE.search(tail20).group(0) or "").strip()
    if SHELL_RE.search(last):
        return "SHELL", last[:80]
    body_tail = "\n".join(nonfooter[-8:])
    if PARK_RE.search(body_tail) or QUESTION_RE.search(body_tail):
        return "PARKED", body_tail.replace("\n", " | ")[:300]
    return "IDLE", ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--parked-only", action="store_true")
    args = ap.parse_args()

    rows = []
    for ws, wn, sf in surfaces():
        lines = capture(ws, sf)
        kind, detail = classify(lines)
        rows.append({"workspace": wn, "surface": sf, "state": kind,
                     "detail": detail, "lines_read": len(lines)})

    if args.json:
        print(json.dumps({"scrollback_lines": SCROLLBACK_LINES, "surfaces": rows}, indent=2))
        return 0

    counts: dict[str, int] = {}
    for r in rows:
        counts[r["state"]] = counts.get(r["state"], 0) + 1
    if args.parked_only:
        for r in rows:
            if r["state"] == "PARKED":
                print(f"[{r['workspace']}/{r['surface']}]\n  {r['detail']}\n")
        return 0

    print(f"terminals={len(rows)} " + " ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    for state in ("PARKED", "DEAD", "STALLED", "CHURN"):
        sel = [r for r in rows if r["state"] == state]
        if sel and state in ("PARKED", "DEAD"):
            print(f"\n{state}:")
            for r in sel:
                print(f"  [{r['workspace']}/{r['surface']}] {r['detail'][:120]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
