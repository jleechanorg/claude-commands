#!/usr/bin/env python3
"""Verify the sovereign/multiverse tier is actually disabled per the campaign-tier-redesign umbrella.

Runs three gates against the your-project.com repo at the path passed on argv:
1. Constants gate — UNIVERSE_CONTROL_THRESHOLD is the sentinel (>= 99999) OR explicitly commented disabled.
2. Detector gate — campaign_divine.py's is_multiverse_upgrade_available() returns False for any sane state.
3. Loader gate — agent_prompts.py does NOT load any prompt file under $PROJECT_ROOT/prompts/multiverse/ (only $PROJECT_ROOT/prompts/multiverse_disabled/ or empty).

Exits 0 if all 3 gates pass, 1 otherwise. Prints the failing gate to stdout.

Usage:
    python3 scripts/verify_disable.py $HOME/repos/$GITHUB_REPOSITORY
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


SENTINEL_THRESHOLD = 99999


def gate_constants(repo: Path) -> tuple[bool, str]:
    """Gate 1 — constants.py must have UNIVERSE_CONTROL_THRESHOLD >= SENTINEL_THRESHOLD."""
    constants = repo / "mvp_site" / "constants.py"
    if not constants.exists():
        return False, f"missing {constants}"

    text = constants.read_text()
    # Match: UNIVERSE_CONTROL_THRESHOLD = <int-or-sentinel-commented>
    pattern = re.compile(
        r"UNIVERSE_CONTROL_THRESHOLD\s*=\s*"
        r"(?P<value>\d+|True|False|#.*disabled.*)"
    )
    m = pattern.search(text)
    if not m:
        return False, "UNIVERSE_CONTROL_THRESHOLD not found in constants.py"
    val = m.group("value")
    if val.startswith("#"):
        return True, f"constants.py has commented-out threshold ({val[:60]}…)"
    try:
        n = int(val)
    except ValueError:
        return False, f"UNIVERSE_CONTROL_THRESHOLD = {val!r} (not int)"
    if n >= SENTINEL_THRESHOLD:
        return True, f"UNIVERSE_CONTROL_THRESHOLD = {n} (>= {SENTINEL_THRESHOLD}, sentinel)"
    return False, f"UNIVERSE_CONTROL_THRESHOLD = {n} (< {SENTINEL_THRESHOLD}, trigger can still fire)"


def gate_detector(repo: Path) -> tuple[bool, str]:
    """Gate 2 — is_multiverse_upgrade_available() must short-circuit to False for any non-sovereign state."""
    cd = repo / "mvp_site" / "campaign_divine.py"
    if not cd.exists():
        return False, f"missing {cd}"

    text = cd.read_text()
    # Look for the function definition and check that the body starts with a return False guard
    fn_pattern = re.compile(
        r"def\s+is_multiverse_upgrade_available\s*\([^)]*\)\s*->\s*bool\s*:\s*"
        r"(?P<body>(?:\n\s+[^\n]+)+)",
        re.MULTILINE,
    )
    m = fn_pattern.search(text)
    if not m:
        return False, "is_multiverse_upgrade_available() not found"
    body = m.group("body")
    # First non-docstring statement should be a short-circuit guard
    non_blank = [line.strip() for line in body.splitlines() if line.strip() and not line.strip().startswith('"""') and not line.strip().startswith("'''")]
    if not non_blank:
        return False, "is_multiverse_upgrade_available() body is empty"
    first = non_blank[0]
    if "return False" in first or "disabled" in first.lower():
        return True, f"is_multiverse_upgrade_available() short-circuits on first statement: {first[:60]}"
    return False, f"is_multiverse_upgrade_available() first stmt is {first[:60]!r} (no short-circuit)"


def gate_loader(repo: Path) -> tuple[bool, str]:
    """Gate 3 — agent_prompts.py must not load anything from $PROJECT_ROOT/prompts/multiverse/ (only _disabled/ is OK)."""
    agent_prompts = repo / "mvp_site" / "agent_prompts.py"
    if not agent_prompts.exists():
        return False, f"missing {agent_prompts}"

    text = agent_prompts.read_text()
    # Find references to $PROJECT_ROOT/prompts/multiverse/ — those should be ONLY to *_disabled/ or moved files
    bad_refs = []
    for m in re.finditer(r"$PROJECT_ROOT/prompts/multiverse/([^\"'\\s)]+)", text):
        path = m.group(1)
        if "_disabled" in path or path.endswith(".DISABLED"):
            continue
        bad_refs.append(path)
    if bad_refs:
        return False, f"agent_prompts.py still loads multiverse files: {bad_refs[:3]}"
    return True, "agent_prompts.py has no live multiverse/ references (only *_disabled/ allowed)"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: verify_disable.py <your-project.com repo path>", file=sys.stderr)
        return 2
    repo = Path(argv[1]).expanduser().resolve()
    if not repo.is_dir():
        print(f"not a directory: {repo}", file=sys.stderr)
        return 2

    gates = [
        ("constants", gate_constants),
        ("detector", gate_detector),
        ("loader", gate_loader),
    ]
    failures = []
    for name, gate in gates:
        ok, msg = gate(repo)
        flag = "PASS" if ok else "FAIL"
        print(f"[{flag}] gate {name}: {msg}")
        if not ok:
            failures.append(name)
    if failures:
        print(f"\nVERDICT: DISABLE INCOMPLETE — failing gates: {', '.join(failures)}")
        return 1
    print("\nVERDICT: DISABLE COMPLETE — sovereign/multiverse tier is unreachable")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))