"""test_skillify_check.py — integration tests for skillify_check.py.

Layer-2 tests: invoke the shipped script against the live skill tree,
assert the report shape and per-item status. No mocks at the boundary.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "skillify_check.py"
SKILL_DIR = REPO_ROOT / "skills" / "skillify"


def run_skillify_check(extra_args=None):
    args = [sys.executable, str(SCRIPT), str(SKILL_DIR), "--json"]
    if extra_args:
        args.extend(extra_args)
    p = subprocess.run(args, capture_output=True, text=True, check=False)
    if p.returncode not in (0, 1, 2):
        raise RuntimeError(
            f"skillify_check failed: rc={p.returncode} stderr={p.stderr!r}"
        )
    return p


def test_skillify_check_returns_parseable_json():
    p = run_skillify_check()
    assert p.returncode in (0, 2), f"expected pass or defer-warn, got {p.returncode}"
    report = json.loads(p.stdout)
    assert "items" in report
    assert len(report["items"]) == 11
    assert report["skill"] == "skillify"


def test_items_required_present():
    p = run_skillify_check()
    report = json.loads(p.stdout)
    by_n = {i["n"]: i for i in report["items"]}
    # always-required items must not be FAIL
    for n in (1, 2, 4, 5, 7, 8, 9, 10):
        assert by_n[n]["status"] in ("pass", "defer", "na"), \
            f"item {n} unexpectedly failed: {by_n[n]}"


def test_cross_modal_eval_deferred_with_rationale():
    p = run_skillify_check()
    report = json.loads(p.stdout)
    by_n = {i["n"]: i for i in report["items"]}
    assert by_n[3]["status"] == "defer"
    assert "port-rationale" in by_n[3]["evidence"] or "references" in by_n[3]["evidence"]


def test_brain_filing_rationale_present():
    """Brain-filing item must be either N/A (skill doesn't write brain pages)
    or PASS (skill describes its filing rule). The truthful contract says
    the audit script cannot lie about what the SKILL.md claims — if the
    SKILL.md mentions brain filing under any heading, the audit calls it
    'pass', otherwise 'na'. Either answer is acceptable; the contract is
    'no FAIL'."""
    p = run_skillify_check()
    report = json.loads(p.stdout)
    by_n = {i["n"]: i for i in report["items"]}
    assert by_n[11]["status"] in ("na", "pass"), \
        f"brain-filing should be na or pass, got {by_n[11]}"


def test_lying_skill_fails_audit(tmp_path: Path):
    """Adversarial: a fixture skill that claims to have tests but doesn't."""
    fixture = tmp_path / "lying"
    (fixture / "scripts").mkdir(parents=True)
    (fixture / "scripts" / "noop.py").write_text("# noop\n")
    (fixture / "tests").mkdir()
    # explicitly do NOT create any test_*.py
    (fixture / "SKILL.md").write_text(
        "---\nname: lying\ndescription: x\n---\n## Contract\nx\n## Phases\nx\n## Output Format\nx\n"
    )
    args = [sys.executable, str(SCRIPT), str(fixture), "--json",
            "--repo-root", str(REPO_ROOT)]
    p = subprocess.run(args, capture_output=True, text=True, check=False)
    report = json.loads(p.stdout)
    by_n = {i["n"]: i for i in report["items"]}
    assert by_n[4]["status"] == "fail", f"item 4 should fail: {by_n[4]}"
    assert report["fail"] >= 1
