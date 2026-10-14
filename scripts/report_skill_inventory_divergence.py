#!/usr/bin/env python3
"""Report divergence between a portable bundle set and the .claude/skills source.

The 2026-10-13 consolidation audit found that portable/skills/** was NOT a duplicate of
.claude/skills/** : most entries diverged and several existed only in the portable set.
Any plan that assumes "portable == duplicate" is wrong; run this first.

Usage: python3 scripts/report_skill_inventory_divergence.py [--json]
Exit code 0 always (report only); the contract test pins the current counts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "portable" / "manifest.json"


def digest(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def report() -> dict:
    if not MANIFEST.exists():
        return {"status": "no-portable-manifest"}
    names = json.loads(MANIFEST.read_text())["skills"]
    missing, identical, differing = [], [], []
    for name in names:
        src = ROOT / "portable" / "skills" / name / "SKILL.md"
        snap = ROOT / ".claude" / "skills" / name / "SKILL.md"
        if not snap.exists():
            missing.append(name)
        elif not src.exists() or digest(src) != digest(snap):
            differing.append(name)
        else:
            identical.append(name)
    return {
        "status": "ok",
        "portable_skills": len(names),
        "missing_in_claude_skills": sorted(missing),
        "identical_bodies": sorted(identical),
        "differing_bodies": sorted(differing),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    r = report()
    if a.json:
        print(json.dumps(r, indent=2))
        return 0
    if r["status"] != "ok":
        print(f"portable manifest absent ({r['status']}) - nothing to reconcile")
        return 0
    print(f"portable skills: {r['portable_skills']}")
    print(f"  MISSING from .claude/skills ({len(r['missing_in_claude_skills'])}): {r['missing_in_claude_skills']}")
    print(f"  IDENTICAL bodies            ({len(r['identical_bodies'])}): {r['identical_bodies']}")
    print(f"  DIFFERING bodies            ({len(r['differing_bodies'])}): {r['differing_bodies']}")
    print("\n=> portable/** is a DIVERGENT VARIANT SET, not a duplicate. Reconcile before collapsing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
