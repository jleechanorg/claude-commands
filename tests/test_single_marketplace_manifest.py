"""Contract: exactly one marketplace manifest; the second path is a symlink to it."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL = REPO_ROOT / ".claude-plugin" / "marketplace.json"
LINK = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"


class SingleMarketplaceManifestTest(unittest.TestCase):
    def test_link_is_a_symlink_to_the_canonical_manifest(self):
        self.assertTrue(LINK.is_symlink(), f"{LINK} must be a symlink, not a copy")
        self.assertEqual(CANONICAL.resolve(), LINK.resolve())

    def test_both_paths_parse_to_identical_json(self):
        self.assertEqual(json.loads(CANONICAL.read_text()), json.loads(LINK.read_text()))


if __name__ == "__main__":
    unittest.main()
