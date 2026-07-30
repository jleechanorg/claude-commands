"""Contract test: /nextsteps routing — default vs --full.

User requirement (verbatim, preserved in the test fixture below):

    "Make /nextsteps only do beads and ~/roadmap and
     /nextsteps --full does everything"

This test enforces the contract by reading the three files that govern the
`/nextsteps` command and asserting that:

1. **Command file** (`.claude/commands/nextsteps.md`) declares both modes and
   has the YAML header that `commands/CLAUDE.md` requires for executable
   commands.
2. **Skill file** (`.claude/skills/nextsteps/SKILL.md`) — the canonical
   protocol — has a "Modes" section that names both `default` and `--full`,
   tags the side-effecting phases (Claude auto-memory, mem0, GH Issues) as
   `--full`-only, and gives a Phase 8 checklist for each mode.
3. **Loose skill** (`.claude/skills/nextsteps.md`) — the user-scope fallback —
   also names both modes and tells the executor to skip the side-effecting
   phases in default mode.

A run that defaults to any of Phase 4 / Phase 5 / Phase 7b without an
explicit `--full` marker on the invocation is a regression and fails this
test.
"""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
NEXTSTEPS_CMD = REPO_ROOT / ".claude" / "commands" / "nextsteps.md"
NEXTSTEPS_SKILL = REPO_ROOT / ".claude" / "skills" / "nextsteps" / "SKILL.md"
NEXTSTEPS_LOOSE = REPO_ROOT / ".claude" / "skills" / "nextsteps.md"

