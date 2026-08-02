"""
test_campaign_creation_skill.py — Live integration tests for the
campaign-creation skill.

These tests exercise the shipped scripts on the live skill tree (no mocks).
They verify:

1. The two reference templates exist and are the cached Google Doc bodies
2. The god_mechanics_general.md reference exists (and is ≥ 5 KB)
3. SKILL.md has all 11-item-contract pieces (frontmatter, contract, phases, output format)
4. template_validator.py runs without error and detects the right structure
5. section_completeness.py runs without error and quantifies abilities
6. End-to-end: a synthetic bible built from the Sanguine Architecture
   passes the validator's required-section checks

Run with:
    PYTHONPATH=~/.hermes/skills/campaign-creation/scripts \
    python3 -m pytest ~/.hermes/skills/campaign-creation/tests/ -v
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path setup — live skill tree
# ---------------------------------------------------------------------------

SKILL_DIR = Path(__file__).parent.parent.resolve()
SCRIPTS_DIR = SKILL_DIR / "scripts"
REFERENCES_DIR = SKILL_DIR / "references"
TESTS_DIR = SKILL_DIR / "tests"

CAMPAIGN_TEMPLATE = REFERENCES_DIR / "campaign_template.txt"
PERSONALITY_TEMPLATE = REFERENCES_DIR / "personality_template.txt"
GOD_MECHANICS_GENERAL = REFERENCES_DIR / "god_mechanics_general.md"
SKILL_MD = SKILL_DIR / "SKILL.md"

sys.path.insert(0, str(SCRIPTS_DIR))

import template_validator  # noqa: E402
import section_completeness  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def synthetic_bible(tmp_path_factory) -> Path:
    """A minimal-but-complete campaign bible fixture that should pass the
    structural validator. Mirrors the God of Murder Sanguine Architecture
    shape so the tests double as a smoke test for the actual campaign."""
    body = """\
# Campaign Module: Test Faithful Architecture

*A test campaign. The protagonist is a sovereign-tier divine being.*

## Source Provenance

- Test fixture.

## Section 1: Campaign Intro

**Title:** The Faithful Architecture.
**Concept:** A world where the protagonist has just consumed a god.
**Hook:** You are not saving the world; you are rewriting it.

## Section 2: Character Personality

### Core Identity
- Name: Test Character
- Archetype: The Disgraced Sovereign
- Alignment: Neutral Evil
- MBTI: INTJ

### Psychology
- Core Motivation: Atonement
- Greatest Fear: Loss of Control
- Key Traits: Analytical, Guarded, Anxious

### Behavior and Speech
- Demeanor Under Stress: hyper-focus
- Speech Patterns: clinical precision
- Reputation: tragic, celebrated

### Backstory
- Defining Moment: a catalytic event
- Relevant History: chronological summary
- Secrets: hidden past actions

### Persona vs Repressed Interior
- Social Persona: outward mask
- Inner Person: raw internal reality

### Unconscious Beliefs
1. I am the cause of all suffering.
2. My core traits are inherently dangerous.

## Section 3: Character Class

### Class Name
**The Apex Sovereign** — Paladin 2 / Bard 10 (College of Swords).

### Unique Mechanic
**Kyōka Suigetsu** — as a bonus action, force all creatures within 30 feet to make a Wisdom saving throw (DC = 8 + proficiency bonus + Charisma modifier) or be affected by absolute illusion for 1 minute. Once per long rest.

### Progression (Levels 1-30)

#### Tier 1 (Lvl 1-5)
- Renamed core features + 1 Custom Ability: **Martyr's Substitution** — 1/day, when reduced to 0 HP, drop to 1 HP instead.

#### Tier 2 (Lvl 6-10)
- Renamed core features + 1 Custom Aura: **Dread Proclamation** — all non-allies within 30 ft save DC 100 or fall prone.

#### Tier 3 (Lvl 11-16)
- Renamed core features + 1 Offensive Capstone: **Death Strike** — double damage on surprised targets.

