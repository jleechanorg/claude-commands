"""Command-line contract tests for the fail-closed convergence CLI."""

from __future__ import annotations

import io
import json
import subprocess
import sys
import unittest
from contextlib import redirect_stderr
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from scripts.beads_convergence import cli
from scripts.beads_convergence.approval import SignedApproval, envelope_bytes
from scripts.beads_convergence.codec import canonical_json_bytes, sha256_hex
from scripts.beads_convergence.transaction import TransactionCrash, apply_plan

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

    def test_recovery_delegates_full_authorization_and_reports_rolled_back(self) -> None:
        """A fixture recovery uses the current Task 5 request contract."""

        from tests.test_beads_convergence_transaction import (
            make_recovery_request,
            make_request,
        )
        self._run_fixture_recovery(make_request, make_recovery_request)

    def _run_fixture_recovery(self, make_request, make_recovery_request) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request = make_request(root)
            crashed = replace(request, fault_at="after-rename")
            with self.assertRaises(TransactionCrash):
                apply_plan(crashed)
            recovery = make_recovery_request(request)
            assert recovery.approval is not None
            recovery = replace(
                recovery,
                approval=SignedApproval(
                    replace(
                        recovery.approval.envelope,
                        expires_at="2099-01-01T00:00:00Z",
                    ),
                    recovery.approval.signature,
                ),
            )
            registry_raw = canonical_json_bytes(request.registry)
            manifest_raw = canonical_json_bytes(request.manifest)
            approval_raw = envelope_bytes(recovery.approval.envelope)  # type: ignore[union-attr]
            registry_path = root / "registry.json"
            manifest_path = root / "manifest.json"
            approval_path = root / "approval.json"
            signature_path = root / "approval.sig"
            registry_path.write_bytes(registry_raw)
            manifest_path.write_bytes(manifest_raw)
            approval_path.write_bytes(approval_raw)
            signature_path.write_bytes(recovery.approval.signature)  # type: ignore[union-attr]
            args = (
                "recover", "--repo", "repo-a", "--registry", str(registry_path),
                "--expected-registry-sha256", sha256_hex(registry_raw),
                "--manifest", str(manifest_path),
                "--expected-manifest-sha256", sha256_hex(manifest_raw),
                "--expected-plan-sha256", request.plan.sha256,
                "--expected-canonical", str(request.manifest.canonical_beads),
                "--expected-adapter", "br-sqlite-v1",
                "--expected-tracker-path", "/bin/true", "--expected-tracker-version", "fixture",
                "--expected-tracker-sha256", "a" * 64,
                "--expected-git-path", "/bin/true", "--expected-git-version", "fixture",
                "--expected-git-sha256", "a" * 64,
                "--approval", str(approval_path), "--approval-signature", str(signature_path),
                "--run-id", request.run_id, "--expected-journal-sha256", recovery.expected_journal_sha256,
                "--recover",
            )
            class BinaryStdout:
                def __init__(self) -> None:
                    self.buffer = io.BytesIO()

            output = BinaryStdout()
            diagnostics = io.StringIO()
            with patch.object(cli, "BrSqliteV1Adapter", lambda: request.adapter), patch.object(
                cli, "FileControlStore", lambda root: request.control
            ), patch.object(cli, "_pinned_verifier", lambda: request.verifier), patch.object(
                cli, "build_manifest", lambda selected, adapter: request.manifest
            ), patch.object(cli.sys, "stdout", output), redirect_stderr(diagnostics):
                result = cli.main(args)
            self.assertEqual(result, 0)
            payload = json.loads(output.buffer.getvalue())
            self.assertTrue(payload["ok"])
            self.assertTrue(payload["recovered"])
            self.assertEqual(payload["status"], "ROLLED_BACK")
            self.assertEqual(payload["repo_id"], "repo-a")
            self.assertEqual(payload["adapter"], "br-sqlite-v1")
            self.assertEqual(diagnostics.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
