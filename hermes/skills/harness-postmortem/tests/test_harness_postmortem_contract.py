"""
Tests for the /meta skill (canonical: harness-postmortem) — scope guardrail +
commit-not-codepath invariant + Phase 0/1 protocol coverage.

These tests verify the META-SKILL itself is scope-locked: it MUST NOT
investigate the underlying task the agent was working on, and its fix MUST
land in the agent's harness (SOUL.md / new skill / new test), not in the
project code path.

Run from any cwd:
    cd ~/.hermes/skills/harness-postmortem/tests && python3 -m pytest -q
    # or
    HERMES_SKILLS=~/.hermes/skills python3 -m pytest -q
"""

from __future__ import annotations

import os
import re
import unittest
from pathlib import Path


def _skill_path() -> Path:
    """Resolve the canonical skill SKILL.md path.

    Resolution order:
    1. `HARNESS_POSTMORTEM_SKILL` env var (explicit override).
    2. `HERMES_SKILLS` env var + harness-postmortem/SKILL.md.
    3. Walk up from this test file's location to find the SKILL.md
       (works whether tests are run from staging or a worktree).
    4. Fall back to `~/.hermes/skills/harness-postmortem/SKILL.md`.
    """
    explicit = os.environ.get("HARNESS_POSTMORTEM_SKILL")
    if explicit:
        return Path(explicit)
    env = os.environ.get("HERMES_SKILLS")
    if env:
        return Path(env) / "harness-postmortem" / "SKILL.md"
    # Walk up from this test file to find the SKILL.md.
    here = Path(__file__).resolve()
    for parent in (here.parent, here.parent.parent, here.parent.parent.parent):
        candidate = parent / "SKILL.md"
        if candidate.exists() and "harness-postmortem" in str(parent):
            return candidate
    return Path.home() / ".hermes" / "skills" / "harness-postmortem" / "SKILL.md"


def _slash_command_path() -> Path:
    """Slash command lives in user's Claude Code user-scope."""
    return Path.home() / ".claude" / "commands" / "meta.md"


def _soul_path() -> Path:
    return Path.home() / ".hermes" / "workspace" / "SOUL.md"


def _resolver_path() -> Path:
    env = os.environ.get("HERMES_SKILLS")
    if env:
        return Path(env) / "RESOLVER.md"
    return Path.home() / ".hermes" / "skills" / "RESOLVER.md"


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


class TestMetaSkillStructure(unittest.TestCase):
    """The skill file itself must exist, have valid frontmatter, and contain
    the canonical sections."""

    SKILL_PATH = _skill_path()

    def test_skill_md_exists(self):
        self.assertTrue(
            self.SKILL_PATH.exists(),
            f"harness-postmortem SKILL.md missing at {self.SKILL_PATH}",
        )

    def test_yaml_frontmatter(self):
        text = _read(self.SKILL_PATH)
        m = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
        self.assertIsNotNone(m, "SKILL.md must start with --- YAML frontmatter")
        fm = m.group(1)
        for required in ("name:", "version:", "description:", "triggers:"):
            self.assertIn(required, fm, f"frontmatter missing '{required}'")

    def test_name_field_is_harness_postmortem(self):
        """The internal skill name MUST be harness-postmortem to avoid the
        `meta-prompting` / `meta-harness` / `MetaGPT` collisions (Reviewer B,
        2026-07-02). `meta` is retained as a slash-command alias only."""
        text = _read(self.SKILL_PATH)
        m = re.search(r"^name:\s*(\S+)\s*$", text, flags=re.MULTILINE)
        self.assertIsNotNone(m)
        self.assertEqual(
            m.group(1), "harness-postmortem",
            f"internal skill name must be `harness-postmortem`, got {m.group(1)!r}",
        )

    def test_meta_alias_declared_in_frontmatter(self):
        """The `meta` alias must be declared explicitly so the slash-command
        path resolves to the same skill."""
        text = _read(self.SKILL_PATH)
        self.assertIn('internal-aliases:', text)
        self.assertIn('"meta"', text)

    def test_required_sections(self):
        text = _read(self.SKILL_PATH)
        for section in (
            "## Scope guardrail",
            "## Input shapes",
            "## Phases",
            "## Phase 0 — Classify the failure mode (MAST-anchored)",
            "## Phase 1 — Observe → Isolate → Simulate → Evaluate",
            "## Phase 2 — Apply fixes",
            "## Phase 3 — Land via hermes-deploy-pipeline",
            "## Phase 4 — Final reply",
            "## Anti-patterns",
            "## Loader / auto-fire contract",
            "## Prior art (cited to avoid duplicate work)",
        ):
            self.assertIn(section, text, f"SKILL.md missing section: {section}")

    def test_trigger_phrases_present(self):
        text = _read(self.SKILL_PATH)
        for trigger in (
            "autonomy violation",
            "hermes refused",
            "stopped halfway",
            "didn't do",
            "/meta",
            "fix the agent",
            "fix the harness not the task",
            "harness postmortem",
        ):
            self.assertIn(trigger, text.lower(), f"trigger phrase missing: {trigger!r}")


