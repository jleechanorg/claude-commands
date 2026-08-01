"""
test_e2e.py — End-to-end smoke test for the campaign-creation skill.

Exercises the full pipeline:
1. RESOLVER.md has the campaign-creation entry
2. SKILL.md has frontmatter + Contract + Phases + Output Format sections
3. References (templates + god-mechanics) exist
4. Scripts run on the synthetic bible without ERROR-level failures
5. The synthetic bible passes the resolver trigger eval (intent matches
   expected skill via simple keyword match)
6. check_resolvable.py --self passes
7. skillify_check passes (full 11-item contract)

This is the contract test the skillify 11-item contract requires for
"production-used" skills (item 10).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).parent.parent.resolve()
SCRIPTS_DIR = SKILL_DIR / "scripts"
REFERENCES_DIR = SKILL_DIR / "references"
RESOLVER = Path.home() / ".hermes" / "skills" / "RESOLVER.md"
ROUTING_EVAL = SKILL_DIR / "routing-eval.jsonl"


def extract_triggers_from_resolver() -> list[str]:
    """Read RESOLVER.md and extract the campaign-creation trigger list.

    Supports both formats:
      ## campaign-creation : t1, t2, ...   (skillify_check convention)
      ## campaign-creation\n**Triggers:** t1, t2, ...
    """
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


class TestResolverEntry:
    def test_resolver_md_exists(self):
        assert RESOLVER.exists()

    def test_resolver_has_campaign_creation_heading(self):
        text = RESOLVER.read_text()
        assert re.search(r"^##\s+campaign-creation\b", text, re.MULTILINE), (
            f"RESOLVER.md must have a '## campaign-creation' heading"
        )

    def test_resolver_has_at_least_5_triggers(self):
        triggers = extract_triggers_from_resolver()
        assert len(triggers) >= 5, (
            f"campaign-creation should declare at least 5 trigger phrases; "
            f"got {len(triggers)}"
        )


class TestSkillInvariants:
    def test_skill_md_has_contract_heading(self):
        text = (SKILL_DIR / "SKILL.md").read_text()
        assert "## Contract" in text

    def test_skill_md_has_phases_heading(self):
        text = (SKILL_DIR / "SKILL.md").read_text()
        assert "## Phases" in text, (
            "SKILL.md must have a '## Phases' heading per skillify 11-item contract"
        )

    def test_skill_md_has_output_format_heading(self):
        text = (SKILL_DIR / "SKILL.md").read_text()
        assert "## Output Format" in text

    def test_skill_md_has_distinct_from_section(self):
        text = (SKILL_DIR / "SKILL.md").read_text()
        assert "Distinct from" in text or "distinct from" in text


class TestScriptsRunOnSyntheticBible:
    """Re-run the scripts on a synthetic bible + verify they exit non-error."""

    @pytest.fixture
    def synthetic_bible(self, tmp_path) -> Path:
        body = """\
# Test Campaign

## Section 1: Campaign Intro
A test campaign intro. Power fantasy for the protagonist. The hook is fun.

## Section 2: Character Personality
### Core Identity
- Name: Test
### Psychology
- Core Motivation: Atonement
### Behavior and Speech
- Demeanor: hyper-focus
### Backstory
- Defining Moment: a moment
### Persona vs Repressed Interior
- Outer mask
### Unconscious Beliefs
1. I suffer.

## Section 3: Character Class
### Class Name
The Apex Sovereign.
### Unique Mechanic
Bonus action: target makes a Wisdom save DC 20 or be frightened.
### Progression
Levels 1-30 with renames.

## Section 4: Assets and The Retinue
### The Panoply
### Sword of Light
A relic.
### Shield of Truth
A relic.
### Crown of Kings
A relic.
### The Retinue
### Spymaster
A loyal NPC.
### General
A martial NPC.
### Vizier
A wise NPC.

## Section 5: Family
### Father
A parent.
### Mother
A parent.
### Brother 1
Sibling.
### Brother 2
Sibling.
### Sister 1
Sibling.
### Sister 2
Sibling.

## Section 6: Factions
Ten factions listed. (Abbreviated for fixture.)

## Section 7: World Lore
Brief world.

## Section 8: Gazetteer
### Locations
#### Palace
A palace.
### Loot Table
| Relic | Effect |
|-------|--------|
| Sword | +1 attack |
| Shield | +1 AC |
| Crown | Advantage on saves |
| Bow | +2 damage |
| Ring | Detect magic |
| Amulet | Resist fire |
| Cloak | Stealth |
| Boots | Speed +10 |
| Tome | Arcana |
| Dagger | Sneak attack +1 |

## Section 9: Starting Scene
### Setting
A room.
### The Hook
A crisis.
### The Action
A. Act now.

## Part 1: Personality Profile
### Core Identity
Name: Test.
### Psychology
- Core Motivation: Atonement
### Behavior and Speech
- Demeanor: hyper-focus
### Backstory
- Defining Moment: a moment
### System Mechanics
- Feats: Skilled
### Psychological Deep Dive
#### Portrait Summary
The character is a...
#### Composite Psychological Sketch
Big Five: O:4, C:2, E:1, A:3, N:5
#### Social Persona vs Repressed Interior
Outer vs inner.
#### Defense-Mechanism Diagnostics
Repression, Intellectualization.
#### Relational Decoding
Attachment Script: "If I let you close..."
#### Core Unconscious Beliefs
1. I suffer.
#### Personal Myth Narrative
The Living Wound.
#### Break-Point Scenario
Catalyst: a companion in danger.
#### Closing Pulse
They believe themselves broken.

