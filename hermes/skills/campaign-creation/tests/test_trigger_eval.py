"""
test_trigger_eval.py — Routing evaluation for the campaign-creation skill.

For every positive intent in routing-eval.jsonl, the keyword-match algorithm
must resolve it to `campaign-creation`.

Also includes a small set of negative intents (clearly unrelated phrases)
that must NOT match any campaign-creation trigger — proving the skill
isn't over-triggering.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).parent.parent.resolve()
RESOLVER = Path.home() / ".hermes" / "skills" / "RESOLVER.md"
ROUTING_EVAL = SKILL_DIR / "routing-eval.jsonl"


def extract_triggers_from_resolver() -> list[str]:
    """Read RESOLVER.md and extract the campaign-creation trigger list."""
    text = RESOLVER.read_text()
    m_heading = re.search(
        r"^##\s+campaign-creation\s+[:\-]\s*(.+)$",
        text,
        re.MULTILINE,
    )
    if m_heading and "," in m_heading.group(1):
        return [
            t.strip().lower()
            for t in m_heading.group(1).split(",")
            if t.strip()
        ]
    m_section = re.search(
        r"^##\s+campaign-creation\b([\s\S]*?)(?=^##\s+|\Z)",
        text,
        re.MULTILINE,
    )
    section = m_section.group(1)
    m_trig = re.search(r"\*\*Triggers:\*\*\s*(.+)$", section, re.MULTILINE)
    return [t.strip().lower() for t in m_trig.group(1).split(",")]


def trigger_token_sets(triggers: list[str]) -> list[set[str]]:
    """For each trigger, produce a set of significant tokens (len > 3)."""
    sets: list[set[str]] = []
    for t in triggers:
        tokens = {tok for tok in re.findall(r"[a-z0-9\-]+", t) if len(tok) > 3}
        if tokens:
            sets.append(tokens)
    return sets


def matches(intent: str, trigger_token_sets: list[set[str]]) -> bool:
    """Match rule: any trigger's tokens are a subset of intent tokens,
    OR share at least one token."""
    intent_tokens = set(re.findall(r"[a-z0-9\-]+", intent.lower()))
    return any(
        tokens.issubset(intent_tokens) or (tokens & intent_tokens)
        for tokens in trigger_token_sets
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestTriggerEval:
    def test_positive_intents_resolve_to_campaign_creation(self):
        triggers = extract_triggers_from_resolver()
        token_sets = trigger_token_sets(triggers)
        assert token_sets, "campaign-creation triggers empty"

        lines = ROUTING_EVAL.read_text().strip().splitlines()
        positive_intents = [json.loads(line)["intent"] for line in lines]
        assert len(positive_intents) >= 5

        for intent in positive_intents:
            assert matches(intent, token_sets), (
                f"Intent '{intent}' should match one of {triggers}"
            )

    def test_negative_intents_do_not_match(self):
        triggers = extract_triggers_from_resolver()
        token_sets = trigger_token_sets(triggers)

        negative_intents = [
            "what's the weather today",
            "set a 9am alarm for tomorrow",
            "translate this paragraph to French",
            "play some lo-fi music",
            "summarize the news headlines",
            "what time is it in Tokyo",
            "fix the bug in the React component",
        ]
        for intent in negative_intents:
            assert not matches(intent, token_sets), (
                f"campaign-creation is over-triggering on '{intent}'. "
                f"Triggers: {triggers}"
            )

    def test_trigger_count_is_reasonable(self):
        triggers = extract_triggers_from_resolver()
        assert 5 <= len(triggers) <= 50, (
            f"campaign-creation should declare 5-50 trigger phrases; got {len(triggers)}"
        )

    def test_triggers_are_lowercase_or_normalized(self):
        """Triggers are matched case-insensitively, so they should already
        be lowercase in the RESOLVER for consistency."""
        triggers = extract_triggers_from_resolver()
        for t in triggers:
            assert t == t.lower(), f"Trigger '{t}' should be lowercase"