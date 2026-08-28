"""Focused read-only tests for the br-sqlite-v1 adapter."""

import ast
import hashlib
import inspect
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.beads_convergence import fsafety
from scripts.beads_convergence.adapters import (
    AdapterError,
    BrSqliteV1Adapter,
)
from scripts.beads_convergence.fsafety import (
    FsafetyError,
    GitProbe,
    UnsupportedCapability,
    VerifiedExecutable,
    open_trusted_tree,
    open_verified_executable,
    run_verified_git_probe,
)
from scripts.beads_convergence.models import BinaryBinding


class AdapterTest(unittest.TestCase):
    def _fixture_binding(
        self, root: Path, source: Path = Path(sys.executable)
    ) -> BinaryBinding:
        fixture = root / source.name
        shutil.copyfile(source, fixture)
        fixture.chmod(0o755)
        return BinaryBinding(
            fixture,
            "fixture",
            hashlib.sha256(fixture.read_bytes()).hexdigest(),
        )

    def _beads(self, root: Path) -> Path:
        beads = root / ".beads"
        beads.mkdir()
        (beads / "beads.db").write_bytes(b"SQLite format 3\x00" + b"\0" * 32)
        (beads / "issues.jsonl").write_bytes(b"{}\n")
        return beads

    def test_sqlite_backend_and_source_fingerprint_are_descriptor_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            beads = self._beads(root)
            with open_trusted_tree(root, beads) as handle:
                adapter = BrSqliteV1Adapter()
                self.assertEqual(adapter.attest_backend(handle).backend, "sqlite")
                snapshot = adapter.fingerprint_sources(handle)
                self.assertEqual(
                    [source.name for source in snapshot.sources],
                    ["beads.db", "issues.jsonl"],
                )
                self.assertTrue(snapshot.plan_only)
                self.assertFalse(snapshot.quiescent)

    def test_hot_journal_and_unknown_sidecar_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            beads = self._beads(root)
            (beads / "beads.db-journal").write_bytes(b"hot")
            with open_trusted_tree(root, beads) as handle, self.assertRaisesRegex(
                AdapterError, "hot beads.db-journal"
            ):
                BrSqliteV1Adapter().attest_backend(handle)

    def test_hard_linked_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            beads = self._beads(root)
            os.link(beads / "issues.jsonl", beads / "beads.db-wal")
            with open_trusted_tree(root, beads) as handle, self.assertRaisesRegex(
                AdapterError, "unsafe source"
            ):
                BrSqliteV1Adapter().fingerprint_sources(handle)

    def _assert_second_pass_race_rejected(
        self, source_name: str, *, replace_source: bool
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            beads = self._beads(root)
            (beads / "beads.db-wal").write_bytes(b"wal")
            (beads / "beads.db-shm").write_bytes(b"shm")
            real_listdir = os.listdir
            list_calls = 0

            def race_on_second_pass(path: object) -> list[str]:
                nonlocal list_calls
                list_calls += 1
                if list_calls == 3:
                    source = beads / source_name
                    changed = b"changed-" + source.read_bytes()
                    if replace_source:
                        replacement = beads / f".{source_name}.replacement"
                        replacement.write_bytes(changed)
                        os.replace(replacement, source)
                    else:
                        source.write_bytes(changed)
                return real_listdir(path)

            with open_trusted_tree(root, beads) as handle, mock.patch(
                "scripts.beads_convergence.adapters.os.listdir",
                side_effect=race_on_second_pass,
            ), self.assertRaisesRegex(
                AdapterError, "source family changed during fingerprint"
            ):
                BrSqliteV1Adapter().fingerprint_sources(handle)

    def test_second_family_pass_rejects_each_replaced_source(self) -> None:
        for source_name in BrSqliteV1Adapter.source_names:
            with self.subTest(source_name=source_name):
                self._assert_second_pass_race_rejected(
                    source_name, replace_source=True
                )

    def test_second_family_pass_rejects_each_written_source(self) -> None:
        for source_name in BrSqliteV1Adapter.source_names:
            with self.subTest(source_name=source_name):
                self._assert_second_pass_race_rejected(
                    source_name, replace_source=False
                )

    def test_unproven_writer_lease_is_plan_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            beads = self._beads(root)
            with open_trusted_tree(root, beads) as handle:
                lease = BrSqliteV1Adapter().acquire_writer_exclusion(handle, object())
                self.assertTrue(lease.plan_only)
                self.assertFalse(lease.available)

    def test_tracker_binding_verification_opens_and_hashes_without_execution(
        self,
    ) -> None:
        path = Path("/bin/echo")
        binding = BinaryBinding(
            path, "0.4.0", hashlib.sha256(path.read_bytes()).hexdigest()
        )
        with mock.patch(
            "scripts.beads_convergence.fsafety.os.fork",
            side_effect=AssertionError("tracker execution is forbidden"),
        ):
            executable = BrSqliteV1Adapter().verify_binary(binding)
        try:
            self.assertEqual(executable.binding, binding)
            self.assertEqual(executable.measured_sha256, binding.sha256)
        finally:
            executable.close()

    def test_tracker_binding_rejects_unsupported_version_before_open(self) -> None:
        binding = BinaryBinding(Path("/bin/echo"), "0.5.0", "a" * 64)
        with mock.patch(
            "scripts.beads_convergence.adapters.open_verified_executable",
            side_effect=AssertionError("unsupported version must not be opened"),
        ), self.assertRaisesRegex(AdapterError, "unsupported tracker version"):
            BrSqliteV1Adapter().verify_binary(binding)

    def test_tracker_runtime_probes_fail_before_execution(self) -> None:
        adapter = BrSqliteV1Adapter()
        fake = VerifiedExecutable(0, object(), 0, 0, "")
        with tempfile.TemporaryDirectory() as temp, open_trusted_tree(
            Path(temp), Path(temp)
        ) as worktree, mock.patch(
            "scripts.beads_convergence.fsafety.os.fork",
            side_effect=AssertionError("tracker execution is forbidden"),
        ):
            with self.assertRaisesRegex(AdapterError, "snapshot-backed"):
                adapter.verify_health(worktree, fake)
            with self.assertRaisesRegex(AdapterError, "snapshot-backed"):
                adapter.resolve_authority(worktree, fake)
            with self.assertRaisesRegex(AdapterError, "snapshot-backed"):
                adapter.redirect_oracle(Path("/canonical"), worktree, fake)

    @unittest.skipUnless(sys.platform == "darwin", "Darwin capability contract")
    def test_darwin_read_only_runner_rejects_user_owned_fixture_without_source_changes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            beads = self._beads(root)
            for name, content in (
                ("beads.db-wal", b"wal"),
                ("beads.db-shm", b"shm"),
            ):
                (beads / name).write_bytes(content)
            binding = self._fixture_binding(root)
            monitored = tuple(beads / name for name in BrSqliteV1Adapter.source_names)
            before = tuple(
                (path.stat().st_ino, path.stat().st_mtime_ns, path.read_bytes())
                for path in monitored
            )
            executable = open_verified_executable(binding)
            try:
                with open_trusted_tree(root, root) as cwd, self.assertRaisesRegex(
                    UnsupportedCapability, "root-controlled"
                ):
                    run_verified_git_probe(executable, GitProbe.VERSION, cwd)
            finally:
                executable.close()
            after = tuple(
                (path.stat().st_ino, path.stat().st_mtime_ns, path.read_bytes())
                for path in monitored
            )
            self.assertEqual(before, after)

    @unittest.skipUnless(sys.platform == "darwin", "Darwin capability contract")
    def test_darwin_read_only_runner_uses_verified_root_controlled_fixture(
        self,
    ) -> None:
        path = Path("/bin/echo")
        binding = BinaryBinding(
            path, "fixture", hashlib.sha256(path.read_bytes()).hexdigest()
        )
        executable = open_verified_executable(binding)
        try:
            with open_trusted_tree(Path("/"), Path("/")) as cwd:
                result = run_verified_git_probe(executable, GitProbe.VERSION, cwd)
        finally:
            executable.close()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"--version\n")

    @unittest.skipUnless(sys.platform == "darwin", "Darwin capability contract")
    def test_darwin_read_only_runner_rejects_replaced_binding_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            binding = self._fixture_binding(root)
            executable = open_verified_executable(binding)
            replacement = root / "replacement"
            shutil.copyfile(Path("/usr/bin/false"), replacement)
            replacement.chmod(0o755)
            os.replace(replacement, binding.path)
            try:
                with open_trusted_tree(root, root) as cwd, self.assertRaisesRegex(
                    FsafetyError, "pathname was replaced"
                ):
                    run_verified_git_probe(executable, GitProbe.VERSION, cwd)
            finally:
                executable.close()

    @unittest.skipUnless(sys.platform == "darwin", "Darwin capability contract")
    def test_darwin_root_controlled_topology_is_rechecked_before_exec(self) -> None:
        path = Path("/bin/echo")
        binding = BinaryBinding(
            path, "fixture", hashlib.sha256(path.read_bytes()).hexdigest()
        )
        executable = open_verified_executable(binding)
        parent_pid = os.getpid()

        def becomes_writable(*_args: object, **_kwargs: object) -> bool:
            return os.getpid() != parent_pid

        try:
            with mock.patch(
                "scripts.beads_convergence.fsafety.os.access",
                side_effect=becomes_writable,
            ), open_trusted_tree(Path("/"), Path("/")) as cwd:
                result = run_verified_git_probe(executable, GitProbe.VERSION, cwd)
        finally:
            executable.close()
        self.assertEqual(result.returncode, 127)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"root-controlled executable path changed", result.stderr)

    def test_git_probe_surface_has_no_argv_parameter(self) -> None:
        signature = inspect.signature(run_verified_git_probe)
        self.assertEqual(tuple(signature.parameters), ("executable", "probe", "cwd"))
        self.assertEqual(
            set(GitProbe),
            {GitProbe.VERSION, GitProbe.WORKTREE_LIST, GitProbe.COMMON_DIR},
        )

    def test_runtime_has_no_generic_executor_or_private_argv_callers(self) -> None:
        self.assertFalse(hasattr(fsafety, "run_verified"))
        runtime = Path(fsafety.__file__).parent
        private_definitions: list[tuple[str, str]] = []
        private_imports: list[tuple[str, str]] = []
        private_callers: list[tuple[str, str]] = []
        public_argv_functions: list[tuple[str, str]] = []
        for path in sorted(runtime.glob("*.py")):
            tree = ast.parse(path.read_text(), filename=str(path))
            parents = {
                child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)
            }
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name.startswith("_run_verified"):
                        private_definitions.append((path.name, node.name))
                    if (
                        path.name == "fsafety.py"
                        and not node.name.startswith("_")
                        and any(
                            argument.arg == "argv" for argument in node.args.args
                        )
                    ):
                        public_argv_functions.append((path.name, node.name))
                if isinstance(node, ast.ImportFrom):
                    private_imports.extend(
                        (path.name, alias.name)
                        for alias in node.names
                        if alias.name.startswith("_run_verified")
                    )
                if not isinstance(node, ast.Call):
                    continue
                called_name = (
                    node.func.id
                    if isinstance(node.func, ast.Name)
                    else node.func.attr
                    if isinstance(node.func, ast.Attribute)
                    else ""
                )
                if not called_name.startswith("_run_verified"):
                    continue
                parent = parents.get(node)
                while parent is not None and not isinstance(
                    parent, (ast.FunctionDef, ast.AsyncFunctionDef)
                ):
                    parent = parents.get(parent)
                private_callers.append(
                    (path.name, parent.name if parent is not None else "<module>")
                )
        self.assertEqual(
            private_definitions, [("fsafety.py", "_run_verified_argv")]
        )
        self.assertEqual(private_imports, [])
        self.assertEqual(public_argv_functions, [])
        self.assertEqual(
            private_callers, [("fsafety.py", "run_verified_git_probe")]
        )


if __name__ == "__main__":
    unittest.main()
