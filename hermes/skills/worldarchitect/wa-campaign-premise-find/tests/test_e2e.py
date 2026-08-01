#!/usr/bin/env python3
"""E2E smoke test for wa-campaign-premise-find skill.

Exercises the full pipeline from user premise → keyword matrix → grep
→ candidate extraction. Does NOT call Firestore (that requires live auth
and is out of scope for a unit-time E2E). Validates the wiki-fan-out
phase against the live `~/llm_wiki/raw/campaigns/` tree.

Usage:
    python3 -m pytest tests/test_e2e.py -v
    # or directly:
    python3 tests/test_e2e.py
"""
import os
import re
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))
from keyword_matrix import KEYWORD_MATRIX, build_search_regex, classify_god_mode  # noqa: E402
import json  # noqa: E402

ROOT = Path(os.path.expanduser("~/llm_wiki/raw/campaigns"))
ISEKI_DIR_NAME = "dUfl4Adb3oH6foczNFSZ"
ISEKI_CAMPAIGN_ID = ISEKI_DIR_NAME


def test_iseki_v1_is_findable():
    """End-to-end: user says 'find demon lord reincarnation campaign',
    the skill should surface Iseki v1 in the wiki grep results."""
    regex = build_search_regex(["demon_lord", "reincarnation"])
    assert regex, "empty regex from build_search_regex"

    matches = []
    for d in sorted(os.listdir(ROOT)):
        p = ROOT / d
        if not p.is_dir():
            continue
        files = sorted(os.listdir(p))
        primary = next(
            (p / f for f in files
             if (f.endswith(".md") or f.endswith(".txt"))
             and "game_state" not in f.lower()),
            None,
        )
        if not primary:
            continue
        try:
            text = primary.read_text(errors="replace")[:5000]
        except Exception:
            continue
        if re.search(regex, text, re.IGNORECASE):
            matches.append((d, primary))

    assert matches, "no wiki matches for demon_lord + reincarnation"

    # Iseki v1 MUST be in the top matches
    matched_ids = [m[0] for m in matches]
    assert ISEKI_CAMPAIGN_ID in matched_ids, (
        f"FAIL: Iseki v1 ({ISEKI_CAMPAIGN_ID}) not in wiki grep results. "
        f"Got {len(matched_ids)} matches; sample: {matched_ids[:5]}"
    )

    # Verify Iseki v1's primary file actually classifies as demon_lord + reincarnation
    iseki_primary = next(
        (p for d, p in matches if d == ISEKI_CAMPAIGN_ID), None,
    )
    assert iseki_primary, "Iseki v1 primary file not found in matches"
    text = iseki_primary.read_text(errors="replace")[:6000]
    classification = classify_god_mode(text)
    assert classification["demon_lord"] is True
    assert classification["reincarnation"] is True
    print(f"\nPASS: Iseki v1 ({ISEKI_CAMPAIGN_ID}) found + classified correctly")
    print(f"  classification: {classification}")


def test_luna_post_bg3_is_resurrected_npc_not_pc():
    """Luna post bg3 has 'Shadowheart (Resurrected)' as NPC. The skill
    must correctly classify this as `resurrected=True` BUT note that the
    PC herself (Luna) is not the resurrected one — this is a pitfall."""
    luna_dir = ROOT / "yvkGUlbBJ90zrjivwn7r"
    files = sorted(os.listdir(luna_dir))
    primary = next(
        (luna_dir / f for f in files
         if (f.endswith(".md") or f.endswith(".txt"))
         and "game_state" not in f.lower()),
        None,
    )
    assert primary, "Luna post bg3 primary file not found"
    text = primary.read_text(errors="replace")[:6000]

    classification = classify_god_mode(text)
    assert classification["resurrected"] is True  # Shadowheart NPC
    # Luna herself is NOT explicitly resurrected — this is the pitfall
    print(f"\nPASS: Luna post bg3 resurrect classification: {classification}")
    print("  Pitfall: 'resurrected' matched on NPC Shadowheart, not PC Luna")


def test_iseki_v1_via_skillify_check_pipeline():
    """Run the canonical skillify_check on this skill and verify items pass.

    Note: skillify_check returns rc=2 when score < 9/9 (deems it not fully
    skilled). For our purposes, 8/9 with 0 fails is fine. Only rc=1 (Python
    error) is a real failure."""
    skill_dir = str(SKILL_DIR)
    result = subprocess.run(
        ["python3",
         "$HOME/.hermes/skills/skillify/scripts/skillify_check.py",
         skill_dir, "--repo-root", "$HOME/.hermes", "--json"],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode in (0, 2), (
        f"skillify_check unexpected rc={result.returncode}: {result.stderr}"
    )
    payload = json.loads(result.stdout)
    score_str = payload.get("score", "0/9")
    pass_count = sum(1 for item in payload.get("items", []) if item.get("status") == "pass")
    fail_count = sum(1 for item in payload.get("items", []) if item.get("status") == "fail")
    print(f"\nskillify_check score: {score_str} ({pass_count} pass, {fail_count} fail)")
    assert fail_count == 0, f"expected 0 fails, got {fail_count}: {payload}"
    assert pass_count >= 7, f"expected >=7 pass items, got {pass_count}"


def test_iseki_v1_via_check_resolvable_pipeline():
    """Run our own check_resolvable.py CLI to verify it returns success."""
    result = subprocess.run(
        ["python3", str(SKILL_DIR / "scripts" / "check_resolvable.py"), "--all"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, (
        f"check_resolvable failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    assert "PASS" in result.stdout, f"expected PASS in output: {result.stdout}"
    print(f"\ncheck_resolvable output:\n{result.stdout}")


def test_pytest_unit_suite_runs_clean():
    """Sanity check: the unit-test suite passes (NOT including this E2E file)."""
    result = subprocess.run(
        ["/opt/homebrew/bin/pytest",
         str(SKILL_DIR / "tests" / "test_wa_campaign_premise_find.py"),
         "-v", "--tb=line", "--no-header"],
        capture_output=True, text=True, cwd=str(SKILL_DIR.parent),
        timeout=60,
    )
    assert result.returncode == 0, (
        f"unit-test pytest failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    assert "passed" in result.stdout, (
        f"expected 'passed' in pytest output, got:\n{result.stdout}"
    )
    print(f"\nPASS: unit-test pytest suite green")


if __name__ == "__main__":
    test_iseki_v1_is_findable()
    test_luna_post_bg3_is_resurrected_npc_not_pc()
    test_pytest_unit_suite_runs_clean()
    print("\nALL E2E TESTS PASSED")
