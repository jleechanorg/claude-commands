"""Command-line contract tests for the fail-closed convergence CLI."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "beads-converge"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        (sys.executable, str(SCRIPT), *args),
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def all_hash_args() -> tuple[str, ...]:
    return (
        "--registry",
        "/tmp/registry.json",
        "--expected-registry-sha256",
        "a" * 64,
        "--manifest",
        "/tmp/manifest.json",
        "--expected-manifest-sha256",
        "b" * 64,
        "--expected-plan-sha256",
        "c" * 64,
        "--expected-canonical",
        "/tmp/repo/.beads",
        "--expected-adapter",
        "br-sqlite-v1",
        "--expected-tracker-path",
        "/tmp/br",
        "--expected-tracker-version",
        "0.4.0",
        "--expected-tracker-sha256",
        "d" * 64,
        "--expected-git-path",
        "/usr/bin/git",
        "--expected-git-version",
        "2.0",
        "--expected-git-sha256",
        "e" * 64,
        "--approval",
        "/tmp/approval.json",
        "--approval-signature",
        "/tmp/approval.sig",
    )


class CliContractTest(unittest.TestCase):
    def test_plan_all_parser_has_no_apply_flag(self) -> None:
        result = run_cli(
            "plan-all",
            "--registry",
            "/tmp/registry.json",
            "--expected-registry-sha256",
            "a" * 64,
            "--apply",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--apply", result.stderr)

    def test_apply_requires_one_repo_and_literal_apply(self) -> None:
        result = run_cli("apply", "--repo", "repo-a", *all_hash_args())
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--apply", result.stderr)

    def test_recover_requires_literal_recover(self) -> None:
        result = run_cli(
            "recover",
            "--repo",
            "repo-a",
            "--run-id",
            "run-1",
            *all_hash_args(),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--recover", result.stderr)

    def test_apply_requires_every_operator_binding(self) -> None:
        result = run_cli("apply", "--repo", "repo-a", "--apply")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--registry", result.stderr)
        self.assertIn("--expected-registry-sha256", result.stderr)

    def test_unknown_command_is_rejected(self) -> None:
        result = run_cli("apply-all")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid choice", result.stderr)

    def test_no_authority_bypass_or_test_switches_are_exposed(self) -> None:
        result = run_cli("--help")
        self.assertEqual(result.returncode, 0)
        for forbidden in ("apply-all", "--bypass", "--test-authority", "--approve"):
            self.assertNotIn(forbidden, result.stdout)

    def test_failures_have_json_stdout_and_diagnostics_stderr(self) -> None:
        result = run_cli(
            "registry",
            "validate",
            "--registry",
            "/tmp/does-not-exist.json",
            "--expected-registry-sha256",
            "a" * 64,
        )
        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertTrue(result.stderr.startswith("beads-converge:"))

    def test_apply_without_approval_files_fails_before_mutation(self) -> None:
        result = run_cli("apply", "--repo", "repo-a", *all_hash_args(), "--apply")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("registry", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
