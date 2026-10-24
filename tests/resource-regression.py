#!/usr/bin/env python3
"""Exercise a supplied creation launcher against resource/auth gate cases.

This regression imports the supplied launcher and calls its real main entry
point. It never supplies a default launcher: use RESOURCE_TEST_RUNNER or the
first positional argument so the test cannot silently test a copy.
"""
from __future__ import annotations

import contextlib
import datetime
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


def _runner_from_args() -> Path:
    args = list(sys.argv[1:])
    runner_arg = None
    if args and not args[0].startswith("-"):
        runner_arg = args.pop(0)
    elif args[:1] == ["--runner"]:
        if len(args) < 2:
            raise SystemExit("--runner requires a launcher path")
        runner_arg = args[1]
        del args[:2]
    runner_value = runner_arg or os.environ.get("RESOURCE_TEST_RUNNER")
    if not runner_value:
        raise SystemExit(
            "supply the actual launcher path as the first argument or "
            "RESOURCE_TEST_RUNNER"
        )
    runner = Path(runner_value).expanduser()
    if not runner.is_file():
        raise SystemExit(f"RESOURCE_TEST_RUNNER is not a file: {runner}")
    sys.argv[:] = [sys.argv[0], *args]
    return runner


RUNNER = _runner_from_args()


class ReachedIdentity(Exception):
    """Sentinel proving the launcher reached its auth boundary."""