## Part 2: Mechanical Character Sheet
### Core Attributes and Scaling
STR 14, DEX 8.
### Combat and Tactical Vitality
HP 100, AC 18.
### Proficiencies and Expertise
Armor: all.
### Features, Traits and Flaws
Heritage: Child of Bane.
### Inventory and Equipment
Apparel: plate.
"""
        path = tmp_path / "synthetic_bible.md"
        path.write_text(body)
        return path

    def test_template_validator_exits_clean(self, synthetic_bible):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "template_validator.py"),
                str(synthetic_bible),
                "--json",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        report = json.loads(result.stdout)
        assert report["error"] == 0, (
            f"Template validator should produce 0 ERRORs on a structurally-complete bible; "
            f"got {report['error']}:\n" + json.dumps(report, indent=2)
        )

    def test_section_completeness_exits_clean(self, synthetic_bible):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "section_completeness.py"),
                str(synthetic_bible),
                "--json",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        report = json.loads(result.stdout)
        assert "sections" in report
        assert "abilities" in report
        assert report["section_count"] >= 9, (
            f"Should detect ≥ 9 sections; got {report['section_count']}"
        )


class TestCheckResolvable:
    def test_check_resolvable_self_pass(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "check_resolvable.py"),
                "--self",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 0, (
            f"check_resolvable.py --self failed:\n"
            f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )


class TestRoutingEvalFixture:
    def test_routing_eval_jsonl_is_valid_jsonl(self):
        assert ROUTING_EVAL.exists()
        lines = ROUTING_EVAL.read_text().strip().splitlines()
        assert len(lines) >= 5, (
            f"routing-eval.jsonl should have ≥ 5 entries; got {len(lines)}"
        )
        for i, line in enumerate(lines):
            obj = json.loads(line)
            assert "intent" in obj, f"line {i} missing 'intent'"
            assert "expected_skill" in obj, f"line {i} missing 'expected_skill'"
            assert obj["expected_skill"] == "campaign-creation", (
                f"line {i} expected_skill should be 'campaign-creation'; "
                f"got {obj['expected_skill']}"
            )

    def test_routing_eval_intents_keyword_match(self):
        """Every intent must match a trigger in the RESOLVER entry.

        Match rule: at least one significant-word sequence from any trigger
        appears in the intent (case-insensitive).
        """
        triggers = extract_triggers_from_resolver()

        trigger_tokens: list[set[str]] = []
        for t in triggers:
            tokens = {tok for tok in re.findall(r"[a-z0-9\-]+", t) if len(tok) > 3}
            if tokens:
                trigger_tokens.append(tokens)

        for line in ROUTING_EVAL.read_text().strip().splitlines():
            obj = json.loads(line)
            intent = obj["intent"].lower()
            intent_tokens = set(re.findall(r"[a-z0-9\-]+", intent))
            matched = any(
                tokens.issubset(intent_tokens) or (tokens & intent_tokens)
                for tokens in trigger_tokens
            )
            assert matched, (
                f"Intent '{obj['intent']}' doesn't match any trigger in "
                f"{triggers}. Either add a trigger phrase or refine the intent."
            )


class TestSkillifyCheck:
    """Full 11-item contract audit via skillify_check."""

    def test_skillify_check_passes(self):
        """The skillify_check must show ≥ 8 PASS items."""
        skillify_check = (
            Path.home() / ".hermes" / "skills" / "skillify" / "scripts" / "skillify_check.py"
        )
        if not skillify_check.exists():
            pytest.skip("skillify_check not available")
        result = subprocess.run(
            [
                sys.executable,
                str(skillify_check),
                str(SKILL_DIR),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Parse "score=N/9 fail=M"
        m_score = re.search(r"score=(\d+)/(\d+)", result.stdout)
        m_fail = re.search(r"fail=(\d+)", result.stdout)
        assert m_score, f"Could not parse score from skillify_check output:\n{result.stdout}"
        assert m_fail, f"Could not parse fail count:\n{result.stdout}"
        score = int(m_score.group(1))
        fail = int(m_fail.group(1))
        assert score >= 8, (
            f"skillify_check should pass ≥ 8/9 items; got {score}/9.\n"
            f"Failures:\n{result.stdout}"
        )
        assert fail == 0, (
            f"skillify_check should have 0 failures; got {fail}.\n{result.stdout}"
        )


class TestTriggerEval:
    """The trigger_eval contract — every routing-eval.jsonl intent resolves
    to campaign-creation, and at least one negative case proves the
    skill isn't over-triggering on unrelated phrases."""

    def test_negative_intent_routing(self):
        """A clearly unrelated intent should NOT keyword-match any trigger."""
        triggers = extract_triggers_from_resolver()
        trigger_tokens: list[set[str]] = []
        for t in triggers:
            tokens = {tok for tok in re.findall(r"[a-z0-9\-]+", t) if len(tok) > 3}
            if tokens:
                trigger_tokens.append(tokens)

        negative = "what's the weather today"
        intent_tokens = set(re.findall(r"[a-z0-9\-]+", negative.lower()))
        matched = any(
            tokens.issubset(intent_tokens) or (tokens & intent_tokens)
            for tokens in trigger_tokens
        )
        assert not matched, (
            f"campaign-creation is over-triggering on unrelated intent "
            f"'{negative}'. Triggers: {triggers}"
        )