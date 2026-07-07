"""Tests for post_approved.py — must hard-block without the POST APPROVED token."""
import sys
import subprocess
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
POSTER = SKILL_DIR / "scripts" / "post_approved.py"


def test_no_token_blocks():
    """No --approval-token flag → exit code 2 with BLOCKED message."""
    r = subprocess.run(
        ["python3", str(POSTER), "--drafts", "/tmp/nonexistent_drafts/"],
        capture_output=True, text=True, timeout=15,
    )
    assert r.returncode == 2, f"expected exit 2, got {r.returncode}\nstdout: {r.stdout}\nstderr: {r.stderr}"
    assert "BLOCKED" in r.stdout
    assert "POST APPROVED" in r.stdout


def test_wrong_token_blocks():
    """Wrong token → exit code 2."""
    r = subprocess.run(
        ["python3", str(POSTER), "--drafts", "/tmp/nonexistent_drafts/",
         "--approval-token", "ship it"],
        capture_output=True, text=True, timeout=15,
    )
    assert r.returncode == 2, f"expected exit 2, got {r.returncode}"
    assert "BLOCKED" in r.stdout


def test_correct_token_passes_gate_but_fails_on_missing_drafts():
    """Correct token → exit code 1 (drafts missing), NOT 2 (gate passed)."""
    r = subprocess.run(
        ["python3", str(POSTER), "--drafts", "/tmp/nonexistent_drafts/",
         "--approval-token", "POST APPROVED"],
        capture_output=True, text=True, timeout=15,
    )
    assert r.returncode != 2, f"gate failed despite correct token — exit {r.returncode}"
    # Expect 1 because drafts dir is missing
    assert r.returncode == 1, f"expected 1 (missing drafts), got {r.returncode}\nstdout: {r.stdout}\nstderr: {r.stderr}"


def test_correct_token_with_platforms_passes_gate():
    """Correct token + platforms → exit code 1 (missing drafts), NOT 2."""
    r = subprocess.run(
        ["python3", str(POSTER), "--drafts", "/tmp/nonexistent_drafts/",
         "--approval-token", "POST APPROVED", "--platforms", "linkedin,hackernews"],
        capture_output=True, text=True, timeout=15,
    )
    assert r.returncode != 2, f"gate failed despite correct token — exit {r.returncode}"
    assert "BLOCKED" not in r.stdout


def test_case_insensitive_token():
    """Token is case-insensitive (POST APPROVED, post approved, etc.)."""
    r = subprocess.run(
        ["python3", str(POSTER), "--drafts", "/tmp/nonexistent_drafts/",
         "--approval-token", "post approved"],
        capture_output=True, text=True, timeout=15,
    )
    assert r.returncode != 2, f"case-insensitive token should pass gate, got {r.returncode}"
    assert "BLOCKED" not in r.stdout


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))