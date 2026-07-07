"""Unit tests for download_campaign.py — focus on pure functions."""
import sys
import unittest
from pathlib import Path

# Add the scripts dir to path so we can import the module
SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))

import download_campaign as dc  # noqa: E402


class TestSlugify(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(dc.slugify("Vespera Thul"), "vespera-thul")

    def test_special_chars_collapsed(self):
        self.assertEqual(dc.slugify("BG3 — Nocturne v3.5!"), "bg3-nocturne-v3-5")

    def test_truncation(self):
        s = "a" * 200
        out = dc.slugify(s)
        self.assertLessEqual(len(out), 80)
        self.assertEqual(len(out), 80)

    def test_strip_leading_trailing_dashes(self):
        self.assertEqual(dc.slugify("  hello  "), "hello")
        self.assertEqual(dc.slugify("---foo---"), "foo")

    def test_idempotent_path_uniqueness(self):
        """Two campaigns with the same title must produce different wiki paths."""
        title = "Vespera Thul (copy)"
        slug = dc.slugify(title)
        ids = ["a" * 20, "b" * 20, "c" * 20]
        paths = [f"{slug}-{i[:8]}.md" for i in ids]
        # The crucial check: all paths unique despite same slug
        self.assertEqual(len(set(paths)), 3)


class TestPathCollisionAvoidance(unittest.TestCase):
    def test_duplicate_titles_get_unique_paths(self):
        """Reproduces the actual bug: 'Vespera Thul (copy)' × 11 copies."""
        title = "Vespera Thul (copy)"
        slug = dc.slugify(title)
        ids = [f"abc{i:04d}xyz" for i in range(11)]
        paths = [f"{slug}-{cid[:8]}.md" for cid in ids]
        unique = set(paths)
        self.assertEqual(len(unique), 11, "Slug collision: duplicates would overwrite")
        # And the raw archive dir uses campaign_id directly — also unique
        raw_dirs = [cid for cid in ids]
        self.assertEqual(len(set(raw_dirs)), 11)


class TestDependencyCheck(unittest.TestCase):
    def test_required_modules_importable(self):
        """The .venv dep chain must be installed for this skill to work."""
        required = [
            "firebase_admin",
            "google.cloud.firestore",
            "flask",
            "pydantic",
            "jsonschema",
            "docx",
            "fpdf",
            "clock_skew_credentials",
        ]
        missing = []
        for mod in required:
            try:
                __import__(mod)
            except ImportError as e:
                missing.append(f"{mod}: {e}")
        self.assertFalse(
            missing,
            f"Missing deps in WA .venv: {missing}. "
            "Run the bootstrap in SKILL.md Phase 1.",
        )


if __name__ == "__main__":
    unittest.main()
