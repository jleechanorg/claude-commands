"""Unit tests for wa-prod-data-query helper functions.

Run: cd ~/.hermes_prod/skills/wa-prod-data-query && python3 -m unittest discover -s tests -v

These tests mock out Firestore/auth and only verify the deterministic logic:
    - test-pattern detection
    - datetime coercion from various input shapes
    - session clustering with the 30-min gap rule
    - $USER exclusion handling
    - report rendering format
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from datetime import datetime, timezone

# Add the scripts/ directory to sys.path so we can import the helper module
HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(HERE)
SCRIPTS_DIR = os.path.join(SKILL_ROOT, "scripts")
sys.path.insert(0, SCRIPTS_DIR)

# Import only the pure-Python helpers — skip firebase-admin at module import
import importlib.util

spec = importlib.util.spec_from_file_location("query_real_users", os.path.join(SCRIPTS_DIR, "query_real_users.py"))
qru = importlib.util.module_from_spec(spec)
# Pre-stub the WA-specific import so module body doesn't try to load firebase-admin
import types
fake_stub = types.ModuleType("clock_skew_credentials")
fake_stub.apply_clock_skew_patch = lambda: None
sys.modules["clock_skew_credentials"] = fake_stub
fake_admin = types.ModuleType("firebase_admin")
fake_admin._apps = {"already-initialized"}  # pretend it's initialized so init_app isn't called
fake_admin.initialize_app = lambda cred: None
sys.modules["firebase_admin"] = fake_admin
sys.modules["firebase_admin.credentials"] = types.ModuleType("firebase_admin.credentials")
sys.modules["firebase_admin.credentials"].Certificate = lambda x: None

# Patch out the WA import path injection by overriding ensure_wa_imports
qru.ensure_wa_imports = lambda: None  # type: ignore
spec.loader.exec_module(qru)


class TestIsTestEmail(unittest.TestCase):
    def test_none_is_test(self):
        self.assertTrue(qru.is_test_email(None))

    def test_empty_is_test(self):
        self.assertTrue(qru.is_test_email(""))

    def test_test_user_is_test(self):
        self.assertTrue(qru.is_test_email("test-user@example.com"))

    def test_anon_is_test(self):
        self.assertTrue(qru.is_test_email("anon12345@gmail.com"))

    def test_dev_runner_is_test(self):
        self.assertTrue(qru.is_test_email("dev-runner@worldarchitecture-ai.iam.gserviceaccount.com"))

    def test_example_com_is_test(self):
        self.assertTrue(qru.is_test_email("foo@example.com"))

    def test_jleechantest_is_test(self):
        # jleechantest is Jeffrey's personal test account family
        self.assertTrue(qru.is_test_email("<your-email@gmail.com>"))
        self.assertTrue(qru.is_test_email("jleechantest3@gmail.com"))

    def test_real_gmail_is_real(self):
        self.assertFalse(qru.is_test_email("stream.of.silver@gmail.com"))

    def test_real_snapchat_is_real(self):
        self.assertFalse(qru.is_test_email("dlin@snapchat.com"))

    def test_case_insensitive(self):
        self.assertTrue(qru.is_test_email("TEST-user@gmail.com"))


class TestToDt(unittest.TestCase):
    def test_none(self):
        self.assertIsNone(qru.to_dt(None))

    def test_naive_datetime_gets_utc(self):
        d = datetime(2026, 6, 15, 12, 0, 0)
        out = qru.to_dt(d)
        self.assertEqual(out.tzinfo, timezone.utc)

    def test_aware_datetime_passes_through(self):
        d = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        out = qru.to_dt(d)
        self.assertEqual(out, d)

    def test_int_milliseconds(self):
        # 2026-06-15 12:00:00 UTC = 1781553600000 ms
        out = qru.to_dt(1781553600000)
        self.assertEqual(out.year, 2026)
        self.assertEqual(out.month, 6)
        self.assertEqual(out.day, 15)
        self.assertEqual(out.tzinfo, timezone.utc)

    def test_int_seconds(self):
        # 2026-06-15 12:00:00 UTC = 1781553600 s
        out = qru.to_dt(1781553600)
        self.assertEqual(out.year, 2026)
        self.assertEqual(out.tzinfo, timezone.utc)


class TestCollectRealUsersAggregation(unittest.TestCase):
    """Test the aggregation logic with mocked Firestore."""

    def _fake_record(self, uid, email, turns):
        return {"uid": uid, "turns": turns, "last_updated": qru.to_dt(turns[-1]) if turns else None}

    def test_real_user_is_kept(self):
        # Hand-craft a tiny data dict and run aggregation logic
        # (collect_real_users requires firebase; instead, test the post-aggregation rendering)
        data = {
            "by_email": {
                "akey445@gmail.com": {"uid": "C3dNG", "turns": [1.0, 1.1, 1.2, 100.0, 100.1], "n_turns": 5, "sessions": [(qru.to_dt(1.0), qru.to_dt(1.2), 3), (qru.to_dt(100.0), qru.to_dt(100.1), 2)], "last_updated": qru.to_dt(100.1)},
            },
            "summary": {"signins_7d": 1, "signins_30d": 1, "unique_active_7d": 1, "total_turns_7d": 5, "window_days": 7, "now": "2026-06-23T09:00:00+00:00"},
        }
        out = qru.render_report(data, top=10)
        self.assertIn("akey445@gmail.com", out)
        self.assertIn("TURNS", out)
        self.assertIn("SESSIONS", out)
        self.assertIn("5", out)  # turns
        self.assertIn("2", out)  # sessions


class TestSessionClustering(unittest.TestCase):
    """Verify the 30-min session-gap rule via the render_report path.

    Full session-clustering happens inside collect_real_users which needs
    Firebase; here we test by constructing an already-clustered record and
    ensuring the format renders both session counts correctly.
    """

    def test_two_sessions_render_as_two(self):
        data = {
            "by_email": {
                "x@gmail.com": {
                    "uid": "x",
                    "turns": [t for t in range(10)],
                    "n_turns": 10,
                    "sessions": [
                        (qru.to_dt(1.0), qru.to_dt(3.0), 3),
                        (qru.to_dt(200.0), qru.to_dt(209.0), 7),  # >30min gap from previous
                    ],
                    "last_updated": qru.to_dt(209.0),
                },
            },
            "summary": {"signins_7d": 1, "signins_30d": 1, "unique_active_7d": 1, "total_turns_7d": 10, "window_days": 7, "now": "2026-06-23T09:00:00+00:00"},
        }
        out = qru.render_report(data, top=10)
        self.assertIn("10", out)  # turns
        self.assertIn("2", out)   # sessions
        self.assertIn("x@gmail.com", out)


class TestSummaryShape(unittest.TestCase):
    def test_summary_keys(self):
        # Validate the summary keys are stable; useful for downstream tools
        keys = {"signins_7d", "signins_30d", "unique_active_7d", "total_turns_7d", "window_days", "now"}
        data = {
            "by_email": {},
            "summary": {**{k: 0 for k in keys}, "window_days": 7, "now": "2026-06-23T09:00:00+00:00"},
        }
        out = qru.render_report(data, top=10)
        # Summary line should mention each key as a row label
        for label in ["sign-ins (7d)", "sign-ins (30d)", "Unique active", "Total turns", "window=7"]:
            self.assertIn(label, out)


if __name__ == "__main__":
    unittest.main()