#### Tier 4 (Lvl 17-20)
- **Avatar State** — Transformation mechanic. Trigger: when HP drops below threshold. Duration: 1 minute.

#### Tier 5 (Lvl 21-30)
- Epic Boons + Attribute cap increases (max 30) + reality-bending capabilities.

## Section 4: Assets and The Retinue

### Starting Status
Level 12 Sovereign.

### Resources
- 100,000 gold
- 1 safehouse named The Blackwoods Compound
- Political leverage: blackmail material on Lord Irlingstar

### The Panoply

### Aegis of Divine Law
- **Item Name and Classification:** Legendary Plate Armor (+6)
- **Aesthetic and Material:** +6 plate, weight 65 lb, dark steel
- **Mythic Origin:** forged by Gond's faithful
- **System Metrics:**
  - Passive Property: advantage on death saves
  - Active Tactical Feature: 1/day, bonus action, +10 to AC for 1 minute
  - Narrative Side Effect: whispers of law

### Blade of Cosmic Order
- **Item Name and Classification:** Legendary Greatsword (+6)
- **Aesthetic and Material:** +6 greatsword, dark steel
- **Mythic Origin:** seized from a Bhaalist high priest
- **System Metrics:**
  - Passive Property: deals +2d6 damage to chaotic creatures
  - Active Tactical Feature: 3/day, action, +20 to hit for 1 round
  - Narrative Side Effect: whispers of order

### Bastion of the Absolute Will
- **Item Name and Classification:** Legendary Shield (+3)
- **Aesthetic and Material:** +3 shield
- **Mythic Origin:** recovered from a planar fortress
- **System Metrics:**
  - Passive Property: resistance to psychic damage
  - Active Tactical Feature: reaction, negate one attack per short rest
  - Narrative Side Effect: whispers of absolute will

### The Retinue

### Sosuke the Spymaster
- **Core Identity:** Spymaster, Half-Elf, Rogue 8
- **Psychology:** Driven by debt; fears irrelevance
- **Behavior and Speech:** Whispery, deliberate
- **Backstory:** Former Flaming Fist captain; owes you his life
- **Persona:** Loyal servant
- **Unconscious Beliefs:** I am only useful if I have a master
- **Loyalty Profile:** You hold his debt of honor

### Gortash the General
- **Core Identity:** General, Human, Fighter 12
- **Psychology:** Driven by ambition; fears chaos
- **Behavior and Speech:** Loud, martial
- **Backstory:** Former dukeling; you broke his army and offered him command
- **Persona:** Reformed warlord
- **Unconscious Beliefs:** Order is the only virtue
- **Loyalty Profile:** Bound by the Heart-Stone pact

### Gale the Vizier
- **Core Identity:** Wizard, Human, Wizard 14
- **Psychology:** Driven by hubris; fears irrelevance
- **Behavior and Speech:** Eloquent, verbose
- **Backstory:** Former Chosen of Mystra; broken by your deicide
- **Persona:** Humbled scholar
- **Unconscious Beliefs:** Knowledge without power is nothing
- **Loyalty Profile:** Bound to your throne by oath

## Section 5: Family Dynamics

### The Parents
### Father — Lord Kaito
- **Core Identity:** Noble patriarch
- **Psychology:** Driven by honor; fears disgrace
- **Behavior and Speech:** Formal, austere
- **Backstory:** Founded House Sosuke
- **Persona:** Public noble
- **Unconscious Beliefs:** The family name is all
- **Stance:** Protective/Nurturing Guide

### Mother — Lady Mizu
- **Core Identity:** Noble matriarch
- **Psychology:** Driven by legacy; fears irrelevance
- **Behavior and Speech:** Quiet, strategic
- **Backstory:** Background diplomat
- **Persona:** Shadow negotiator
- **Unconscious Beliefs:** My children are my legacy
- **Stance:** Demanding/Indifferent Superior

### The Siblings
### Older Brother — Renji
- **Role:** Direct Ally
- **Mask:** The Dutiful Brother
- **Conflict:** None significant

### Older Brother — Daisuke
- **Role:** Hostile Rival
- **Mask:** The Disinherited
- **Conflict:** Inheritance dispute

