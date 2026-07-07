#!/usr/bin/env python3
"""Resolver trigger eval for browser-headless-default.

Feeds the canonical user trigger phrases (and adjacent decoys) through a substring
match against `~/.hermes_prod/skills/RESOLVER.md`. Asserts the headless-default entry
is the closest match for headless-policy phrases and does NOT absorb playwright /
browserclaw / general browser traffic.
"""
from __future__ import annotations

import pathlib
import re
import unittest

RESOLVER = pathlib.Path("$HOME/.hermes_prod/skills/RESOLVER.md")
SKILL_NAME = "browser-headless-default"

# Triggers the user actually types — must route to browser-headless-default
SHOULD_ROUTE = [
    "headless browser",
    "hide browser",
    "browser mode",
    "chrome mode",
    "headed mode forbidden",
    "show browser denied",
    "browser headless policy",
    "no visible chrome",
]

# Adjacent skills that share keywords — must NOT absorb these. Each tuple is
# (expected_skill_name, exact_trigger_phrase_as_listed_in_resolver).
SHOULD_NOT_ROUTE = [
    ("browserclaw", "browserclaw"),
    ("browserclaw", "capture browser traffic"),
    ("browserclaw", "playwright"),
    ("antigravity-computer-use", "antigravity"),
    ("antigravity-computer-use", "control google"),
]


def _load_sections() -> dict[str, list[str]]:
    """Return {skill_name: [trigger phrases]} from RESOLVER.md.

    Triggers are comma-separated within a `**Triggers:** a, b, c` line.
    """
    if not RESOLVER.exists():
        raise SystemExit(f"RESOLVER.md missing: {RESOLVER}")
    text = RESOLVER.read_text()
    sections: dict[str, list[str]] = {}
    current = None
    for raw in text.splitlines():
        h = re.match(r"^##\s+(\S+)", raw.strip())
        if h:
            current = h.group(1)
            sections.setdefault(current, [])
            continue
        if current is not None and "Triggers:" in raw:
            tail = raw.split("Triggers:", 1)[1]
            for phrase in tail.split(","):
                phrase = phrase.strip().strip("`*")
                if phrase:
                    sections[current].append(phrase)
    return sections


class ResolverRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sections = _load_sections()
        assert SKILL_NAME in cls.sections, f"missing resolver entry for {SKILL_NAME}"

    def test_skill_present_in_resolver(self):
        self.assertIn(SKILL_NAME, self.sections)

    def test_all_documented_triggers_resolve(self):
        for phrase in SHOULD_ROUTE:
            with self.subTest(phrase=phrase):
                hits = [
                    name
                    for name, triggers in self.sections.items()
                    if any(phrase.lower() in t.lower() for t in triggers)
                ]
                self.assertIn(
                    SKILL_NAME,
                    hits,
                    f"phrase '{phrase}' did not route to {SKILL_NAME}; hits={hits}",
                )

    def test_decoy_phrases_route_to_correct_skill(self):
        for expected_skill, phrase in SHOULD_NOT_ROUTE:
            with self.subTest(phrase=phrase, expected=expected_skill):
                hits = [
                    name
                    for name, triggers in self.sections.items()
                    if any(phrase.lower() in t.lower() for t in triggers)
                ]
                self.assertIn(
                    expected_skill,
                    hits,
                    f"decoy '{phrase}' failed to route to {expected_skill}",
                )
                # Must not also collide with headless-default
                self.assertNotIn(
                    SKILL_NAME,
                    hits,
                    f"headless-default absorbed decoy '{phrase}'",
                )


if __name__ == "__main__":
    unittest.main()
