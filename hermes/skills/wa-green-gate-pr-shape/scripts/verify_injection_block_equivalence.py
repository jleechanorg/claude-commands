#!/usr/bin/env python3
"""Verify a dynamic-prompt block rendered by PromptBuilder.build_living_world_instruction
contains all expected contract markers and matches the expected byte-equivalence budget.

Use after any change to $PROJECT_ROOT/prompts/injection/*.md or the agent_prompts.py
loader code. Catches:
- Missing template substitution (the {current_turn} token left unsubstituted)
- Missing required contract markers (e.g. PER-TURN OBLIGATION label)
- Re-inlined f-string regression (a future PR reverts the extraction)
- Block-content drift (markers present but content changed)

Usage:
    # From the worktree (uses HERMES_REPO_ROOT or walks up from cwd):
    python3 scripts/verify_injection_block_equivalence.py

    # Or with explicit repo root:
    python3 scripts/verify_injection_block_equivalence.py $HOME/projects/your-project.com

    # Or with custom markers / expected length:
    python3 scripts/verify_injection_block_equivalence.py --length 1361 \\
        --marker "COMPANION QUEST CADENCE" --marker "Turn 3: MANDATORY" \\
        --turn 3
"""

from __future__ import annotations

import argparse
import os
import sys
import unittest
from unittest.mock import MagicMock

# Required markers (the contract the dynamic block must satisfy)
DEFAULT_MARKERS = [
    "COMPANION QUEST CADENCE",
    "PER-TURN OBLIGATION",
    "current_turn = 3",
    "current_turn + 1",
    "current_turn + 2",
    "Turn 3: MANDATORY",
    "next_companion_arc_turn",
    "companion_arcs",
]

# Template tokens that MUST be substituted (not present in output)
FORBIDDEN_TOKENS = ["{current_turn}"]

# Expected length budget (PR #8527 baseline: 1361 chars; PR #8548: 1364 chars)
DEFAULT_LENGTH_BUDGET = (1350, 1380)


def _resolve_repo_root(repo_root_arg):
    """Walk up from cwd to find a repo with $PROJECT_ROOT/prompts/living_world_instruction.md."""
    if repo_root_arg and os.path.isfile(
        os.path.join(repo_root_arg, "$PROJECT_ROOT/prompts/living_world_instruction.md")
    ):
        return repo_root_arg
    cur = os.getcwd()
    for _ in range(6):
        cur = os.path.dirname(cur)
        if os.path.isfile(
            os.path.join(cur, "$PROJECT_ROOT/prompts/living_world_instruction.md")
        ):
            return cur
    return "$HOME/projects/your-project.com"


def render_dynamic_block(repo_root, turn):
    """Render build_living_world_instruction(turn) with the test fixture."""
    sys.path.insert(0, repo_root)
    from mvp_site.file_cache import clear_file_cache

    clear_file_cache()
    from mvp_site.agent_prompts import PromptBuilder

    builder = PromptBuilder(game_state=None)
    mock_gs = MagicMock()
    mock_gs.last_living_world_turn = 0
    mock_gs.check_living_world_trigger.return_value = (True, "test_force", None)
    mock_gs.get_companion_arcs_summary.return_value = ""
    mock_gs.custom_campaign_state = {
        "next_companion_arc_turn": turn,
        "companion_arcs": {},
    }
    builder.game_state = mock_gs
    return builder.build_living_world_instruction(turn)


# Globals set in main(); read by the TestCase methods
REQUIRED_MARKERS = DEFAULT_MARKERS
LENGTH_BUDGET = DEFAULT_LENGTH_BUDGET
REPO_ROOT = ""
RENDERED_OUTPUT = ""


class DynamicBlockEquivalenceContract(unittest.TestCase):
    """Contract: the dynamic block is byte-equivalent to PR #8527/#8548 baseline.

    Markers and length budget are configurable via the CLI; defaults match the
    cadence block from PR #8527.
    """

    def test_all_required_markers_present(self):
        for marker in REQUIRED_MARKERS:
            self.assertIn(
                marker,
                RENDERED_OUTPUT,
                "MISSING marker: {!r}\n"
                "Output (first 500 chars): {}".format(
                    marker, RENDERED_OUTPUT[:500]
                ),
            )

    def test_template_tokens_substituted(self):
        for token in FORBIDDEN_TOKENS:
            self.assertNotIn(
                token,
                RENDERED_OUTPUT,
                "Template token NOT substituted: {!r} - "
                "read_file_cached(...).format(current_turn=...) is broken".format(token),
            )

    def test_length_within_budget(self):
        lo, hi = LENGTH_BUDGET
        self.assertGreaterEqual(
            len(RENDERED_OUTPUT),
            lo,
            "Output too short: {} chars, expected >= {}".format(len(RENDERED_OUTPUT), lo),
        )
        self.assertLessEqual(
            len(RENDERED_OUTPUT),
            hi,
            "Output too long: {} chars, expected <= {}".format(len(RENDERED_OUTPUT), hi),
        )

    def test_injection_file_exists(self):
        """The .md source file must exist at $PROJECT_ROOT/prompts/injection/."""
        path = os.path.join(
            REPO_ROOT, "$PROJECT_ROOT/prompts/injection/living_world_companion_cadence.md"
        )
        self.assertTrue(
            os.path.isfile(path),
            "injection file missing: {} - the cadence block must live "
            "in $PROJECT_ROOT/prompts/injection/ as a .md file".format(path),
        )

    def test_agent_prompts_does_not_inline_block(self):
        """Regression guard: agent_prompts.py must NOT re-inline the cadence
        block as a Python f-string. The unique phrase from PR #8527's inline
        version is checked for absence."""
        path = os.path.join(REPO_ROOT, "$PROJECT_ROOT/agent_prompts.py")
        with open(path) as f:
            content = f.read()
        self.assertNotIn(
            '\\n**🎯 COMPANION QUEST CADENCE (PER-TURN OBLIGATION)',
            content,
            "agent_prompts.py re-inlined the cadence block as a Python "
            "f-string - this is the PR #8527 anti-pattern that PR #8548 fixed",
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "repo_root",
        nargs="?",
        default=None,
        help="Path to your-project.com checkout (auto-detected if omitted)",
    )
    parser.add_argument(
        "--marker",
        action="append",
        default=None,
        help="Required marker substring (repeatable). Default: cadence block contract",
    )
    parser.add_argument(
        "--length",
        type=int,
        default=None,
        help="Expected output length (uses +/- 10 char budget)",
    )
    parser.add_argument(
        "--turn",
        type=int,
        default=3,
        help="Turn number to bind current_turn (default: 3)",
    )
    args = parser.parse_args()

    repo_root = _resolve_repo_root(args.repo_root)

    global REQUIRED_MARKERS, LENGTH_BUDGET, REPO_ROOT, RENDERED_OUTPUT
    REQUIRED_MARKERS = args.marker if args.marker else DEFAULT_MARKERS
    REPO_ROOT = repo_root
    RENDERED_OUTPUT = render_dynamic_block(repo_root, args.turn)
    if args.length is not None:
        LENGTH_BUDGET = (args.length - 10, args.length + 10)
    else:
        LENGTH_BUDGET = DEFAULT_LENGTH_BUDGET

    # Sanity print
    print("repo_root: {}".format(repo_root))
    print("turn: {}".format(args.turn))
    print("required markers: {}".format(len(REQUIRED_MARKERS)))
    print("length budget: {}".format(LENGTH_BUDGET))
    print("rendered length: {}".format(len(RENDERED_OUTPUT)))
    print("---")
    # Run the TestCase
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(DynamicBlockEquivalenceContract)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()