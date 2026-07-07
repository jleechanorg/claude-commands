#!/usr/bin/env python3
"""check_resolvable.py — structural pass on the resolver graph.

Reads the LIVE skills/RESOLVER.md and walks every `## <skill-name>` heading.
For each heading, extracts the file path next to it, then asserts:
  1. The path points to an existing SKILL.md (orphan detection).
  2. The heading line contains at least one comma-separated trigger phrase
     (so the resolver regex actually matches — gbrain's pitfall).
  3. No two headings claim the same skill (dup-key).
  4. No heading line is unreachable due to whitespace-only (ambiguous).

Usage:
    python3 -m check_resolvable --repo <repo-root>
    python3 -m check_resolvable --resolver <path/to/RESOLVER.md> --skills <path/to/skills/>
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HEADING_RE = re.compile(r"^##\s+(\S+)\s*(.*)$")


def _resolve_skill_dir(skill: str, skill_files: dict[str, Path], block: str) -> Path | None:
    """Resolve a heading skill name to its on-disk skill directory.

    We only score entries that explicitly point at a real `skills/<name>/SKILL.md`
    via the **File:** directive. We do NOT infer matches from a free-form prefix
    because RESOLVER.md mixes slash-commands, workflows, and skills, and prefix
    matching generates false positives (e.g. `auto` matches `autonomous-ai-agents`).
    """
    m = re.search(r"\*\*File:\*\*\s+`?skills/([^/`]+)/SKILL\.md`?", block)
    if m and m.group(1) in skill_files:
        return skill_files[m.group(1)]
    return None


def _classify_entry(skill: str, block: str, skills_dir: Path) -> str:
    """Classify a RESOLVER.md heading so we don't flag slash-commands and
    out-of-tree workflows as orphans. Returns 'skill' | 'slash' | 'workflow' | 'missing-file'."""
    if re.search(r"\*\*File:\*\*\s+`?skills/([^/`]+)/SKILL\.md`?", block):
        return "skill"
    if "slash command" in block.lower() or "`/" in block:
        return "slash"
    if "skills/workflow/" in block or "workflow" in block.lower():
        return "workflow"
    return "missing-file"


def audit(resolver: Path, skills_dir: Path) -> dict:
    if not resolver.is_file():
        return {"error": f"missing {resolver}"}
    text = resolver.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Build skill_dirs: name -> directory. We use lowercase basename for matching.
    skill_files: dict[str, Path] = {}
    for p in skills_dir.glob("*"):
        if p.is_dir():
            skill_files[p.name] = p

    headings = []
    heading_blocks: list[tuple[int, str, str]] = []  # (idx, full block, line)
    for i, line in enumerate(lines):
        m = HEADING_RE.match(line)
        if m:
            headings.append({"skill": m.group(1), "rest": m.group(2), "line": line})
            heading_blocks.append((i, "\n".join(lines[i:i + 4]), line))

    # group by skill (dup-key detection)
    by_skill: dict[str, list[dict]] = {}
    for h in headings:
        by_skill.setdefault(h["skill"], []).append(h)

    orphans = []
    dups = []
    ambiguous = []
    valid = []

    for skill, rows in by_skill.items():
        # use the first heading's block to look for **File:** directive
        block = next((b for (idx, b, l) in heading_blocks if l == rows[0]["line"]), "")
        kind = _classify_entry(skill, block, skills_dir)
        if kind == "missing-file":
            orphans.append({"skill": skill, "reason": "no-SKILL-dir-and-no-File-directive"})
            continue
        if kind in ("slash", "workflow"):
            # not a top-level skill entry — don't classify as skill, but report for awareness
            valid.append(skill)
            continue
        target = _resolve_skill_dir(skill, skill_files, block)
        if target is None:
            orphans.append({"skill": skill, "reason": "no-SKILL-dir"})
            continue
        if len(rows) > 1:
            dups.append({"skill": skill, "count": len(rows)})
            continue
        # heading or its sub-line must have triggers
        idx = lines.index(rows[0]["line"])
        # look ahead up to 4 lines for the Triggers directive
        lookahead = "\n".join(lines[idx + 1:idx + 5])
        has_online = "," in rows[0]["line"]
        has_subline = "Triggers:" in lookahead and "," in lookahead
        if not (has_online or has_subline):
            ambiguous.append({"skill": skill, "reason": "no-triggers-anywhere"})
            continue
        valid.append(skill)

    return {
        "resolver": str(resolver),
        "headings_total": len(headings),
        "valid": len(valid),
        "orphans": orphans,
        "dups": dups,
        "ambiguous": ambiguous,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Skillify check-resolvable structural pass.")
    ap.add_argument("--repo", type=Path, default=None, help="repo root (overrides --resolver/--skills)")
    ap.add_argument("--resolver", type=Path, default=None)
    ap.add_argument("--skills", type=Path, default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 on any orphan / dup / ambiguous (default: exit 0 if dups=0 and ambiguous=0; "
                         "orphans are reported but tolerated)")
    args = ap.parse_args()

    if args.repo is not None:
        repo = args.repo
        resolver = repo / "skills" / "RESOLVER.md"
        skills_dir = repo / "skills"
    else:
        if args.resolver is None or args.skills is None:
            ap.error("either --repo or both --resolver and --skills are required")
        resolver = args.resolver
        skills_dir = args.skills

    result = audit(resolver, skills_dir)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"check-resolvable: headings={result['headings_total']} "
              f"valid={result['valid']} orphans={len(result['orphans'])} "
              f"dups={len(result['dups'])} ambiguous={len(result['ambiguous'])}")
        for o in result["orphans"]:
            print(f"  ORPHAN: {o}")
        for d in result["dups"]:
            print(f"  DUP:    {d}")
        for a in result["ambiguous"]:
            print(f"  AMBIG:  {a}")

    if result.get("error"):
        return 2
    if args.strict:
        if result["orphans"] or result["dups"] or result["ambiguous"]:
            return 1
        return 0
    # default: dups and ambiguous are real bugs; orphans can be existing drift
    if result["dups"] or result["ambiguous"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
