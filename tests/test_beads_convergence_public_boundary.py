"""Production mutation boundary regressions.

These tests intentionally use no disposable mutation harness.  They prove the
shipped module has no caller-selectable fixture authority and the CLI refuses
mutation before reading operator artifacts or opening control state.
"""

from __future__ import annotations

import io
import json
import unittest
from dataclasses import fields
from types import SimpleNamespace
from unittest.mock import patch

from scripts.beads_convergence import cli
from scripts.beads_convergence import transaction as production


class _Trap:
    fixture_only = True

    def __getattr__(self, name: str) -> object:
        raise AssertionError(f"production boundary touched caller fixture {name}")


class ProductionBoundaryTest(unittest.TestCase):
    def test_public_requests_have_no_fixture_authority_injection(self) -> None:
        for forbidden in (
            "FixtureControlStore",
            "TransactionCrash",
            "_write_redirect",
            "_restore_redirect",
            "_rollback",
            "_reattest",
            "_lease",
        ):
            self.assertFalse(hasattr(production, forbidden), forbidden)
        self.assertTrue(
            {"adapter", "control", "verifier", "fault_at"}.isdisjoint(
                field.name for field in fields(production.ApplyRequest)
            )
        )
        self.assertTrue(
            {"adapter", "control", "verifier"}.isdisjoint(
                field.name for field in fields(production.RecoveryRequest)
            )
        )

    def test_forgeable_fixture_markers_cannot_reach_nonce_journal_or_target(self) -> None:
        request = SimpleNamespace(
            apply=True,
            adapter=_Trap(),
            control=_Trap(),
            verifier=_Trap(),
            canonical_beads="/Users/jleechan/projects/worldarchitect.ai/.beads",
        )
        with self.assertRaisesRegex(
            production.TransactionError, "production writer lease is unavailable"
        ):
            production.apply_plan(request)  # type: ignore[arg-type]

    def test_cli_apply_and_recover_fail_before_artifact_or_control_access(self) -> None:
        class BinaryStdout:
            def __init__(self) -> None:
                self.buffer = io.BytesIO()

        for command, mode in (("apply", "--apply"), ("recover", "--recover")):
            with self.subTest(command=command):
                output = BinaryStdout()
                args = [command, "--repo", "repo-a"]
                if command == "recover":
                    args.extend(
                        [
                            "--run-id",
                            "run-a",
                            "--expected-journal-sha256",
                            "f" * 64,
                        ]
                    )
                args.extend(
                    [
                        "--registry",
                        "/nonexistent/registry.json",
                        "--expected-registry-sha256",
                        "a" * 64,
                        "--manifest",
                        "/nonexistent/manifest.json",
                        "--expected-manifest-sha256",
                        "b" * 64,
                        "--expected-plan-sha256",
                        "c" * 64,
                        "--expected-canonical",
                        "/non-temp/real-repository/.beads",
                        "--expected-adapter",
                        "br-sqlite-v1",
                        "--expected-tracker-path",
                        "/nonexistent/br",
                        "--expected-tracker-version",
                        "0.4.0",
                        "--expected-tracker-sha256",
                        "d" * 64,
                        "--expected-git-path",
                        "/nonexistent/git",
                        "--expected-git-version",
                        "2.0",
                        "--expected-git-sha256",
                        "e" * 64,
                        "--approval",
                        "/nonexistent/approval.json",
                        "--approval-signature",
                        "/nonexistent/approval.sig",
                        mode,
                    ]
                )
                with (
                    patch.object(cli, "load_registry", side_effect=AssertionError("read")),
                    patch.object(cli, "_capture", side_effect=AssertionError("artifact")),
                    patch.object(cli.sys, "stdout", output),
                ):
                    result = cli.main(args)
                payload = json.loads(output.buffer.getvalue())
                self.assertEqual(result, cli.EXIT_FAILURE)
                self.assertFalse(payload["ok"])
                self.assertIn("production writer lease is unavailable", payload["error"])


if __name__ == "__main__":
    unittest.main()
