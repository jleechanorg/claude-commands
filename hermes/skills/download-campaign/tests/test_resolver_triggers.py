"""Resolver trigger eval — verifies the user phrases in RESOLVER.md
route to the download-campaign skill.

Heuristic: for each trigger phrase, check that `download-campaign` SKILL.md
exists and that the phrase appears in RESOLVER.md under that skill entry.
This is the same heuristic skillify uses, not a real LLM routing test.
"""
import re
import sys
import unittest
from pathlib import Path

RESOLVER = Path("$HOME/.hermes_prod/skills/RESOLVER.md")
SKILL = Path("$HOME/.hermes_prod/skills/download-campaign/SKILL.md")

# Phrases a user would actually type — taken from this conversation
PHRASES = [
    "download campaign",
    "fetch this campaign",
    "pull from firestore",
    "ingest campaign",
    "get campaign by id",
    "copy campaign X",
    "batch download recent campaigns",
    "scan last N days",
    "scan for >50 entries",
    "last 2 weeks of campaigns",
    "walk a WA campaign",
    "pull Vespera Thul",
    "pull Itachi",
    "single campaign download",
    "get the campaign",
]

class TestDownloadCampaignResolverTriggers(unittest.TestCase):
    def setUp(self):
        if not RESOLVER.exists():
            self.skipTest(f"RESOLVER.md not at {RESOLVER}")
        if not SKILL.exists():
            self.skipTest(f"SKILL.md not at {SKILL}")
        self.resolver_text = RESOLVER.read_text()
        self.skill_text = SKILL.read_text()

    def test_skill_md_exists(self):
        self.assertTrue(SKILL.exists(), "download-campaign SKILL.md missing")
        self.assertIn("download-campaign", self.skill_text[:200])

    def test_resolver_has_entry(self):
        self.assertRegex(self.resolver_text, r"## download-campaign")

    def test_resolver_has_file_path(self):
        m = re.search(r"## download-campaign.*?\*\*File:\*\*\s*`([^`]+)`",
                      self.resolver_text, re.DOTALL)
        self.assertIsNotNone(m, "Resolver entry missing **File:** path")
        self.assertIn("download-campaign", m.group(1))

    def test_each_phrase_present_in_resolver(self):
        """Each trigger phrase should appear somewhere in the resolver entry."""
        # Slice the resolver entry to just the download-campaign section
        m = re.search(
            r"## download-campaign(.*?)(?=\n## |\Z)",
            self.resolver_text, re.DOTALL
        )
        self.assertIsNotNone(m, "No download-campaign section found")
        section = m.group(1)
        for phrase in PHRASES:
            with self.subTest(phrase=phrase):
                # Be lenient — match case-insensitively
                self.assertIn(
                    phrase.lower(),
                    section.lower(),
                    f"Phrase {phrase!r} not in resolver entry",
                )

    def test_skill_describes_pitfalls(self):
        """The skill must call out the gRPC FD bug, story subcollection, and dev_mode."""
        for kw in [
            "gRPC FD inheritance",
            "story",  # not story_entries
            "WORLDAI_DEV_MODE",
            "idempotent",
            "id8",  # for slug collision
        ]:
            with self.subTest(keyword=kw):
                self.assertIn(kw, self.skill_text, f"SKILL.md missing {kw!r}")

    def test_script_is_in_path(self):
        script = Path("$HOME/.hermes_prod/skills/download-campaign/scripts/download_campaign.py")
        self.assertTrue(script.exists(), f"download_campaign.py not at {script}")
        # Script must have at least one --mode arg
        self.assertIn("--mode", script.read_text())


if __name__ == "__main__":
    unittest.main()
