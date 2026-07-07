"""test_trigger_eval.py — integration tests for the routing-eval fixture.

Layer-2: runs trigger_eval.py against the live routing-eval.jsonl and the
live RESOLVER.md + skills/ tree. The fixture is the single source of
truth, so the test iterates the fixture rather than a hardcoded list.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "trigger_eval.py"
FIXTURE = REPO_ROOT / "skills" / "skillify" / "routing-eval.jsonl"


def run_trigger_eval(llm=False):
    args = [sys.executable, str(SCRIPT), "--fixture", str(FIXTURE),
            "--repo-root", str(REPO_ROOT)]
    if llm:
        args.append("--llm")
    p = subprocess.run(args, capture_output=True, text=True, check=False)
    return p


def test_fixture_exists_and_is_valid_jsonl():
    assert FIXTURE.is_file(), "routing-eval.jsonl must exist"
    rows = []
    for ln in FIXTURE.read_text().splitlines():
        ln = ln.strip()
        if not ln:
            continue
        row = json.loads(ln)
        assert "intent" in row and "expected_skill" in row, \
            f"row missing required fields: {list(row)}"
        rows.append(row)
    assert len(rows) >= 6, f"need at least 6 intents, got {len(rows)}"


def test_trigger_eval_resolves_every_intent():
    p = run_trigger_eval()
    assert p.returncode == 0, f"trigger_eval rc={p.returncode}\nstdout={p.stdout}\nstderr={p.stderr}"
    report = json.loads(p.stdout)
    assert report["passed"] == report["total"], \
        f"{report['passed']}/{report['total']} resolved — see {report['results']}"


def test_ambiguous_row_handled_without_llm():
    """The fixture includes one row with ambiguous_with; without --llm, we
    still expect a non-failure (skipped-LLM is acceptable)."""
    p = run_trigger_eval(llm=False)
    report = json.loads(p.stdout)
    if report["ambiguous_rows"] > 0:
        # ok — handler accepts ambiguous_without_llm
        assert report["passed"] >= report["total"] - report["ambiguous_rows"], \
            "ambiguous rows should still resolve via expected_skill when --llm is off"