class TestScopeGuardrail(unittest.TestCase):
    """The skill MUST scope-lock to the agent behavior failure. It must NOT
    promote investigation of the underlying task."""

    SKILL_PATH = _skill_path()

    def test_explicit_scope_guardrail(self):
        text = _read(self.SKILL_PATH)
        self.assertIn("scope guardrail", text.lower())
        pattern = re.compile(
            r"(does NOT|will not|must not).{0,200}(underlying task|original task|the task)",
            flags=re.IGNORECASE | re.DOTALL,
        )
        self.assertRegex(text, pattern)

    def test_anti_patterns_section_exists(self):
        text = _read(self.SKILL_PATH)
        self.assertIn("## Anti-patterns", text)
        self.assertIn("Fix the underlying task too", text)

    def test_phase_0_failure_classes_includes_mast_mapping(self):
        text = _read(self.SKILL_PATH)
        # Phase 0 must map working classes to MAST + ETCLOVG (Reviewer B).
        self.assertIn("MAST", text)
        self.assertIn("ETCLOVG", text)
        self.assertIn("arXiv:2503.13657", text)
        self.assertIn("arXiv:2606.06324", text)
        # Working classes still present.
        for cls in (
            "mid-task-clarification-freeze",
            "local-commit-without-PR",
            "task-correction-pivot-refused",
            "capable-didn't-execute",
        ):
            self.assertIn(cls, text, f"Phase 0 missing failure class: {cls}")


