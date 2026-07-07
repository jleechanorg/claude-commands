#!/usr/bin/env python3
"""trigger_eval.py — semantic pass on the routing-eval.jsonl fixture.

Reads each row of the fixture (`{intent, expected_skill, ambiguous_with?}`)
and verifies:
  - the skill referenced in `expected_skill` actually has a SKILL.md, AND
  - the resolver contains a heading for that skill.

In `--llm` mode (optional), ambiguous routes (`ambiguous_with` populated)
are passed through a frontier model for tie-break. Off by default — Hermes
uses `advice` for that.

Usage:
    python3 -m trigger_eval --fixture <fixture.jsonl> [--llm]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_resolver_skills(resolver: Path) -> set[str]:
    if not resolver.is_file():
        return set()
    skills = set()
    for line in resolver.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            skill = line[3:].split()[0]
            skills.add(skill)
    return skills


def llm_tie_break(intent: str, candidates: list[str]) -> str:
    """Optional LLM tie-break. Off by default. If enabled, calls Claude (cheap)."""
    try:
        from anthropic import Anthropic  # type: ignore
    except ImportError:
        return candidates[0] if candidates else ""
    client = Anthropic()
    prompt = (
        f"User intent: {intent!r}\n"
        f"Candidates: {candidates!r}\n"
        "Pick the one skill that best matches the intent. Reply with only the skill name."
    )
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=64,
        messages=[{"role": "user", "content": prompt}],
    )
    return (msg.content[0].text or "").strip()


def run(fixture: Path, repo_root: Path, use_llm: bool) -> dict:
    if not fixture.is_file():
        return {"error": f"missing {fixture}"}
    resolver = repo_root / "skills" / "RESOLVER.md"
    available_skills = parse_resolver_skills(resolver)
    skills_dir = repo_root / "skills"

    rows = []
    for ln in fixture.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        rows.append(json.loads(ln))

    results = []
    ambiguous_hits = 0
    for row in rows:
        intent = row.get("intent", "")
        expected = row.get("expected_skill", "")
        ambig = row.get("ambiguous_with") or []

        # the expected_skill must be on the resolver
        if expected not in available_skills:
            results.append({"intent": intent, "status": "missing-from-resolver", "expected": expected})
            continue

        # the SKILL.md must exist
        sk = skills_dir / expected / "SKILL.md"
        if not sk.is_file():
            results.append({"intent": intent, "status": "no-SKILL.md", "expected": expected})
            continue

        if ambig:
            ambiguous_hits += 1
            if use_llm:
                pick = llm_tie_break(intent, [expected] + ambig)
                results.append({"intent": intent, "status": f"llm-tie:{pick}", "expected": expected})
                continue

        results.append({"intent": intent, "status": "ok", "expected": expected})

    passed = sum(1 for r in results if r["status"] in ("ok",) or r["status"].startswith("llm-tie"))
    return {
        "total": len(results),
        "passed": passed,
        "ambiguous_rows": ambiguous_hits,
        "results": results,
        "use_llm": use_llm,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Skillify trigger_eval (semantic).")
    ap.add_argument("--fixture", type=Path, required=True)
    ap.add_argument("--repo-root", type=Path, default=None,
                    help="root of the repo (default: 3 parents up from --fixture)")
    ap.add_argument("--llm", action="store_true")
    args = ap.parse_args()

    if not args.fixture.is_file():
        sys.exit(f"error: missing fixture {args.fixture}")
    repo_root = args.repo_root or args.fixture.parents[2]
    if not repo_root.is_dir():
        sys.exit(f"error: repo_root {repo_root} is not a directory")

    result = run(args.fixture, repo_root, args.llm)

    print(json.dumps(result, indent=2))
    if result.get("error"):
        return 2
    if result["passed"] != result["total"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
