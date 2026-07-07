#!/usr/bin/env python3
"""skillify_check.py — the deterministic 11-item audit.

Walks a skill directory and reports which of the 11 contract items are
present, missing, or deferred. Used as Layer-2 evidence for /er.

Usage:
    python3 -m skillify_check <skill_dir> [--json]

Exit codes:
    0  all applicable items pass
    1  one or more required items fail
    2  one or more items are deferred (warns but does not fail)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ITEM_NAMES = {
    1: "SKILL.md",
    2: "deterministic_code",
    3: "cross_modal_eval",
    4: "unit_tests",
    5: "integration_tests",
    6: "llm_evals",
    7: "resolver_trigger_entry",
    8: "resolver_trigger_eval",
    9: "check_resolvable",
    10: "e2e_test",
    11: "brain_filing",
}

ALWAYS_REQUIRED = {1, 2, 4, 5, 7, 8, 9, 10}
CONDITIONAL = {3, 6, 11}  # 3=frontier eval, 6=LLM-calls, 11=writes-to-brain


def check_item_1(skill_dir: Path) -> tuple[str, str]:
    """SKILL.md exists, valid YAML frontmatter, has Contract + Phases + Output Format."""
    p = skill_dir / "SKILL.md"
    if not p.is_file():
        return ("fail", "missing")
    text = p.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return ("fail", "missing-YAML-frontmatter")
    try:
        end = text.index("\n---", 4)
    except ValueError:
        return ("fail", "missing-YAML-close")
    frontmatter = text[4:end]
    needed = ("name", "description")
    for f in needed:
        if f"{f}:" not in frontmatter:
            return ("fail", f"missing-frontmatter-{f}")
    for section in ("## Contract", "## Phases", "## Output Format"):
        if section not in text:
            return ("fail", f"missing-section-{section}")
    return ("pass", "present")


def check_item_2(skill_dir: Path) -> tuple[str, str]:
    """Deterministic code: scripts/ exists with at least one .py."""
    scripts = skill_dir / "scripts"
    if not scripts.is_dir():
        return ("fail", "missing-scripts-dir")
    py_files = list(scripts.glob("*.py"))
    if not py_files:
        return ("fail", "no-python-scripts")
    return ("pass", f"{len(py_files)}-scripts")


def check_item_3(skill_dir: Path) -> tuple[str, str]:
    """Cross-modal eval: 3 frontier models from 3 providers; receipts.
    DEFERRED in Hermes — no sub-script."""
    ref = skill_dir / "references" / "gbrain-skillify-v1.1.0-port.md"
    if ref.is_file():
        return ("defer", "documented-in-references-port")
    return ("defer", "no-port-rationale")


def check_item_4(skill_dir: Path) -> tuple[str, str]:
    """Unit tests: tests/ exists with at least one test_*.py (excludes __init__.py)."""
    tests = skill_dir / "tests"
    if not tests.is_dir():
        return ("fail", "missing-tests-dir")
    py_tests = [p for p in tests.glob("test_*.py") if p.name != "__init__.py"]
    if not py_tests:
        return ("fail", "no-test_-py")
    return ("pass", f"{len(py_tests)}-test_-py")


def check_item_5(skill_dir: Path) -> tuple[str, str]:
    """Integration tests: same dir as unit, but the test must actually invoke the
    shipped script on the live tree — we grep for the script name in test bodies."""
    tests = skill_dir / "tests"
    if not tests.is_dir():
        return ("fail", "missing-tests-dir")
    scripts = skill_dir / "scripts"
    py_scripts = [p.stem for p in scripts.glob("*.py")] if scripts.is_dir() else []
    live_call_count = 0
    for t in tests.glob("test_*.py"):
        body = t.read_text(encoding="utf-8")
        for s in py_scripts:
            if s in body:  # the test references the script by name
                live_call_count += 1
                break
    if live_call_count == 0:
        return ("fail", "no-live-script-call")
    return ("pass", f"{live_call_count}-scripts-referenced-in-tests")


def check_item_6(skill_dir: Path) -> tuple[str, str]:
    """LLM evals: evals/{rubric.json, cases.jsonl, run_eval.py} all present."""
    evals = skill_dir / "evals"
    if not evals.is_dir():
        return ("na", "no-evals-dir-not-required")
    needed = ["rubric.json", "cases.jsonl", "run_eval.py"]
    missing = [n for n in needed if not (evals / n).is_file()]
    if missing:
        return ("fail", f"missing-{missing}")
    return ("pass", "all-evals-artifacts")


def check_item_7(skill_dir: Path, repo_root: Path) -> tuple[str, str]:
    """Resolver trigger entry: a row in skills/RESOLVER.md for this skill.

    Triggers must appear on the heading line of the section so the
    test_resolver_trigger regex matches (gbrain pitfall)."""
    resolver = repo_root / "skills" / "RESOLVER.md"
    if not resolver.is_file():
        return ("fail", "missing-RESOLVER.md")
    text = resolver.read_text(encoding="utf-8")
    name = skill_dir.name
    # find ## <name> heading and check if Triggers appear on the SAME line
    heading_marker = f"## {name} "
    if heading_marker not in text and f"## {name}\n" not in text:
        # try the pointer alias
        if name == "skillify":
            heading_marker = "## skillify "
            if heading_marker not in text and "## skillify\n" not in text:
                return ("fail", f"no-##-{name}-heading-in-RESOLVER.md")
        else:
            return ("fail", f"no-##-{name}-heading-in-RESOLVER.md")
    # find the line
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith(f"## {name}") and line != f"## {name}":
            # triggers ARE on the heading line — verify there is at least one comma
            if "," in line:
                return ("pass", "triggers-on-heading-line")
            break
    return ("fail", "triggers-not-on-heading-line")


def check_item_8(skill_dir: Path) -> tuple[str, str]:
    """Resolver trigger eval: routing-eval.jsonl + test_trigger_eval.py exist
    AND the fixture uses {intent, expected_skill, ambiguous_with?} schema."""
    fixture = skill_dir / "routing-eval.jsonl"
    test = skill_dir / "tests" / "test_trigger_eval.py"
    if not fixture.is_file():
        return ("fail", "missing-routing-eval.jsonl")
    if not test.is_file():
        return ("fail", "missing-test_trigger_eval.py")
    bad_rows = []
    intent_count = 0
    for ln in fixture.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            import json as _json
            row = _json.loads(ln)
        except Exception as e:
            bad_rows.append(f"json-err:{e}")
            continue
        if "intent" not in row or "expected_skill" not in row:
            bad_rows.append(f"missing-fields:{list(row)}")
            continue
        intent_count += 1
    if bad_rows:
        return ("fail", f"{len(bad_rows)}-bad-rows")
    if intent_count == 0:
        return ("fail", "zero-intents")
    return ("pass", f"{intent_count}-intents")


def check_item_9(skill_dir: Path, repo_root: Path) -> tuple[str, str]:
    """check-resolvable: scripts/check_resolvable.py exists, exposes a CLI,
    and reads the LIVE RESOLVER.md (not a string fixture)."""
    scripts = skill_dir / "scripts"
    cr = scripts / "check_resolvable.py"
    if not cr.is_file():
        return ("fail", "missing-check_resolvable.py")
    body = cr.read_text(encoding="utf-8")
    if "RESOLVER.md" not in body:
        return ("fail", "check_resolvable-does-not-reference-RESOLVER.md")
    if "argparse" not in body and "ArgumentParser" not in body:
        return ("fail", "no-CLI-surface")
    return ("pass", "present-with-CLI")


def check_item_10(skill_dir: Path) -> tuple[str, str]:
    """E2E smoke test: tests/test_e2e.py exists AND exercises a full pipeline."""
    e = skill_dir / "tests" / "test_e2e.py"
    if not e.is_file():
        return ("fail", "missing-test_e2e.py")
    body = e.read_text(encoding="utf-8")
    # E2E must reference at least 2 of: skillify_check, check_resolvable, trigger_eval
    refs = sum(1 for v in ("skillify_check", "check_resolvable", "trigger_eval") if v in body)
    if refs < 2:
        return ("fail", f"only-{refs}-stage-references")
    return ("pass", f"{refs}-stages")


def check_item_11(skill_dir: Path) -> tuple[str, str]:
    """Brain filing (conditional). Default N/A unless the SKILL.md describes
    that the skill writes to brain pages via a `## Brain Filing` or
    `## Brain RESOLVER` section with explicit filing semantics."""
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8") if (skill_dir / "SKILL.md").exists() else ""
    lower = text.lower()
    has_section = (
        "## brain filing" in lower
        or ("brain filing" in lower and ("this skill" in lower or "the skill writes" in lower))
    )
    if not has_section:
        return ("na", "skill-does-not-write-brain-pages")
    if any(needle in lower for needle in ("writes to", "register", "filing rule", "add an entry to")):
        return ("pass", "filing-rule-described")
    return ("fail", "claims-brain-filing-but-no-rule")


def audit(skill_dir: Path, repo_root: Path) -> dict:
    skill_dir = skill_dir.resolve()
    repo_root = repo_root.resolve()
    items = []
    for n in range(1, 12):
        name = ITEM_NAMES[n]
        if n == 1:
            status, evidence = check_item_1(skill_dir)
        elif n == 2:
            status, evidence = check_item_2(skill_dir)
        elif n == 3:
            status, evidence = check_item_3(skill_dir)
        elif n == 4:
            status, evidence = check_item_4(skill_dir)
        elif n == 5:
            status, evidence = check_item_5(skill_dir)
        elif n == 6:
            status, evidence = check_item_6(skill_dir)
        elif n == 7:
            status, evidence = check_item_7(skill_dir, repo_root)
        elif n == 8:
            status, evidence = check_item_8(skill_dir)
        elif n == 9:
            status, evidence = check_item_9(skill_dir, repo_root)
        elif n == 10:
            status, evidence = check_item_10(skill_dir)
        elif n == 11:
            status, evidence = check_item_11(skill_dir)
        items.append({"n": n, "name": name, "status": status, "evidence": evidence})

    passes = sum(1 for i in items if i["status"] == "pass")
    fails = sum(1 for i in items if i["status"] == "fail")
    defers = sum(1 for i in items if i["status"] == "defer")
    nas = sum(1 for i in items if i["status"] == "na")
    total_applicable = 11 - nas
    return {
        "skill": skill_dir.name,
        "items": items,
        "score": f"{passes}/{total_applicable}",
        "pass": passes,
        "fail": fails,
        "defer": defers,
        "na": nas,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Skillify 11-item audit.")
    ap.add_argument("skill_dir", type=Path)
    ap.add_argument("--repo-root", type=Path, default=None,
                    help="root of the repo (default: parent of skill_dir)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not args.skill_dir.is_dir():
        sys.exit(f"error: {args.skill_dir} is not a directory")
    repo_root = args.repo_root or args.skill_dir.parent.parent
    if not repo_root.is_dir():
        sys.exit(f"error: repo_root {repo_root} is not a directory")

    report = audit(args.skill_dir, repo_root)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Skillify audit: {report['skill']}  score={report['score']} "
              f"defer={report['defer']} na={report['na']} fail={report['fail']}")
        for i in report["items"]:
            tag = {"pass": "OK", "fail": "MISS", "defer": "DEFER", "na": "N/A",
                   "partial": "PART"}[i["status"]]
            print(f"  [{tag}] {i['n']:>2}. {i['name']:<26}  {i['evidence']}")

    # exit: 0 if no fail, 2 if any defer (warn), 1 if any fail
    if report["fail"] > 0:
        return 1
    if report["defer"] > 0:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
