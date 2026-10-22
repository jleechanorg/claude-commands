#!/usr/bin/env python3
"""Tests for the shared 2 complex + 2 short admission guard."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))

import capacity_guard as cg  # noqa: E402

LIVE = {"owner": "dot-a", "action": "running pytest", "receipt": "log://run/17/EXIT=0"}
FAKE = {"owner": "", "action": "assigned", "receipt": ""}


def entry(item_id, klass, evidence=None, **extra):
    row = {"id": item_id, "class": klass, "evidence": LIVE if evidence is None else evidence}
    row.update(extra)
    return row


class GuardTest(unittest.TestCase):
    def run_guard(self, state, wanted, item_id=None):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            path.write_text(json.dumps(state))
            argv = [sys.executable, str(HERE.parent / "scripts" / "capacity_guard.py"), "--state", str(path)]
            if wanted:
                argv += ["--class", wanted]
            if item_id:
                argv += ["--id", item_id]
            done = subprocess.run(argv, capture_output=True, text=True)
            return done.returncode, done.stdout.strip(), done.stderr.strip()

    def test_third_complex_rejected(self):
        state = {"active": [entry("a", "complex"), entry("b", "complex"), entry("c", "complex")]}
        code, out, _ = self.run_guard(state, "complex", "e")
        self.assertEqual(code, 3, out)
        self.assertTrue(out.startswith("REJECT complex:e"), out)
        self.assertIn("active=3 cap=2", out)

    def test_third_short_rejected(self):
        state = {"active": [entry("a", "complex"), entry("d", "short"), entry("e", "short"), entry("f", "short")]}
        code, out, _ = self.run_guard(state, "short", "g")
        self.assertEqual(code, 3, out)
        self.assertIn("active=3 cap=2", out)

    def test_second_complex_admitted(self):
        state = {"active": [entry("a", "complex")]}
        code, out, _ = self.run_guard(state, "complex", "b")
        self.assertEqual(code, 0, out)
        self.assertTrue(out.startswith("ADMIT complex:b"), out)

    def test_second_short_admitted_with_full_complex_lane(self):
        state = {"active": [entry("a", "complex"), entry("b", "complex"), entry("d", "short")]}
        code, out, _ = self.run_guard(state, "short", "e")
        self.assertEqual(code, 0, out)
        self.assertIn("active=1 cap=2", out)

    def test_fake_evidence_does_not_consume_capacity(self):
        state = {"active": [
            entry("a", "complex"),
            entry("b", "complex", FAKE),
            entry("c", "complex", FAKE),
            entry("d", "short", {"owner": "dot-a", "action": "open", "receipt": "  "}),
        ]}
        self.assertEqual(self.run_guard(state, "complex", "e")[0], 0)
        self.assertEqual(self.run_guard(state, "short", "f")[0], 0)

    def test_parked_work_does_not_occupy_slot(self):
        state = {"active": [
            entry("a", "complex"),
            entry("b", "complex"),
            {"id": "parked", "class": "complex", "parked": True,
             "resumption_trigger": "peer unblocks", "evidence": FAKE},
        ]}
        code, out, _ = self.run_guard(state, "complex", "e")
        self.assertEqual(code, 3, out)

    def test_counts_only_mode(self):
        state = {"active": [entry("a", "complex"), entry("d", "short")]}
        code, out, _ = self.run_guard(state, None)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.split(" ", 1)[1]), {"complex": 1, "short": 1})

    def test_unknown_class_is_error(self):
        state = {"active": [entry("a", "complex")]}
        self.assertEqual(self.run_guard(state, "medium", "x")[0], 2)

    def test_duplicate_id_is_error(self):
        state = {"active": [entry("a", "complex"), entry("a", "short")]}
        self.assertEqual(self.run_guard(state, "short")[0], 2)

    def test_malformed_state_is_error(self):
        self.assertEqual(self.run_guard({"active": "nope"}, "complex")[0], 2)
        self.assertEqual(self.run_guard([], "complex")[0], 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
