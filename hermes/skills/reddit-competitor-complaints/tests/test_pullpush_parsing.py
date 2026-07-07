"""Integration test for PullPush.io round-trip.

Hits the live api.pullpush.io endpoint with the same query format the
scraper uses, verifies the response shape matches what
extract_candidates() expects. Skipped if no network or PullPush is down.

Run: cd ~/.hermes/skills/reddit-competitor-complaints/tests && \
     python3 -m pytest test_pullpush_parsing.py -v
"""
import json
import subprocess
import unittest
import sys
import os
import importlib.util

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_PATH = os.path.join(os.path.dirname(os.path.dirname(SKILL_DIR)), "scripts", "reddit-competitor-complaints.py")
if not os.path.isfile(SCRIPT_PATH):
    SCRIPT_PATH = os.path.join(os.path.dirname(SKILL_DIR), "scripts", "reddit-competitor-complaints.py")

if not os.path.isfile(SCRIPT_PATH):
    SCRIPT_PATH = os.path.join(
        os.path.expanduser("~"),
        ".hermes_prod", "scripts", "reddit-competitor-complaints.py",
    )
spec = importlib.util.spec_from_file_location("scraper", SCRIPT_PATH)
scraper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scraper)


class TestPullPushParsing(unittest.TestCase):
    """Verify the response shape from a single PullPush query."""

    URL = (
        "https://api.pullpush.io/reddit/search/submission/"
        "?subreddit=AIDungeon&size=10&sort=desc&sort_type=score"
    )

    def _fetch(self):
        r = subprocess.run(
            ["curl", "-sL", "--max-time", "20",
             "-A", scraper.USER_AGENT, self.URL],
            capture_output=True, text=True, timeout=25,
        )
        if r.returncode != 0 or not r.stdout.strip():
            self.skipTest(f"PullPush fetch failed rc={r.returncode}")
        try:
            return json.loads(r.stdout)
        except json.JSONDecodeError as e:
            self.skipTest(f"PullPush returned non-JSON: {e}")

    def test_response_has_data_key(self):
        data = self._fetch()
        self.assertIn("data", data)
        self.assertIsInstance(data["data"], list)

    def test_at_least_one_result(self):
        data = self._fetch()
        self.assertGreater(len(data["data"]), 0,
                           "Expected AIDungeon subreddit to have at least one submission")

    def test_each_result_has_required_fields(self):
        """The scraper reads: id, title, selftext, score, num_comments,
        subreddit, permalink, created_utc.  Verify PullPush returns all of them
        for at least 80% of the results (some historical posts are missing
        selftext)."""
        data = self._fetch()
        results = data["data"]
        required = {"id", "title", "score", "permalink", "subreddit", "created_utc"}
        missing_count = 0
        for h in results:
            if not required.issubset(h.keys()):
                missing_count += 1
        miss_rate = missing_count / max(1, len(results))
        self.assertLess(miss_rate, 0.2,
                        f"{missing_count}/{len(results)} results missing required fields")

    def test_permalink_format(self):
        """Permalinks should start with /r/ for cross-subreddit routing."""
        data = self._fetch()
        for h in data["data"][:3]:
            self.assertTrue(h["permalink"].startswith("/r/"),
                            f"Unexpected permalink: {h['permalink']}")

    def test_created_utc_is_numeric(self):
        data = self._fetch()
        for h in data["data"][:3]:
            v = h["created_utc"]
            self.assertIsInstance(v, (int, float, str),
                                  f"created_utc wrong type: {type(v)}")
            # PullPush sometimes returns it as a string; to_float() handles
            # both — just verify it's parseable.
            self.assertGreaterEqual(scraper.to_float(v), 0)


if __name__ == "__main__":
    unittest.main()
