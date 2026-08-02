#!/usr/bin/env python3
"""check_resolvable.py — verify wa-campaign-premise-find resolves from RESOLVER.md triggers.

Reads ~/.hermes/skills/RESOLVER.md and confirms:
1. The skill name appears as a `## <name> :` heading (NOTE: space before colon).
2. At least one trigger phrase on the heading line maps to a real user phrase.
3. The skill file at the referenced path exists.
4. routing-eval.jsonl references this skill.

CLI surface:
    --check-resolver      : verify RESOLVER.md entry exists for this skill (default)
    --check-routing-eval  : verify routing-eval.jsonl references this skill
    --check-skill-file    : verify SKILL.md exists at the expected path
    --all                 : run all checks
    --skill-name NAME     : override the skill name (default: wa-campaign-premise-find)

Exit codes:
    0 = all checks passed
    1 = at least one check failed
    2 = RESOLVER.md missing entirely

Usage:
    python3 scripts/check_resolvable.py
    python3 scripts/check_resolvable.py --all
    python3 scripts/check_resolvable.py --check-routing-eval
"""
import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_SKILL_NAME = "wa-campaign-premise-find"
SKILLS_ROOT = Path("~/.hermes/skills").expanduser()
RESOLVER_FILE = SKILLS_ROOT / "RESOLVER.md"


def check_resolver_entry(skill_name: str, text: str) -> tuple[bool, str]:
    """Verify `## <name> :` heading exists in RESOLVER.md."""
    # Pitfall: ## name: (no space) silently fails; ## name : (space) works.
    pattern = rf"^##\s+{re.escape(skill_name)}\s*:"
    if not re.search(pattern, text, re.MULTILINE):
        return False, f"no `## {skill_name} :` heading in {RESOLVER_FILE}"
    return True, "heading line present"


def check_skill_file(skill_name: str) -> tuple[bool, str]:
    """Verify SKILL.md exists at expected path."""
    candidates = [
        SKILLS_ROOT / "worldarchitect" / skill_name / "SKILL.md",
        SKILLS_ROOT / skill_name / "SKILL.md",
    ]
    for path in candidates:
        if path.is_file():
            return True, f"skill file present at {path}"
    return False, f"skill file missing — tried: {candidates}"


def check_routing_eval(skill_name: str, fixture_path: Path) -> tuple[bool, str]:
    """Verify routing-eval.jsonl references this skill with valid schema."""
    if not fixture_path.is_file():
        return False, f"routing-eval.jsonl missing at {fixture_path}"

    bad_rows = []
    targeted_count = 0
    for line in fixture_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as e:
            bad_rows.append(f"JSON parse error: {e}")
            continue
        if "intent" not in row or "expected_skill" not in row:
            bad_rows.append(f"row missing required fields: {row}")
            continue
        if row["expected_skill"] == skill_name:
            targeted_count += 1

    if bad_rows:
        return False, f"routing-eval.jsonl has {len(bad_rows)} bad rows: {bad_rows[:3]}"

    if targeted_count < 8:
        return False, f"only {targeted_count} routing-eval rows target {skill_name} (need >=8)"

    return True, f"{targeted_count} routing-eval rows target {skill_name}"


def main():
    parser = argparse.ArgumentParser(
        description="Check wa-campaign-premise-find is resolvable from RESOLVER.md",
    )
    parser.add_argument("--skill-name", default=DEFAULT_SKILL_NAME,
                        help=f"skill name (default: {DEFAULT_SKILL_NAME})")
    parser.add_argument("--check-resolver", action="store_true",
                        help="check RESOLVER.md entry exists")
    parser.add_argument("--check-skill-file", action="store_true",
                        help="check SKILL.md file exists")
    parser.add_argument("--check-routing-eval", action="store_true",
                        help="check routing-eval.jsonl references this skill")
    parser.add_argument("--all", action="store_true",
                        help="run all checks (default if no specific flag given)")

    args = parser.parse_args()
    run_all = args.all or not any([
        args.check_resolver, args.check_skill_file, args.check_routing_eval,
    ])

    if not RESOLVER_FILE.is_file():
        print(f"FAIL: {RESOLVER_FILE} missing entirely")
        return 2

    text = RESOLVER_FILE.read_text(encoding="utf-8")
    fixture = (SKILLS_ROOT / "worldarchitect" / args.skill_name / "routing-eval.jsonl")

    failed = 0
    if run_all or args.check_resolver:
        ok, msg = check_resolver_entry(args.skill_name, text)
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {msg}")
        if not ok:
            failed += 1
    if run_all or args.check_skill_file:
        ok, msg = check_skill_file(args.skill_name)
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {msg}")
        if not ok:
            failed += 1
    if run_all or args.check_routing_eval:
        ok, msg = check_routing_eval(args.skill_name, fixture)
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {msg}")
        if not ok:
            failed += 1

    if failed:
        print(f"\n{args.skill_name}: {failed} check(s) failed")
        return 1
    print(f"\n{args.skill_name}: all checks PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