# Verbatim user request, preserved per the task brief.
USER_REQUEST = (
    "Make /nextsteps only do beads and ~/roadmap and /nextsteps --full does everything"
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_checklist_body(text: str, header_regex: str):
    """Find a `**...:**` checklist header and return the body of `- [x] ...`
    bullets that follow it, up to the next bold-header or `---` separator.
    Returns (body, end_index) or (None, -1) if the header is missing.

    The skill formats checklists as:

        **Default mode checklist:**

        - `[x]` item one
        - `[x]` item two

        **`--full` mode checklist:**

        - `[x]` item one

    so we need to skip the blank line(s) between header and bullets, then
    slurp until the next `**...:**` block.
    """
    m = re.search(header_regex, text)
    if not m:
        return None, -1
    start = m.end()
    # Skip whitespace + newlines until first bullet.
    rest = text[start:]
    # Now collect lines that look like `- [x] ...` or `- [ ] ...`.
    body_lines = []
    pos = 0
    seen_bullet = False
    for line in rest.split("\n"):
        # Match `- [x] ...`, ``- `[x]` ...``, etc. The skill uses backtick-
        # wrapped checkbox markers (e.g. `- `[x]``); accept both.
        if re.match(r"^-\s+`?\[[ xX]\]`?\s+", line):
            body_lines.append(line)
            seen_bullet = True
            pos += len(line) + 1
        elif seen_bullet and line.strip().startswith("**"):
            # Next checklist block — stop.
            break
        elif seen_bullet and line.strip().startswith("---"):
            break
        elif line.strip() == "":
            # Blank line — keep going whether before or after bullets.
            pos += len(line) + 1
            continue
        else:
            # Non-bullet non-empty line. If we've already started a checklist,
            # the next section has begun; stop.
            if seen_bullet:
                break
            # Otherwise skip leading prose between header and bullets.
            pos += len(line) + 1
    return "\n".join(body_lines), start + pos


class NextstepsCommandContractTest(unittest.TestCase):
    """Contract for .claude/commands/nextsteps.md — the entry point Claude reads
    when the user types `/nextsteps`.
    """

    def setUp(self):
        self.assertTrue(
            NEXTSTEPS_CMD.is_file(),
            f"nextsteps command file missing at {NEXTSTEPS_CMD}",
        )
        self.text = read(NEXTSTEPS_CMD)

    def test_has_yaml_frontmatter(self):
        """commands/CLAUDE.md mandates YAML frontmatter for executable commands."""
        self.assertTrue(
            self.text.startswith("---\n"),
            "nextsteps command file must start with YAML frontmatter "
            "(see commands/CLAUDE.md); the old file had none.",
        )
        # Must close the frontmatter before the body.
        end = self.text.find("\n---\n", 4)
        self.assertGreater(
            end,
            4,
            "nextsteps command YAML frontmatter must close with a second `---` line.",
        )

    def test_declares_default_and_full_modes(self):
        """Both modes must be named in the command file so a reader knows
        which one is in effect before the skill loads.
        """
        # Case-insensitive lookup so we catch e.g. "Default" too.
        text_lower = self.text.lower()
        self.assertIn(
            "default",
            text_lower,
            "command file must document the default (lean) mode",
        )
        self.assertIn(
            "--full",
            text_lower,
            "command file must document the --full flag",
        )

    def test_preserves_user_request_verbatim(self):
        """The user's exact phrasing should appear somewhere on the command or
        skill files so a future maintainer can find the requirement.
        """
        # We accept the same content distributed across command + skill files.
        combined = (
            read(NEXTSTEPS_CMD)
            + "\n"
            + read(NEXTSTEPS_SKILL)
            + "\n"
            + read(NEXTSTEPS_LOOSE)
        )
        # Match on the unique "Make /nextsteps only do beads" prefix so we
        # don't false-positive on partial phrases elsewhere.
        self.assertIn(
            "Make /nextsteps only do beads and ~/roadmap",
            combined,
            "user's verbatim request must be preserved (verbatim string) "
            f"across the nextsteps command/skill files. Request: {USER_REQUEST!r}",
        )


class NextstepsSkillContractTest(unittest.TestCase):
    """Contract for .claude/skills/nextsteps/SKILL.md — the canonical protocol
    Claude reads when the command is invoked.
    """

    def setUp(self):
        self.assertTrue(
            NEXTSTEPS_SKILL.is_file(),
            f"nextsteps skill missing at {NEXTSTEPS_SKILL}",
        )
        self.text = read(NEXTSTEPS_SKILL)

    def test_modes_section_exists(self):
        """The skill must have an explicit Modes section naming both modes."""
        # Accept either `## Modes` or `## Modes (...)` — the canonical skill
        # uses the parenthetical form to put the routing hint front-and-center.
        self.assertRegex(
            self.text,
            r"##\s+[Mm]odes(\b|\s|\()",
            "skill must have a `## Modes` section (with optional parenthetical) "
            "that names both default and --full before any phase detail",
        )

    def test_default_mode_only_uses_beads_and_roadmap(self):
        """Default mode must be defined as reading only beads + ~/roadmap.

        We accept either a sentence ("reads only beads" / "only does beads
        and ~/roadmap") or a table row.
        """
        # Sentence form
        sentence_patterns = [
            r"default.*only.*beads.*~/roadmap",
            r"only does? beads.*~/roadmap",
        ]
        # Table form (the Modes table has a row labeled `default`)
        table_pattern = r"\|.*\*\*default\*\*.*\|.*\bbr\b.*~/roadmap"
        combined = self.text
        ok = any(
            re.search(p, combined, re.IGNORECASE | re.DOTALL) for p in sentence_patterns
        ) or re.search(table_pattern, combined, re.IGNORECASE | re.DOTALL)
        self.assertTrue(
            ok,
            "default mode must be explicitly scoped to beads + ~/roadmap "
            "(sentence or table row); found neither in the skill.",
        )

    def test_full_mode_does_everything(self):
        """`--full` mode must explicitly preserve the legacy all-source
        behavior — i.e. it must add Claude auto-memory + mem0 + GH Issues
        on top of the default mode.
        """
        sentence_patterns = [
            r"--full.*does everything",
            r"--full.*legacy all-source",
            r"--full.*preserves.*legacy",
        ]
        # Table form: the Modes table has a `--full` row listing Claude memory
        # + mem0 + GH Issues as side effects.
        table_pattern = r"\|.*--full.*\|.*Claude.*memory.*mem0.*GH\s*Issues"
        combined = self.text
        ok = any(
            re.search(p, combined, re.IGNORECASE | re.DOTALL) for p in sentence_patterns
        ) or re.search(table_pattern, combined, re.IGNORECASE | re.DOTALL)
        self.assertTrue(
            ok,
            "--full mode must explicitly preserve the legacy all-source "
            "behavior (Claude memory + mem0 + GH Issues); found neither "
            "in the skill.",
        )

    def test_side_effecting_phases_marked_full_only(self):
        """Phase 4 (Claude memory), Phase 5 (mem0), and Phase 7b (GH Issues)
        must each be tagged as `--full` only — otherwise the default mode
        regresses back to writing those side effects.
        """
        # Each phase heading must contain `(--full only)` or equivalent.
        for phase_num, phase_name in (
            ("Phase 4", "Claude auto-memory"),
            ("Phase 5", "mem0"),
            ("Phase 7b", "GitHub Issue"),
        ):
            # Look for a heading line that mentions the phase number/name and
            # includes the `--full only` marker.
            pattern = rf"###\s+{re.escape(phase_num)}[^#\n]*{phase_name}[^#\n]*`--full`\s*only"
            self.assertRegex(
                self.text,
                pattern,
                f"{phase_num} ({phase_name}) must be tagged as `--full` only "
                f"in the skill heading. Searched regex: {pattern}",
            )

    def test_default_mode_checklist_present(self):
        """Phase 8 must include a default-mode checklist that omits memory +
        mem0 + GH Issues items.

        We check the `[x]` (claimed-done) bullets specifically — the `[ ]`
        bullet that calls out "intentionally blank — Claude memory + mem0 +
        GH Issues are owned by `--full`" is a *meta-comment* explaining the
        omission, not a claim of work, so it's allowed to mention those
        tokens.
        """
        # The default-mode checklist should mention beads + roadmap/README +
        # learnings, but NOT mention Claude memory, mem0, or GH Issues.
        # We locate the `Default mode checklist:` block and search within it
        # up to the next blank-line-separated `**...**` header or `---`.
        body, end_idx = _extract_checklist_body(
            self.text, r"\*\*Default mode checklist:\*\*"
        )
        self.assertIsNotNone(
            body,
            "skill must include a `Default mode checklist:` block under "
            "Phase 8 — the fail-closed rule depends on it.",
        )
        # Only the [x] (done) bullets count as claimed work; the [ ] bullet
        # is an explicit non-claim.
        done_bullets = "\n".join(
            line for line in body.split("\n") if re.search(r"\[x\]", line)
        )
        self.assertIn("Beads", done_bullets)
        self.assertIn("learnings-YYYY-MM.md", done_bullets)
        self.assertIn("roadmap/README.md", done_bullets)
        # And it must NOT claim to have written the --full-only side effects.
        for forbidden in ("Claude memory", "mem0", "GH Issue"):
            self.assertNotIn(
                forbidden,
                done_bullets,
                f"default-mode checklist must not claim to write `{forbidden}` "
                f"— that is owned by --full only.",
            )

    def test_full_mode_checklist_present(self):
        """Phase 8 must include a `--full`-mode checklist that DOES mention
        Claude memory + mem0 + GH Issues.
        """
        body, end_idx = _extract_checklist_body(
            self.text, r"\*\*`--full` mode checklist:\*\*"
        )
        self.assertIsNotNone(
            body,
            "skill must include a `--full` mode checklist: block under "
            "Phase 8 — the legacy all-source behavior depends on it.",
        )
        for required in ("Beads", "Claude memory", "MEMORY.md", "mem0", "GH Issue"):
            self.assertIn(
                required,
                body,
                f"--full checklist must include `{required}` — it is part of "
                f"the legacy all-source behavior that --full preserves.",
            )


class NextstepsLooseSkillContractTest(unittest.TestCase):
    """Contract for .claude/skills/nextsteps.md — the user-scope fallback.
    Mirrors the canonical skill so /nextsteps works even if the user has not
    pulled the latest canonical version.
    """

    def setUp(self):
        # The loose file may legitimately be absent in some forks; only run
        # this test class if it exists.
        if not NEXTSTEPS_LOOSE.is_file():
            self.skipTest(f"loose skill not present at {NEXTSTEPS_LOOSE}")

        self.text = read(NEXTSTEPS_LOOSE)

    def test_loose_skill_names_both_modes(self):
        text_lower = self.text.lower()
        self.assertIn("default", text_lower)
        self.assertIn("--full", text_lower)

    def test_loose_skill_marks_side_effecting_phases_default_skip(self):
        """The loose file must say the default mode SKIPS Claude memory,
        mem0, and GH Issue creation — that's the user's whole request.
        """
        text_lower = self.text.lower()
        # Look for the explicit "skip" language tied to the side-effecting
        # phases in the default-mode section.
        # The loose file uses "Do NOT" + the phase tag.
        self.assertIn(
            "do not",
            text_lower,
            "loose skill must contain a `Do NOT` instruction tied to the "
            "side-effecting phases so the default mode skips them",
        )
        # And it must mention all three skip targets.
        for needle in ("claude auto-memory", "mem0", "gh issue"):
            self.assertIn(
                needle,
                text_lower,
                f"loose skill default-mode section must call out `{needle}` "
                f"as a phase to skip",
            )


class NextstepsModeParsingTest(unittest.TestCase):
    """Lightweight parser check: confirm the skill's documented flag-parsing
    rules actually distinguish default vs --full on a few representative
    invocations. This is not a full implementation — we just sanity-check
    that the rules as written are coherent.
    """

    def test_skill_documents_flag_parsing_rules(self):
        text = read(NEXTSTEPS_SKILL)
        # Must include explicit parsing rules: "first non-whitespace token",
        # "exactly --full", and "strip it from the brief".
        for needle in (
            "first non-whitespace token",
            "exactly `--full`",
            "strip it from the brief",
        ):
            self.assertIn(
                needle,
                text,
                f"skill must document the flag-parsing rule: `{needle}`",
            )

    def test_mode_report_examples_present(self):
        text = read(NEXTSTEPS_SKILL)
        # The Phase 8 report must start with a `Mode:` line that names the
        # chosen mode. Both default and --full examples must be present.
        self.assertIn("Mode: default", text)
        self.assertIn("Mode: --full", text)


if __name__ == "__main__":
    unittest.main()