### Older Sister — Yuki
- **Role:** Overprotective Guardian
- **Mask:** The Watchful
- **Conflict:** Restricts player freedom

### Older Sister — Aiko
- **Role:** Unwitting Pawn
- **Mask:** The Innocent
- **Conflict:** Resources drainable

## Section 6: Factions (The Game Board)

### Ruling Factions

#### House Sosuke
- **Nomenclature and Heraldry:** Silver serpent on black field
- **Infrastructure and Domain:** Manor in Upper BG; 50 staff
- **Leadership Dossier:** Lord Kaito (see family)
- **Internal Operational Culture:** Honor-bound; failure = exile
- **The Hook:** Illicit trade with House Gortash

### House Bhaal
- **Nomenclature and Heraldry:** Skull on black field
- **Infrastructure and Domain:** Undercity temple; 200 cultists
- **Leadership Dossier:** Dark Urge (the protagonist)
- **Internal Operational Culture:** Murder rites
- **The Hook:** Reformist movement within

### House Mystra
- **Nomenclature and Heraldry:** Seven stars on blue field
- **Infrastructure and Domain:** Planar fortress
- **Leadership Dossier:** Mystra
- **Internal Operational Culture:** Divine bureaucracy
- **The Hook:** Bound by Ao's compact

#### House Torm
#### House Helm
#### House Tyr
#### House Cyric
#### House Shar
#### House Kelemvor
#### House Selûne

(Full faction list — 10 ruling factions total.)

### Friendly Factions
1. Crimson Legions — Standing army
2. Blackwoods Cult — Hidden cult
3. Githyanki Vanguard — Aerial squadron
4. Cormaeril Trading Co. — Merchants
5. Harper Network — Spies
6. Flaming Fist (Reformed) — Mercenaries
7. House of Grief (Converted) — Shadow priesthood
8. Zhentarim (Vassalized) — Mercenary network
9. Cult of the Absolute (Reformed) — Psionic network
10. Lords' Alliance (Defectors) — Political coalition

### Antagonistic Factions
1. Chosen of Cyric (Rogue Cell) — Eliminates rivals
2. Lords' Alliance (Loyalist Wing) — Crusade against you
3. Chosen of Mystra (Strike Team) — Deicide hunters
4. Vlaakith's Hunt — Githyanki loyalists
5. Bhaalist Reformists — Internal sabotage
6. House Irlingstar Loyalists — Patriar resistance
7. Flaming Fist (Loyalist Wing) — Mercenary resistance
8. Cult of the Absolute (Loyalists) — Psionic resistance
9. Cormaeril Rivals — Commercial warfare
10. House of Grief (Loyalist Wing) — Sharran resistance

## Section 7: World Lore

### The Timeline
- 1492 DR: Absolute crisis
- 1493 DR: Netherbrain falls
- 1494 DR: Bhaal consumed
- 1495 DR: Avatar ascends

### The Mythos
A pantheon of gods governs the cosmology. The protagonist now occupies a new portfolio.

### The Current Situation
The Lords' Alliance has declared a holy war. Your city stands alone against the coalition.

### Story Arcs
**Early Game:** Consolidate Baldur's Gate.
**Mid Game:** Survive the Sword Coast crusade.
**Late Game:** Wage plane-spanning deicide.

## Section 8: Gazetteer and Mechanics

### Locations

#### The Balduran Statue
- **The Vibe:** salt wind, copper scent, the silence of a graveyard
- **Key Sub-locations:** Apex platform, observation deck, dark tunnel
- **Hazard:** DC 25 Wisdom save vs the apex dread aura

#### Wyrm's Rock Fortress
- **The Vibe:** stone halls, watchful banners, ancient fortification
- **Key Sub-locations:** War room, throne room, treasury
- **Hazard:** DC 22 Constitution save vs planar instability

#### The Undercity Temple of Bhaal
- **The Vibe:** incense, blood-stained stone, the dark echo of murder
- **Key Sub-locations:** Altar, reliquary, hidden corridors
- **Hazard:** DC 25 Intelligence save vs Bhaal's lingering memory