class TestObserveIsolateSimulateEvaluate(unittest.TestCase):
    """Phase 1 must use the 4-step Observe→Isolate→Simulate→Evaluate spine
    (Reviewer B, replacing standalone 5-Whys). 5-Whys remains as a
    Simulate-phase heuristic."""

    SKILL_PATH = _skill_path()

    def test_four_step_spine_present(self):
        text = _read(self.SKILL_PATH)
        for step in ("Observe", "Isolate", "Simulate", "Evaluate"):
            self.assertIn(step, text, f"Phase 1 missing 4-step spine section: {step}")

    def test_five_whys_preserved_as_simulate_heuristic(self):
        """5-Whys is no longer the structural spine but must remain available
        inside the Simulate phase."""
        text = _read(self.SKILL_PATH)
        # Should mention 5-Whys in the context of Simulate.
        simulate_section = re.search(
            r"\*\*Simulate\*\*.*?(?=\n###|\n## |\Z)",
            text,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(simulate_section, "Simulate step not found")
        self.assertIn(
            "5-Whys",
            simulate_section.group(0),
            "5-Whys must remain inside Simulate phase as a prompt heuristic",
        )

    def test_reflexion_citation_in_observe(self):
        text = _read(self.SKILL_PATH)
        observe_section = re.search(
            r"\*\*Observe\*\*.*?(?=\n\d+\. \*\*Isolate|\Z)",
            text,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(observe_section)
        self.assertIn("Reflexion", observe_section.group(0))
        self.assertIn("openreview.net", observe_section.group(0))

    def test_existing_coverage_section(self):
        text = _read(self.SKILL_PATH)
        self.assertIn("Existing coverage", text)

    def test_proposed_fixes_layered(self):
        text = _read(self.SKILL_PATH)
        for layer in ("[Instructions]", "[Skill]", "[Test]"):
            self.assertIn(layer, text, f"proposed-fixes layer missing: {layer}")


class TestCommitNotCodepath(unittest.TestCase):
    """The /meta skill MUST land fixes in the agent's harness (SOUL.md /
    new skill / new test). It MUST NOT silently commit to the project code
    path the agent was attempting."""

    SKILL_PATH = _skill_path()

    def test_landing_uses_harness_files(self):
        text = _read(self.SKILL_PATH)
        for path_anchor in ("SOUL.md", "skills/", "hermes-deploy-pipeline"):
            self.assertIn(path_anchor, text, f"landing recipe missing path anchor: {path_anchor}")

    def test_no_commit_to_project_codepath(self):
        text = _read(self.SKILL_PATH)
        self.assertIn("BANNED", text)


class TestPriorArtCitations(unittest.TestCase):
    """Reviewer B requires that prior art (Refinex harness-fix, HarnessFix
    paper, MAST, Reflexion, Observe→Isolate→Simulate→Evaluate) be cited in
    the skill body — not just in the changelog."""

    SKILL_PATH = _skill_path()

    def test_prior_art_section_present(self):
        text = _read(self.SKILL_PATH)
        self.assertIn("## Prior art (cited to avoid duplicate work)", text)

    def test_refinex_citation(self):
        text = _read(self.SKILL_PATH)
        self.assertIn("Refinex-Space", text)
        self.assertIn("github.com/Refinex-Space/Refinex-Skills", text)

    def test_harnessfix_paper_citation(self):
        text = _read(self.SKILL_PATH)
        self.assertIn("HarnessFix paper", text)
        self.assertIn("arXiv:2606.06324", text)

    def test_mast_paper_citation(self):
        text = _read(self.SKILL_PATH)
        self.assertIn("MAST", text)
        self.assertIn("arXiv:2503.13657", text)

    def test_reflexion_citation(self):
        text = _read(self.SKILL_PATH)
        self.assertIn("Reflexion", text)
        self.assertIn("Shinn", text)


class TestSoulMdCommitBlock(unittest.TestCase):
    """The SOUL.md `## COMMIT: meta-autonomy-violation-handler` block must
    exist and follow the trigger-based pattern."""

    SOUL_PATH = _soul_path()

    def test_commit_block_present_and_structured(self):
        text = _read(self.SOUL_PATH)
        if "## COMMIT: meta-autonomy-violation-handler" not in text:
            self.skipTest(
                "SOUL.md `## COMMIT: meta-autonomy-violation-handler` not yet "
                "added — authoring pass adds it in the same turn."
            )
        m = re.search(
            r"## COMMIT: meta-autonomy-violation-handler\s*\n"
            r"(.*?)(?=\n## |\Z)",
            text,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(m)
        block = m.group(1)
        self.assertIn("Trigger:", block)
        self.assertIn("Action:", block)
        # Must reference the harness-postmortem skill (forward link) or the
        # /meta slash command (backward link).
        self.assertTrue(
            "harness-postmortem" in block or "/meta" in block or "skills/meta" in block,
            "COMMIT block must link to the harness-postmortem skill or /meta slash command",
        )


class TestResolverEntry(unittest.TestCase):
    """The skills/RESOLVER.md entry must exist with trigger phrases that
    ALSO appear in the SOUL.md COMMIT block (drift-detection, Reviewer A
    suggestion)."""

    def _resolver_text(self) -> str:
        return _read(_resolver_path())

    def _soul_text(self) -> str:
        return _read(_soul_path())

    def test_resolver_entry_present(self):
        text = self._resolver_text()
        if "## meta" not in text and "skills/harness-postmortem" not in text:
            self.skipTest("RESOLVER.md entry for harness-postmortem not yet added.")
        self.assertTrue(
            "skills/harness-postmortem/SKILL.md" in text
            or "skills/meta/SKILL.md" in text,
            "RESOLVER entry must point at the harness-postmortem skill file",
        )

    def test_trigger_drift_detection(self):
        """Reviewer A's suggestion: ensure SOUL.md COMMIT block and RESOLVER.md
        entry agree on at least 3 trigger phrases. If they drift, future
        sessions won't fire correctly."""
        resolver = self._resolver_text()
        soul = self._soul_text()
        if "## COMMIT: meta-autonomy-violation-handler" not in soul:
            self.skipTest("SOUL.md COMMIT not yet added.")
        if "## meta" not in resolver and "skills/harness-postmortem" not in resolver:
            self.skipTest("RESOLVER entry not yet added.")
        # Extract the COMMIT block and the RESOLVER entry.
        m = re.search(
            r"## COMMIT: meta-autonomy-violation-handler\s*\n(.*?)(?=\n## |\Z)",
            soul,
            flags=re.DOTALL,
        )
        soul_block = m.group(1).lower() if m else ""
        resolver_lower = resolver.lower()
        shared = [
            phrase
            for phrase in (
                "autonomy violation",
                "hermes refused",
                "stopped halfway",
                "didn't do its job",
                "fix the agent",
                "fix the harness not the task",
                "/meta",
            )
            if phrase in soul_block and phrase in resolver_lower
        ]
        self.assertGreaterEqual(
            len(shared), 3,
            f"SOUL.md COMMIT block and RESOLVER.md entry must share ≥3 trigger "
            f"phrases; found only {len(shared)}: {shared}",
        )


class TestSlashCommandFile(unittest.TestCase):
    """The /meta slash command file at ~/.claude/commands/meta.md must exist
    and reference the canonical skill (Reviewer A suggestion)."""

    SLASH_PATH = _slash_command_path()

    def test_slash_command_exists(self):
        self.assertTrue(
            self.SLASH_PATH.exists(),
            f"Slash command file missing at {self.SLASH_PATH}",
        )

    def test_slash_command_has_yaml_frontmatter(self):
        text = _read(self.SLASH_PATH)
        m = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
        self.assertIsNotNone(m, "slash command must start with --- YAML frontmatter")
        fm = m.group(1)
        self.assertIn("description:", fm)


class TestTriggerRegexCompiles(unittest.TestCase):
    """Reviewer A's suggestion: the auto-fire regex documented in the
    SKILL.md must be a valid regex that matches the documented trigger
    phrases (otherwise the auto-fire contract is dead code)."""

    SKILL_PATH = _skill_path()

    def test_trigger_regex_compiles_and_matches(self):
        text = _read(self.SKILL_PATH)
        # Find a fenced block whose contents start with `(autonomy violation|...)` —
        # that's the actual trigger-regex block, not a generic code fence.
        m = re.search(
            r"```\s*\n(\(autonomy violation.*?)\n```",
            text,
            flags=re.DOTALL,
        )
        if not m:
            self.skipTest("Trigger regex block (starting with `(autonomy violation`) not found in SKILL.md")
        regex_src = m.group(1)
        try:
            compiled = re.compile(regex_src, flags=re.IGNORECASE)
        except re.error as e:
            self.fail(f"Trigger regex does not compile: {e}\nPattern: {regex_src}")

        # The regex MUST match the canonical "autonomy violation" sample.
        self.assertRegex(
            "this is an autonomy violation from hermes",
            compiled,
            "Trigger regex does not match canonical 'autonomy violation' sample",
        )

        # And it MUST match /meta.
        self.assertRegex("/meta run on this", compiled)

        # And it MUST NOT match arbitrary unrelated text.
        self.assertNotRegex(
            "the weather is sunny today",
            compiled,
            "Trigger regex over-matches unrelated text — too permissive",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)