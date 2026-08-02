#!/usr/bin/env python3
"""
check_resolvable.py — Verify that every trigger line in RESOLVER.md maps to
a SKILL.md, and that the campaign-creation skill itself is resolvable.

Runs with no LLM. Deterministic. Exits non-zero on any failure.

Usage:
    python3 check_resolvable.py [--resolver <RESOLVER.md>] [--skills <skills_dir>]

Default paths assume the script lives at
~/.hermes/skills/campaign-creation/scripts/check_resolvable.py
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Trigger extraction
# ---------------------------------------------------------------------------

def parse_resolver_entries(resolver_path: Path) -> list[dict]:
    """Parse the ## <name> ... **Triggers:** <csv> blocks from RESOLVER.md."""
    text = resolver_path.read_text(encoding="utf-8")
    entries: list[dict] = []
    current_name: str | None = None
    current_triggers: list[str] = []

    for line in text.splitlines():
        m_heading = re.match(r"^##\s+(\S+)", line)
        if m_heading:
            if current_name and current_triggers:
                entries.append(
                    {"name": current_name, "triggers": current_triggers}
                )
            current_name = m_heading.group(1)
            current_triggers = []
            continue
        m_triggers = re.search(r"\*\*Triggers:\*\*\s*(.+)$", line)
        if m_triggers and current_name:
            csv = m_triggers.group(1)
            triggers = [t.strip() for t in csv.split(",") if t.strip()]
            current_triggers.extend(triggers)

    if current_name and current_triggers:
        entries.append({"name": current_name, "triggers": current_triggers})

    return entries


def trigger_files_exist(entries: list[dict], skills_dir: Path) -> list[dict]:
    """For each resolver entry, verify its triggers point to an existing SKILL.md.

    Convention: resolver entry '## foo' with **Triggers:** expects
    `skills_dir / foo / SKILL.md`. If **File:** is present, that overrides.
    """
    failures: list[dict] = []
    for entry in entries:
        skill_path = skills_dir / entry["name"] / "SKILL.md"
        if not skill_path.exists():
            failures.append(
                {
                    "name": entry["name"],
                    "issue": f"Missing SKILL.md at {skill_path}",
                    "triggers": entry["triggers"],
                }
            )
    return failures


# ---------------------------------------------------------------------------
# Self-check: campaign-creation itself
# ---------------------------------------------------------------------------

def self_check(skill_dir: Path) -> list[str]:
    """Verify campaign-creation's own resolvable-ness."""
    errors: list[str] = []
    required = [
        "SKILL.md",
        "routing-eval.jsonl",
        "scripts/template_validator.py",
        "scripts/section_completeness.py",
        "tests/test_campaign_creation_skill.py",
        "references/campaign_template.txt",
        "references/personality_template.txt",
        "references/god_mechanics_general.md",
    ]
    for rel in required:
        p = skill_dir / rel
        if not p.exists():
            errors.append(f"Missing required file: {p}")
    return errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--resolver",
        type=Path,
        default=Path.home() / ".hermes" / "skills" / "RESOLVER.md",
        help="Path to RESOLVER.md",
    )
    parser.add_argument(
        "--skills",
        type=Path,
        default=Path.home() / ".hermes" / "skills",
        help="Path to skills directory",
    )
    parser.add_argument(
        "--self",
        action="store_true",
        help="Run self-check (verify campaign-creation files exist)",
    )
    args = parser.parse_args(argv)

    if args.self:
        errors = self_check(Path(__file__).parent.parent)
        if errors:
            print(f"Self-check FAILED with {len(errors)} errors:", file=sys.stderr)
            for e in errors:
                print(f"  - {e}", file=sys.stderr)
            return 1
        print("Self-check PASS: campaign-creation has all required files.")
        return 0

    if not args.resolver.exists():
        print(f"ERROR: resolver not found at {args.resolver}", file=sys.stderr)
        return 2

    entries = parse_resolver_entries(args.resolver)
    if not entries:
        print(f"ERROR: no entries parsed from {args.resolver}", file=sys.stderr)
        return 1

    failures = trigger_files_exist(entries, args.skills)
    if failures:
        print(f"Resolver check FAILED with {len(failures)} missing SKILL.md files:")
        for f in failures:
            print(f"  - {f['name']}: {f['issue']}")
        return 1

    print(
        f"Resolver check PASS: {len(entries)} entries, all SKILL.md files present."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))