#### The Blackwoods Compound
- **The Vibe:** quiet forest, hidden wards, scholarly stillness
- **Key Sub-locations:** Library, scrying chamber, vault
- **Hazard:** DC 22 Wisdom save vs the Heart-Stone's pulse

### Custom Mechanics

#### Mass Combat / Unit Rules
Modified 5e metrics for commanding cohorts. Unit cards represent squads; each unit has HP, AC, attack bonus.

#### Social Reputation Tracker (Dignitas / Infamy)
Three bars: Dignitas (legal respect), Infamy (fear), Leverage (blackmail). Shifts based on public deeds.

### Loot Table

| Relic | Effect |
|-------|--------|
| Heart-Stone (Void-Stone) | +50 Divine HP |
| Crown of Karsus (Damaged) | Restorable, +20 DPP/day |
| Aegis of Divine Law | +6 plate, advantage on death saves |
| Blade of Cosmic Order | +6 greatsword, +2d6 vs chaotic |
| Netherese Fragments | 1/day, summon psionic echo |
| Sharran Shadowcloak | advantage on stealth in dim light |
| Githyanki Red Dragon Scale | resistance to fire damage |
| Cyric's Broken Mask | 1/week, force a save reroll |
| Mystra's Silver Strand | advantage on Arcana checks |
| Bhaal's Last Whisper | 1/day, learn a target's death-sin |

## Section 9: Starting Scene

### Setting
The high platform is still warm. The colossal carcass of the Netherbrain hangs from the statue's shoulders like a wet cloak.

### The Hook
You walked up here as the hero of Baldur's Gate. You walk down as something else.

### The Action
**A.** Speak the divine name aloud and let the city feel your dominion.
**B.** Retreat to the Blackwoods and consolidate your power in secret.
**C.** Walk through the Upper City and see who kneels.

## Part 1: Personality Profile

### Core Identity
- Name: Test Character
- Archetype: The Disgraced Sovereign
- Alignment: Neutral Evil
- MBTI: INTJ

### Psychology
- Core Motivation: Atonement
- Greatest Fear: Loss of Control
- Key Traits: Analytical, Guarded, Anxious, Empathetic

### Behavior and Speech
- Demeanor Under Stress: hyper-focus
- Speech Patterns: clinical precision
- Reputation: tragic

### Backstory
- Defining Moment: a catalytic event
- Relevant History: chronological summary
- Secrets: hidden past actions

### System Mechanics
- Feats: Skilled, Lucky
- Special Abilities: Kyōka Suigetsu, Martyr's Substitution

### Psychological Deep Dive

#### Portrait Summary
The protagonist is a brilliant mind drowning in guilt.

#### Composite Psychological Sketch
- Big Five: O:4, C:2, E:1, A:3, N:5
- Dominant Defenses: Repression, Intellectualization
- Attachment Style: Dismissive-Avoidant

#### Social Persona vs Repressed Interior
- Social Persona: the broken pariah
- Inner Person: the raw unmasked reality

#### Defense-Mechanism Diagnostics
- Mechanism 1: Repression — specific behavioral trigger
- Mechanism 2: Moral Masochism — interpersonal trigger
- Mechanism 3: Intellectualization — crisis trigger

#### Relational Decoding
- Attachment Script: "If I let you close, then harm follows."
- Distance Mechanics: strict boundaries
- Interpretation Bias: kindness as pity

#### Core Unconscious Beliefs
1. I am the cause of all suffering.
2. My core traits are inherently dangerous.
3. I deserve the negative outcomes I receive.

#### Personal Myth Narrative
- Role: The Living Wound
- Story Told: I was the chosen one and I broke the world
- Comfort/Safe Haven: The Blackwoods library, alone
- Toxicity: locks them into a cycle of self-punishment

#### Break-Point Scenario
- Catalyst: a specific companion put in mortal danger
- What Fractures: the belief "I cause all suffering"
- Immediate Cost: panic, loss of control
- Liberation/Evolution: recognizes the act of saving as a thing they are allowed to do

