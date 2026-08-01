"""Integration tests for evidence-attach-to-slack post-upload contract.

These tests exercise the **post-upload gate** added in v1.2.0 (2026-07-10):
after every upload batch the agent MUST (a) post a single consolidated
summary message in the thread AND (b) re-verify the attachments are still
present in the thread after the summary post lands.

The motivation: the channel-bridge leaks internal narration into the same
thread (think-block prose, tool-call names). Without the summary message
acting as a cluster anchor, attachments drift out of the user's viewport
and the user concludes "you didn't post the screenshots".

Tests are organized into two tiers:

1. **Contract tests (always run):** verify the skill file itself documents
   the mandatory post-upload stages and the new failure-mode entry.
2. **Live integration tests (gated behind INTEGRATION_LIVE=1):** drive the
   full pipeline against a real Slack thread with a real PNG. Unit tests
   don't catch the "buried under chatter" failure mode — only a real
   Slack workspace exercise does.

Why no `MEDIA:`-style mocks: every Slack-rendering regression in this repo
history was caused by trusting a mock instead of testing the real API.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


SKILL_PATH = Path(os.path.expanduser("~/.hermes/skills/evidence-attach-to-slack/SKILL.md"))
PROD_SKILL_PATH = Path(os.path.expanduser("~/.hermes_prod/skills/evidence-attach-to-slack/SKILL.md"))
UPLOAD_BATCH_PY = Path(os.path.expanduser("~/.hermes/skills/evidence-attach-to-slack/scripts/upload_batch.py"))


class TestSkillFileContract(unittest.TestCase):
    """Verify SKILL.md documents the mandatory post-upload contract."""

    def test_skill_file_exists(self):
        self.assertTrue(SKILL_PATH.exists(), f"SKILL.md missing at {SKILL_PATH}")

    def test_skill_version_is_v1_2(self):
        text = SKILL_PATH.read_text()
        self.assertIn("version: 1.2.0", text, "skill version must be bumped to 1.2.0")

    def test_post_upload_summary_section_exists(self):
        text = SKILL_PATH.read_text()
        # Mandatory section header (was "Optional" in v1.1.0)
        self.assertIn(
            "Stage 3½ — Post consolidated summary message (MANDATORY",
            text,
            "the post-upload summary section must be marked MANDATORY (v1.2.0 contract)",
        )

    def test_reverify_stage_4_exists(self):
        text = SKILL_PATH.read_text()
        self.assertIn("Stage 4 — Re-verify AFTER summary lands (MANDATORY)", text)

    def test_buried_attachments_failure_mode_present(self):
        text = SKILL_PATH.read_text()
        self.assertIn(
            "you keep skipping this",
            text,
            "the 'you keep skipping this' failure mode must be documented",
        )
        self.assertIn(
            "Attachments uploaded + verified present, but user still replies",
            text,
        )

    def test_second_failure_mode_in_why_section(self):
        text = SKILL_PATH.read_text()
        self.assertIn("Second failure mode (added 2026-07-10)", text)

    def test_post_upload_recipe_uses_pinned_filename_lines(self):
        """The summary must NOT use MEDIA: inline tokens (proven broken 2026-07-08)."""
        text = SKILL_PATH.read_text()
        # Find the Stage 3½ example block
        start = text.find("### Stage 3½")
        end = text.find("### Stage 4")
        section = text[start:end]
        self.assertNotIn("MEDIA:/", section, "Stage 3½ example must not include MEDIA: inline tokens")
        self.assertIn("📎 Evidence attached to this thread", section)

    def test_trigger_phrases_include_skipping_re_phrase(self):
        text = SKILL_PATH.read_text()
        # Triggers section must include the user-typed re-trigger phrase
        self.assertIn('"you keep skipping this"', text)
        self.assertIn('"I need the media evidence on this thread"', text)

    def test_upload_batch_recipe_documented(self):
        """The canonical upload_batch.py script must still be referenced."""
        self.assertTrue(UPLOAD_BATCH_PY.exists(), f"upload_batch.py missing at {UPLOAD_BATCH_PY}")
        text = SKILL_PATH.read_text()
        self.assertIn("upload_batch.py", text, "skill must reference the canonical upload_batch.py script")


class TestStagingProdSync(unittest.TestCase):
    """Verify staging and prod copies of the skill are in sync."""

    def test_skill_files_in_sync(self):
        if not PROD_SKILL_PATH.exists():
            self.skipTest(f"prod skill not found at {PROD_SKILL_PATH}")
        # Both copies must reflect v1.2.0 changes
        for path in (SKILL_PATH, PROD_SKILL_PATH):
            text = path.read_text()
            self.assertIn("version: 1.2.0", text, f"{path} not on v1.2.0")
            self.assertIn("Stage 3½ — Post consolidated summary message (MANDATORY", text)
            self.assertIn("Stage 4 — Re-verify AFTER summary lands (MANDATORY)", text)


@unittest.skipUnless(
    os.environ.get("INTEGRATION_LIVE") == "1",
    "set INTEGRATION_LIVE=1 to exercise the live Slack upload + verify pipeline",
)
class TestLiveUploadContract(unittest.TestCase):
    """Live integration test: upload a real PNG, post summary, re-verify."""

    THREAD_TS = "1782519424.587489"  # PR #7953 evidence parent thread (Jeffrey's msg)

    def setUp(self):
        token = os.environ.get("HERMES_SLACK_BOT_TOKEN")
        if not token:
            out = subprocess.run(
                ["bash", "-lc", "source ~/.bashrc && echo $HERMES_SLACK_BOT_TOKEN"],
                capture_output=True, text=True, timeout=10,
            )
            token = out.stdout.strip()
        self.token = token
        self.assertTrue(self.token.startswith("xoxb-"), "HERMES_SLACK_BOT_TOKEN must be set")

    def _upload(self, path: str, title: str) -> str:
        size = os.path.getsize(path)
        r1 = subprocess.run([
            "curl", "-fsS", "-X", "POST",
            "https://slack.com/api/files.getUploadURLExternal",
            "-H", f"Authorization: Bearer {self.token}",
            "-F", f"filename={os.path.basename(path)}",
            "-F", f"length={size}",
        ], capture_output=True, text=True, timeout=30)
        j1 = json.loads(r1.stdout)
        assert j1.get("ok"), f"stage1 failed: {j1}"
        file_id, upload_url = j1["file_id"], j1["upload_url"]
        subprocess.run([
            "curl", "-fsS", "-X", "POST", upload_url,
            "-F", f"file=@{path}",
        ], capture_output=True, text=True, timeout=60, check=True)
        subprocess.run([
            "curl", "-fsS", "-X", "POST",
            "https://slack.com/api/files.completeUploadExternal",
            "-H", f"Authorization: Bearer {self.token}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({
                "files": [{"id": file_id, "title": title}],
                "channel_id": "C0AH3RY3DK6",
                "thread_ts": self.THREAD_TS,
            }),
        ], capture_output=True, text=True, timeout=30, check=True)
        return file_id

    def _fetch_attachments(self) -> set[str]:
        r = subprocess.run([
            "curl", "-fsS",
            f"https://slack.com/api/conversations.replies?channel=C0AH3RY3DK6&ts={self.THREAD_TS}&limit=100",
            "-H", f"Authorization: Bearer {self.token}",
        ], capture_output=True, text=True, timeout=15)
        data = json.loads(r.stdout)
        return {f["id"] for m in data.get("messages", []) for f in (m.get("files") or [])}

    def _fetch_recent_messages(self, limit: int = 100) -> list[dict]:
        """Fetch ALL messages in the thread by paginating with cursors."""
        all_messages: list[dict] = []
        cursor: str | None = None
        while True:
            url = (
                f"https://slack.com/api/conversations.replies"
                f"?channel=C0AH3RY3DK6&ts={self.THREAD_TS}&limit={limit}"
            )
            if cursor:
                url += f"&cursor={cursor}"
            r = subprocess.run([
                "curl", "-fsS", url,
                "-H", f"Authorization: Bearer {self.token}",
            ], capture_output=True, text=True, timeout=15)
            data = json.loads(r.stdout)
            all_messages.extend(data.get("messages", []))
            cursor = (data.get("response_metadata") or {}).get("next_cursor")
            if not cursor:
                break
        return all_messages

    def test_summary_message_must_be_most_recent_bot(self):
        """Contract: after upload batch, summary post lands as last bot message."""
        # Use one of the existing 4 PNGs (already in this thread from the manual upload)
        png = "/tmp/pr7953-evidence/before-modal.png"
        if not os.path.exists(png):
            self.skipTest(f"PNG not present at {png}")

        # Upload a fresh PNG with a unique marker
        marker = f"[evidence-attach-to-slack-v1.2.0-test-{os.getpid()}]"
        title = f"{marker} — contract test sentinel"
        file_id = self._upload(png, title)

        # Slack has eventual consistency for new file-share uploads. Wait for the
        # new file_id to appear in the thread before posting the summary.
        # Maximum wait: 30s, poll every 1s.
        import time
        deadline = time.time() + 30
        attached = set()
        while time.time() < deadline:
            attached = {f["id"] for m in self._fetch_recent_messages() for f in (m.get("files") or [])}
            if file_id in attached:
                break
            time.sleep(1)
        self.assertIn(file_id, attached, f"upload {file_id} not in thread attachments after 30s")

        # Post summary message naming the file
        summary = f"📎 Evidence attached to this thread:\n1. {os.path.basename(png)} — contract test sentinel {marker}"
        r = subprocess.run([
            "curl", "-fsS", "-X", "POST",
            "https://slack.com/api/chat.postMessage",
            "-H", f"Authorization: Bearer {self.token}",
            "-H", "Content-Type: application/json; charset=utf-8",
            "-d", json.dumps({
                "channel": "C0AH3RY3DK6",
                "thread_ts": self.THREAD_TS,
                "text": summary,
            }),
        ], capture_output=True, text=True, timeout=15)
        j = json.loads(r.stdout)
        self.assertTrue(j.get("ok"), f"summary post failed: {j}")
        summary_ts = j["ts"]

        # Re-verify: attachments still present AND summary is the highest-ts bot message
        messages = self._fetch_recent_messages(limit=100)
        attached_after = {f["id"] for m in messages for f in (m.get("files") or [])}
        self.assertIn(file_id, attached_after, "attachment disappeared after summary post")
        # Find the most recent bot message by ts (not by array order — pagination
        # returns oldest-first, so we need max(ts)).
        bot_msgs = [
            m for m in messages
            if m.get("BotName") or (m.get("user") or "").startswith("U")
            and (m.get("subtype") or "") != "channel_join"
        ]
        # Filter to only bot-authored messages by the same user_id as the test
        bot_user_id = self._bot_user_id()
        my_bot_msgs = [m for m in bot_msgs if m.get("user") == bot_user_id]
        latest = max(my_bot_msgs, key=lambda m: float(m["ts"]))
        self.assertEqual(latest["ts"], summary_ts,
                         f"summary is not the latest bot message; latest: ts={latest['ts']} text={latest.get('text', '')[:80]!r}")

    def _bot_user_id(self) -> str:
        r = subprocess.run([
            "curl", "-fsS", "https://slack.com/api/auth.test",
            "-H", f"Authorization: Bearer {self.token}",
        ], capture_output=True, text=True, timeout=15)
        return json.loads(r.stdout).get("user_id", "")


if __name__ == "__main__":
    unittest.main(verbosity=2)