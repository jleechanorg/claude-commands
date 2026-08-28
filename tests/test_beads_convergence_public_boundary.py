"""Production mutation boundary regressions.

These tests intentionally use no disposable mutation harness.  They prove the
shipped module has no caller-selectable fixture authority and the CLI refuses
mutation before reading operator artifacts or opening control state.
"""

from __future__ import annotations

import ast
import io
import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import fields
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts.beads_convergence import cli
from scripts.beads_convergence import transaction as production

ROOT = Path(__file__).resolve().parents[1]


class _Trap:
    fixture_only = True

    def __getattr__(self, name: str) -> object:
        raise AssertionError(f"production boundary touched caller fixture {name}")


class ProductionBoundaryTest(unittest.TestCase):
    def test_launcher_and_runtime_are_sealed_to_scripts_package(self) -> None:
        launcher = (ROOT / "scripts/beads-converge").read_text()
        self.assertIn('"-I"', launcher)
        self.assertIn("from beads_convergence.cli import main", launcher)
        for forbidden in (
            "parents[1]",
            "from scripts.beads_convergence",
        ):
            self.assertNotIn(forbidden, launcher)

        runtime_imports: set[str] = set()
        for path in (ROOT / "scripts/beads_convergence").glob("*.py"):
            tree = ast.parse(path.read_text(), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    runtime_imports.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module is not None:
                    runtime_imports.add(node.module)
        self.assertFalse(
            any(name == "tests" or name.startswith("tests.") for name in runtime_imports)
        )

        with tempfile.TemporaryDirectory() as temp:
            cwd = Path(temp)
            harness = cwd / "tests/beads_convergence_fixture_harness.py"
            harness.parent.mkdir()
            harness.write_text("raise RuntimeError('fixture harness imported')\n")
            probe = subprocess.run(
                (
                    sys.executable,
                    "-I",
                    "-c",
                    (
                        "import sys\n"
                        "sys.path.insert(0, sys.argv[1])\n"
                        "import beads_convergence.cli\n"
                        "try:\n import tests.beads_convergence_fixture_harness\n"
                        "except ModuleNotFoundError:\n raise SystemExit(0)\n"
                        "raise SystemExit(9)"
                    ),
                    str(ROOT / "scripts"),
                ),
                cwd=cwd,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(probe.returncode, 0, probe.stderr)

    def test_cli_source_has_no_retired_activation_helper_cluster(self) -> None:
        tree = ast.parse(Path(cli.__file__).read_text(), filename=str(cli.__file__))
        definitions = {
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        }
        imported = {
            alias.asname or alias.name
            for node in tree.body
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        retired_helpers = {
            "_capture",
            "_load_manifest",
            "_load_json",
            "_unique_pairs",
            "_reject_constant",
            "_approval",
            "_approval_binary",
            "_repo",
            "_binding_args_match",
            "_config_binding_args_match",
            "_control_root",
            "_pinned_verifier",
            "_transaction_success",
        }
        retired_imports = {
            "SignedApproval",
            "SshApprovalVerifier",
            "ApprovalEnvelope",
            "BinaryBinding",
            "Manifest",
            "decode_manifest",
        }
        self.assertTrue(retired_helpers.isdisjoint(definitions))
        self.assertTrue(retired_imports.isdisjoint(imported))

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
                    patch.object(
                        cli, "build_manifest", side_effect=AssertionError("inventory")
                    ),
                    patch.object(cli.sys, "stdout", output),
                ):
                    result = cli.main(args)
                payload = json.loads(output.buffer.getvalue())
                self.assertEqual(result, cli.EXIT_FAILURE)
                self.assertFalse(payload["ok"])
                self.assertIn("production writer lease is unavailable", payload["error"])


if __name__ == "__main__":
    unittest.main()
