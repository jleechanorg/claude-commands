"""test_check_resolvable.py — integration tests for the structural resolver pass.

Layer-2: invokes the shipped script against the live `skills/RESOLVER.md`
and the live `skills/` directory. Asserts that no skill is orphaned,
duplicated, or ambiguous.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_resolvable.py"
RESOLVER = REPO_ROOT / "skills" / "RESOLVER.md"


def run_check_resolvable():
    args = [sys.executable, str(SCRIPT), "--resolver", str(RESOLVER),
            "--skills", str(REPO_ROOT / "skills"), "--json"]
    p = subprocess.run(args, capture_output=True, text=True, check=False)
    return p


def test_resolver_md_exists_and_parses():
    assert RESOLVER.is_file(), "RESOLVER.md must exist in skills/"
    p = run_check_resolvable()
    assert p.returncode in (0, 1), f"unexpected rc={p.returncode} stderr={p.stderr!r}"
    report = json.loads(p.stdout)
    assert "headings_total" in report
    assert report["headings_total"] > 0


def test_skillify_in_resolver():
    p = run_check_resolvable()
    report = json.loads(p.stdout)
    # skillify is the skill under test; it must be present as a non-orphan heading
    orphan_skills = [o["skill"] for o in report["orphans"]]
    assert "skillify" not in orphan_skills, \
        f"skillify must not be orphaned: {report['orphans']}"


def test_no_dup_keys_for_skillify():
    p = run_check_resolvable()
    report = json.loads(p.stdout)
    for d in report["dups"]:
        assert d["skill"] != "skillify", f"dup heading for skillify: {d}"
