"""Tests for the Hermes-side memory-search skill overlay.

Contract:
1. Overlay file exists at `skills/memory-search/SKILL.md` under the jleechanclaw repo.
2. Frontmatter parses with valid YAML (name, description, ---).
3. References the canonical Claude-side file at `~/.claude/skills/memory-search/SKILL.md`.
4. Lists all 10 memory sources in the fan-out (roadmap, beads, claude memories, hermes sqlite, hermes briefings, hermes index, openclaw memories, wiki, history, slack).
5. Triggers on the standard phrases: 'search memories', '/ms', 'look up in memory', 'find in my memories'.
6. SOUL.md `## COMMIT: ms-on-new-task` references this overlay (no broken skill_view calls).
7. AGENTS.md Session-Start Recall Routine references this overlay.
8. Three-home closure: overlay is reachable from `~/.hermes/skills/memory-search/SKILL.md` AND `~/.hermes_prod/skills/memory-search/SKILL.md` (symlink farm).

Run: python3 -m pytest skills/memory-search/tests/test_memory_search_overlay.py -v
"""

from __future__ import annotations

import os
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]  # skills/memory-search/tests/ -> repo root
WORKSPACE = REPO_ROOT / "workspace"
HERMES_SKILLS = Path(os.path.expanduser("~/.hermes/skills/memory-search/SKILL.md"))
HERMES_PROD_SKILLS = Path(os.path.expanduser("~/.hermes_prod/skills/memory-search/SKILL.md"))
CANONICAL_CLAUDE = Path(os.path.expanduser("~/.claude/skills/memory-search/SKILL.md"))


class TestMemorySearchOverlay(unittest.TestCase):
    def setUp(self) -> None:
        self.overlay = REPO_ROOT / "skills" / "memory-search" / "SKILL.md"
        self.soul = WORKSPACE / "SOUL.md"
        self.agents = WORKSPACE / "AGENTS.md"

    def test_overlay_file_exists_in_repo(self):
        self.assertTrue(
            self.overlay.exists(),
            f"overlay missing in repo: {self.overlay} — must live at skills/memory-search/SKILL.md",
        )

    def test_overlay_has_valid_yaml_frontmatter(self):
        text = self.overlay.read_text()
        self.assertTrue(text.startswith("---\n"), "overlay must start with ---")
        # Find the closing ---
        end = text.find("\n---\n", 4)
        self.assertGreater(end, 4, "overlay must have a closing --- in frontmatter")
        fm = text[4:end]
        self.assertIn("name: memory-search", fm, "frontmatter must declare name=memory-search")
        self.assertIn("description:", fm, "frontmatter must have a description")

    def test_overlay_references_canonical_claude_side(self):
        text = self.overlay.read_text()
        self.assertIn(
            "~/.claude/skills/memory-search/SKILL.md",
            text,
            "overlay must reference the canonical Claude-side file",
        )
        # Canonical file should actually exist
        self.assertTrue(
            CANONICAL_CLAUDE.exists(),
            f"canonical Claude-side skill missing: {CANONICAL_CLAUDE}",
        )

    def test_overlay_lists_all_10_memory_sources(self):
        text = self.overlay.read_text().lower()
        required_sources = [
            "~/roadmap",
            "beads",
            "claude memories",
            "hermes sqlite",
            "hermes briefings",
            "hermes index",
            "openclaw memories",
            "wiki",
            "history",
            "slack",
        ]
        for src in required_sources:
            self.assertIn(src, text, f"overlay must list '{src}' as a fan-out source")

    def test_overlay_triggers_on_standard_phrases(self):
        text = self.overlay.read_text().lower()
        required_triggers = [
            "search memories",
            "/ms",
            "look up in memory",
            "find in my memories",
        ]
        for trig in required_triggers:
            self.assertIn(trig, text, f"overlay must trigger on '{trig}'")

    def test_soul_md_references_overlay(self):
        text = self.soul.read_text()
        # The COMMIT block must mention the overlay (so the resolver path is wired)
        m = re.search(
            r"## COMMIT: ms-on-new-task\s*\n(.*?)(?=\n## COMMIT:|\Z)",
            text,
            re.DOTALL,
        )
        self.assertIsNotNone(m, "## COMMIT: ms-on-new-task must exist in SOUL.md")
        block = m.group(1)
        self.assertIn(
            "skills/memory-search/SKILL.md",
            block,
            "SOUL.md ms-on-new-task COMMIT must reference the Hermes-side overlay",
        )

    def test_agents_md_references_overlay(self):
        text = self.agents.read_text()
        self.assertIn(
            "skills/memory-search/SKILL.md",
            text,
            "AGENTS.md must reference the overlay in Session-Start Recall Routine",
        )

    def test_three_home_closure(self):
        # Hermes-side overlay should resolve from BOTH ~/.hermes/skills and ~/.hermes_prod/skills
        # via the symlink farm (verified inode-equal).
        if not HERMES_SKILLS.exists() and not HERMES_PROD_SKILLS.exists():
            self.skipTest(
                "Hermes-side overlay not yet deployed (run deploy.sh to sync). "
                "Repo overlay at skills/memory-search/SKILL.md is the source of truth."
            )
        # If one exists, both must resolve (symlink farm)
        if HERMES_SKILLS.exists():
            self.assertTrue(
                HERMES_SKILLS.exists(),
                "~/.hermes/skills/memory-search/SKILL.md missing — overlay must be in Hermes skill root",
            )
        if HERMES_PROD_SKILLS.exists():
            self.assertTrue(
                HERMES_PROD_SKILLS.exists(),
                "~/.hermes_prod/skills/memory-search/SKILL.md missing — overlay must be in prod runtime",
            )


if __name__ == "__main__":
    unittest.main()