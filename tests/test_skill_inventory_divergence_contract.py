"""Contract: the portable bundle is NOT a duplicate of .claude/skills.

Pins the 2026-10-13 audit numbers so any future consolidation plan cannot re-assume
"portable/** is a duplicate" and delete divergent/unique skill bodies. If the inventory
changes, update this test AND reconcile the affected skills before any collapse.
"""
from __future__ import annotations

import unittest

from scripts.report_skill_inventory_divergence import report


class SkillInventoryDivergenceContract(unittest.TestCase):
    def test_portable_set_is_divergent_not_a_duplicate(self):
        r = report()
        if r["status"] != "ok":
            self.skipTest("portable manifest absent - nothing to reconcile")
        self.assertEqual(7, len(r["missing_in_claude_skills"]),
                         f"portable-only skills changed: {r['missing_in_claude_skills']}")
        self.assertEqual(3, len(r["identical_bodies"]),
                         f"byte-identical set changed: {r['identical_bodies']}")
        self.assertEqual(19, len(r["differing_bodies"]),
                         f"divergent set changed: {r['differing_bodies']}")
        # The invariant that matters: most of the portable set is NOT a duplicate.
        self.assertGreater(len(r["differing_bodies"]) + len(r["missing_in_claude_skills"]),
                           len(r["identical_bodies"]))


if __name__ == "__main__":
    unittest.main()