class ResourceRegression(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("resource_runner", RUNNER)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot import launcher: {RUNNER}")
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ledger = Path(self.tmp.name) / "scene.json"
        self.now = datetime.datetime.now(datetime.timezone.utc)
        self.start = (self.now - datetime.timedelta(seconds=1)).isoformat()
        self.end = (self.now + datetime.timedelta(seconds=600)).isoformat()

    def invoke(self, state="released", conflicts=(), auth_error=None, hold=None,
               owner="creation-test"):
        ledger_path = self.ledger
        if state == "absent":
            ledger_path = Path(self.tmp.name) / "missing-scene.json"
        else:
            ledger_path.write_text(json.dumps({
                "owner": owner,
                "state": state,
                "start": self.start,
                "end": self.end,
            }))
        argv = [
            "launcher", "--admitted-at", self.start,
            "--bounded-until", self.end,
            "--scene-ledger", str(ledger_path),
        ]
        if hold:
            argv += ["--current-human-hold", hold]
        patches = [
            patch.object(sys, "argv", argv),
            patch.object(self.mod, "verify_inputs"),
            patch.object(self.mod, "verify_source_bound_service",
                         return_value={}),
            patch.object(self.mod, "verify_served_frontend",
                         return_value={}),
            patch.object(self.mod, "verify_backend", return_value={}),
            patch.object(self.mod, "observe_live_resources",
                         return_value=list(conflicts), create=True),
            patch.object(self.mod, "require_identity",
                         side_effect=auth_error or
                         ReachedIdentity("auth reached")),
            patch.object(self.mod.subprocess, "Popen",
                         side_effect=AssertionError("must not launch")),
        ]
        with contextlib.ExitStack() as stack:
            for item in patches:
                stack.enter_context(item)
            self.mod.main()

    def test_released_reaches_auth(self):
        with self.assertRaises(ReachedIdentity):
            self.invoke()

    def test_fresh_handback_with_previous_other_owner_reaches_auth(self):
        with self.assertRaises(ReachedIdentity):
            self.invoke(owner="previous-operator")

    def test_unknown_pending_absent_ledger_do_not_create_permission_gate(self):
        for state in ("unknown", "pending", "absent"):
            with self.subTest(state=state), self.assertRaises(ReachedIdentity):
                self.invoke(state)

    def test_active_conflict_rejected_even_if_ledger_admitted(self):
        conflict = {
            "resource": "browser-profile", "owner": "pid:123",
            "evidence": "live argv exact profile match",
        }
        with self.assertRaisesRegex(
            SystemExit, "live resource conflict.*pid:123"
        ):
            self.invoke("admitted", conflicts=[conflict])

    def test_explicit_current_human_hold_rejected(self):
        with self.assertRaisesRegex(
            SystemExit, "current human hold: STOP device capture now"
        ):
            self.invoke("admitted", hold="STOP device capture now")

    def test_injected_auth_error_preserved_exactly(self):
        with self.assertRaises(SystemExit) as raised:
            self.invoke(auth_error=SystemExit(
                "HTTP 401: authentication rejected by issuer"
            ))
        self.assertEqual(
            str(raised.exception), "HTTP 401: authentication rejected by issuer"
        )

    def test_observer_matches_exact_profile_not_similar_paths(self):
        proc = Path(self.tmp.name) / "proc"
        proc.mkdir()
        for pid, argv in (
            (101, ["chrome", "--user-data-dir=" + str(self.mod.PROFILE)]),
            (102, ["python", "--google-profile", str(self.mod.PROFILE)]),
            (103, ["chrome", "--user-data-dir=" +
                    str(self.mod.PROFILE) + "-other"]),
            (104, ["echo", str(self.mod.PROFILE)]),
        ):
            entry = proc / str(pid)
            entry.mkdir()
            (entry / "cmdline").write_bytes(
                (chr(0).join(argv) + chr(0)).encode()
            )
        self.assertCountEqual(
            [item["owner"] for item in self.mod.observe_live_resources(proc)],
            ["pid:101", "pid:102"],
        )
        argv = [
            "launcher",
            "--bounded-until",
            self.end,
            "--scene-ledger",
            str(self.ledger),
        ]
        patches = [
            patch.object(sys, "argv", argv),
            patch.object(self.mod, "verify_inputs"),
            patch.object(self.mod, "verify_source_bound_service",
                         return_value={}),
            patch.object(self.mod, "verify_served_frontend",
                         return_value={}),
            patch.object(self.mod, "verify_backend", return_value={}),
            patch.object(self.mod, "require_identity",
                         side_effect=ReachedIdentity("auth reached")),
            patch.object(self.mod.subprocess, "Popen",
                         side_effect=AssertionError("must not launch")),
        ]
        with contextlib.ExitStack() as stack:
            for item in patches:
                stack.enter_context(item)
            with self.assertRaisesRegex(
                SystemExit, "live resource conflict.*pid:101"
            ):
                self.mod.main(
                    resource_observer=lambda: self.mod.observe_live_resources(proc)
                )

    def test_conflict_arriving_during_preflight_blocks_child(self):
        self.mod.ROOT = Path(self.tmp.name)
        argv = ["launcher", "--bounded-until", self.end,
                "--scene-ledger", str(self.ledger)]
        conflict = {
            "resource": "browser-profile", "owner": "pid:456",
            "evidence": "observed just before launch",
        }
        patches = [
            patch.object(sys, "argv", argv),
            patch.object(self.mod, "verify_inputs"),
            patch.object(self.mod, "verify_source_bound_service",
                         return_value={}),
            patch.object(self.mod, "verify_served_frontend",
                         return_value={}),
            patch.object(self.mod, "assert_same_served_asset"),
            patch.object(self.mod, "verify_backend", return_value={}),
            patch.object(self.mod, "require_identity",
                         return_value=("test@example.invalid", "synthetic-uid")),
        ]
        popen_patch = patch.object(self.mod.subprocess, "Popen")
        with contextlib.ExitStack() as stack:
            for item in patches:
                stack.enter_context(item)
            popen = stack.enter_context(popen_patch)
            observations = iter([[], [conflict]])
            with self.assertRaisesRegex(
                SystemExit, "live resource conflict.*pid:456"
            ):
                self.mod.main(
                    resource_observer=lambda: next(observations)
                )
            popen.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