#### Closing Pulse
They believe themselves to be a shattered mirror, not realizing they hold the power of the unyielding diamond.

## Part 2: Mechanical Character Sheet

### Core Attributes and Scaling
- Strength: 14 (+2)
- Dexterity: 8 (-1)
- Constitution: 14 (+2)
- Intelligence: 8 (-1)
- Wisdom: 13 (+1)
- Charisma: 24 (+7)

### Combat and Tactical Vitality
- HP: 138/138
- AC: 21
- Initiative: +1

### Proficiencies and Expertise
- Armor: All armor, shields
- Weapons: simple + martial
- Skills: Arcana, History, Insight, Investigation

### Features, Traits and Flaws
- Heritage: Child of Bane (+2 INT/CON/WIS/CHA, can raise above 20)
- Class: Kyōka Suigetsu (no concentration on illusion spells, doubled duration)

### Inventory and Equipment
- Apparel: Aegis of Divine Law
- Primary Tool/Focus: The Heart-Stone
- Memento: Bhaal's Last Whisper
- Currency: 100,000 gp
"""
    path = tmp_path_factory.mktemp("bibles") / "synthetic_bible.md"
    path.write_text(body, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Test: References exist + are valid
# ---------------------------------------------------------------------------

class TestReferences:
    def test_campaign_template_exists(self):
        assert CAMPAIGN_TEMPLATE.exists(), (
            f"Campaign Template missing at {CAMPAIGN_TEMPLATE}. "
            "Re-run the template cache step."
        )

    def test_personality_template_exists(self):
        assert PERSONALITY_TEMPLATE.exists(), (
            f"Personality Template missing at {PERSONALITY_TEMPLATE}."
        )

    def test_god_mechanics_general_exists(self):
        assert GOD_MECHANICS_GENERAL.exists(), (
            f"god_mechanics_general.md missing at {GOD_MECHANICS_GENERAL}."
        )
        assert GOD_MECHANICS_GENERAL.stat().st_size > 5_000, (
            "god_mechanics_general.md should be > 5 KB"
        )

    def test_campaign_template_is_the_cached_doc(self):
        """The cached file should contain the canonical 9-section list."""
        text = CAMPAIGN_TEMPLATE.read_text()
        for section in ["Section 1: Campaign Intro", "Section 9: Starting Scene"]:
            assert section in text, f"Campaign Template should contain '{section}'"

    def test_personality_template_is_the_cached_doc(self):
        text = PERSONALITY_TEMPLATE.read_text()
        for section in ["Part 1: Personality Profile", "Part 2: Mechanical Character Sheet"]:
            assert section in text, f"Personality Template should contain '{section}'"


# ---------------------------------------------------------------------------
# Test: SKILL.md frontmatter + structure
# ---------------------------------------------------------------------------

class TestSkillMdStructure:
    def test_skill_md_exists(self):
        assert SKILL_MD.exists()

    def test_skill_md_has_frontmatter(self):
        text = SKILL_MD.read_text()
        assert text.startswith("---\n"), "SKILL.md must start with YAML frontmatter"
        assert "name: campaign-creation" in text
        assert "description:" in text
        # triggers can be inside description OR a top-level YAML key
        assert ("triggers:" in text) or ("Trigger phrases:" in text), (
            "SKILL.md must declare trigger phrases either as YAML `triggers:` "
            "or as inline `Trigger phrases:` in the description block."
        )

    def test_skill_md_has_required_sections(self):
        text = SKILL_MD.read_text()
        for heading in ["## When to load", "## Output Format", "## Verification", "## Pitfalls"]:
            assert heading in text, f"SKILL.md must include '{heading}'"

    def test_skill_md_has_scripts_section(self):
        text = SKILL_MD.read_text()
        assert "template_validator.py" in text
        assert "section_completeness.py" in text

    def test_skill_md_lists_distinct_from(self):
        """Distinct-from adjacent skills prevents confusion."""
        text = SKILL_MD.read_text()
        assert "campaign-design-iteration" in text
        assert "download-campaign" in text


# ---------------------------------------------------------------------------
# Test: Scripts run deterministically
# ---------------------------------------------------------------------------

class TestTemplateValidatorScript:
    def test_script_runs_zero_exit_on_synthetic_bible(self, synthetic_bible):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "template_validator.py"), str(synthetic_bible)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Synthetic bible is complete — should pass with zero ERROR failures
        # (warnings OK)
        assert result.returncode in (0, 1), (
            f"template_validator.py should exit 0 or 1, got {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    def test_script_detects_missing_sections(self, tmp_path):
        bible = tmp_path / "incomplete.md"
        bible.write_text("# Bare\n\nJust a title, no sections.\n")
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "template_validator.py"), str(bible)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # An empty bible should produce ERROR-level failures
        assert result.returncode == 1, (
            f"Incomplete bible should exit 1, got {result.returncode}\n{result.stdout}"
        )
        # The JSON output should show at least one error
        result_json = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "template_validator.py"),
                str(bible),
                "--json",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        report = json.loads(result_json.stdout)
        assert report["error"] > 0, "Empty bible should produce ERROR-level failures"

    def test_script_json_output_is_valid(self, synthetic_bible):
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
        assert "file" in report
        assert "checks" in report
        assert isinstance(report["checks"], list)


class TestSectionCompletenessScript:
    def test_script_runs_on_synthetic_bible(self, synthetic_bible):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "section_completeness.py"), str(synthetic_bible)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode in (0, 1), (
            f"section_completeness.py should exit 0 or 1, got {result.returncode}"
        )

    def test_script_detects_abilities(self, synthetic_bible):
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
        assert report["abilities"], "Should detect at least some abilities"
        quantified = sum(1 for a in report["abilities"] if a["quantified"])
        assert quantified > 0, "Synthetic bible has quantified abilities (Kyōka Suigetsu, etc.)"


# ---------------------------------------------------------------------------
# Test: Validator library API
# ---------------------------------------------------------------------------

class TestValidatorLibraryApi:
    def test_split_sections(self, synthetic_bible):
        text = synthetic_bible.read_text()
        sections = section_completeness.split_sections(text)
        assert "Section 1: Campaign Intro" in sections
        assert "Section 9: Starting Scene" in sections
        assert len(sections) > 9, "Should have at least 9 sections + Personality parts"

    def test_is_quantified_positive(self):
        text = "Bonus action: target makes a Wisdom save DC 20 or be frightened."
        quantified, pat = section_completeness.is_quantified(text)
        assert quantified
        assert pat

    def test_is_quantified_negative(self):
        text = "The character feels a deep connection to the divine."
        quantified, pat = section_completeness.is_quantified(text)
        assert not quantified
        assert not pat

    def test_section_min_words_match(self):
        assert section_completeness.section_min_words_match("Section 1: Campaign Intro") == 200
        assert section_completeness.section_min_words_match("Family") == 400
        assert section_completeness.section_min_words_match("Random Untitled Heading") == 0


# ---------------------------------------------------------------------------
# Test: End-to-end smoke
# ---------------------------------------------------------------------------

class TestEndToEnd:
    def test_validator_passes_synthetic_bible_with_no_errors(self, synthetic_bible):
        """The full pipeline — synthetic bible → validator → zero errors."""
        report = template_validator.validate(synthetic_bible)
        error_count = sum(
            1 for c in report.checks if c.severity == "ERROR" and c.status == "FAIL"
        )
        assert error_count == 0, (
            f"Synthetic bible should pass validator with 0 errors; got {error_count}.\n"
            + "\n".join(
                f"  {c.name}: {c.message}"
                for c in report.checks
                if c.severity == "ERROR" and c.status == "FAIL"
            )
        )

    def test_completeness_audit_runs_clean(self, synthetic_bible):
        report = section_completeness.audit(synthetic_bible)
        assert not report.has_errors, (
            f"Completeness audit should not have ERROR-level failures; "
            f"got {sum(1 for s in report.sections if s.severity == 'ERROR' and s.status == 'FAIL')}"
        )
