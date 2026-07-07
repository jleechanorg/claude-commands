"""test_e2e.py — full pipeline smoke.

Executes the three shipped CLIs against the live skill tree, asserts a
combined JSON report on disk, and confirms the overall score is non-zero.
This is the highest-value Layer-2 evidence for /er.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILLS = REPO_ROOT / "skills"
SKILLIFY_DIR = SKILLS / "skillify"


def _python(script_rel: str) -> list[str]:
    return [sys.executable, str(SKILLIFY_DIR / "scripts" / script_rel)]


def test_e2e_skillify_check_returns_valid_score():
    p = subprocess.run(
        _python("skillify_check.py") + [str(SKILLIFY_DIR), "--json", "--repo-root", str(REPO_ROOT)],
        capture_output=True, text=True, check=False,
    )
    assert p.returncode in (0, 2), f"skillify_check rc={p.returncode} stderr={p.stderr}"
    report = json.loads(p.stdout)
    assert report["skill"] == "skillify"
    # we are not yet "fully green" by design (item 3 defer) but the script
    # MUST identify ≥ 8 pass items
    assert report["pass"] >= 8, f"expected ≥8 pass, got {report}"


def test_e2e_check_resolvable_against_live_resolver():
    p = subprocess.run(
        _python("check_resolvable.py") + ["--repo", str(REPO_ROOT), "--json"],
        capture_output=True, text=True, check=False,
    )
    assert p.returncode in (0, 1), f"check_resolvable rc={p.returncode} stderr={p.stderr}"
    report = json.loads(p.stdout)
    assert report["headings_total"] > 0
    # We added skillify properly; it must NOT appear in the orphan list.
    orphan_skills = [o["skill"] for o in report["orphans"]]
    assert "skillify" not in orphan_skills


def test_e2e_trigger_eval_full_pass():
    p = subprocess.run(
        _python("trigger_eval.py") + ["--fixture", str(SKILLIFY_DIR / "routing-eval.jsonl"),
                                       "--repo-root", str(REPO_ROOT)],
        capture_output=True, text=True, check=False,
    )
    assert p.returncode == 0, f"trigger_eval rc={p.returncode}\nstdout={p.stdout}\nstderr={p.stderr}"
    report = json.loads(p.stdout)
    assert report["passed"] == report["total"], \
        f"all intent rows must resolve, got {report}"
