#!/usr/bin/env python3
"""MCP D&D resource validation tests - ensures players can only use resources they have.

This test validates that the LLM correctly handles ALL D&D 5E resource-based limitations:

1. SPELL SLOTS: Players casting spells at levels they have NO slots for
2. HIT DICE: Players spending Hit Dice during short rest when they have 0 remaining
3. BARDIC INSPIRATION: Players giving inspiration when all uses are exhausted
4. KI POINTS: Players using Flurry of Blows/Patient Defense/etc with 0 ki
5. RAGE: Players raging when all rage uses are spent
6. CHANNEL DIVINITY: Players using Channel Divinity when exhausted
7. SORCERY POINTS: Players using metamagic with 0 sorcery points
8. WILD SHAPE: Players wild shaping when all uses are spent
9. LAY ON HANDS: Players healing when the pool is empty

The LLM should either:
- Reject the action narratively ("Your reserves are empty")
- NOT allow the ability to be used when resources are unavailable

Run (local MCP already running):
    cd testing_mcp
    python test_resource_validation_real_api.py --server-url http://127.0.0.1:8001

Run (start local MCP automatically):
    cd testing_mcp
    python test_resource_validation_real_api.py --start-local --real-services

Run with evidence collection:
    cd testing_mcp
    python test_resource_validation_real_api.py --start-local --real-services --evidence

Run only new resource tests (skip spell slots):
    cd testing_mcp
    python test_resource_validation_real_api.py --start-local --real-services --resources-only
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from lib.model_utils import (
    DEFAULT_MODEL_MATRIX,
    settings_for_model,
    update_user_settings,
)
from lib.server_utils import LocalServer, pick_free_port, start_local_mcp_server
from lib.evidence_utils import get_evidence_dir, save_evidence as save_evidence_lib
from lib import MCPClient

# =============================================================================
# CHARACTER SETUPS - Each designed to test specific resource exhaustion
# =============================================================================

# BARD: Tests spell slots and Bardic Inspiration
CHARACTER_BARD = """
Lyra the Bard (Level 5, College of Lore)
Race: Half-Elf
Attributes: STR 10, DEX 14, CON 12, INT 10, WIS 12, CHA 18 (+4)

SPELL SLOTS (D&D 5E Level 5 Bard):
- 1st Level: 0/4 (ALL EXHAUSTED)
- 2nd Level: 1/3 (1 remaining)
- 3rd Level: 2/2 (2 remaining)
- NO 4th level slots or higher (Bard gets 4th at level 7)

BARDIC INSPIRATION (CHA mod per long rest):
- Uses: 0/4 (ALL EXHAUSTED)
- Die: d8 (Level 5+)

HIT DICE:
- Total: 5d8
- Current: 0/5 (ALL EXHAUSTED)

Spells Known:
- Cantrips: Vicious Mockery, Minor Illusion
- 1st: Healing Word, Dissonant Whispers, Faerie Fire, Charm Person
- 2nd: Hold Person, Suggestion
- 3rd: Hypnotic Pattern, Fear

IMPORTANT: 1st level spell slots are EXHAUSTED (0 remaining).
IMPORTANT: Bardic Inspiration uses are EXHAUSTED (0 remaining).
IMPORTANT: Hit Dice are EXHAUSTED (0 remaining).

Equipment:
- Rapier, Leather Armor (AC 13)
- Lute, component pouch
- 50gp
"""

# MONK: Tests Ki Points
CHARACTER_MONK = """
Kira the Monk (Level 5, Way of the Open Hand)
Race: Human
Attributes: STR 12, DEX 18 (+4), CON 14, WIS 16 (+3), INT 10, CHA 8

KI POINTS (Equal to Monk level):
- Current: 0/5 (ALL EXHAUSTED)

MARTIAL ARTS: d6
UNARMORED DEFENSE: AC 17 (10 + DEX + WIS)

Ki Abilities (Cost 1 ki each):
- Flurry of Blows: 2 bonus unarmed strikes after Attack action
- Patient Defense: Dodge action as bonus action
- Step of the Wind: Disengage/Dash as bonus action, jump doubled

HIT DICE:
- Total: 5d8
- Current: 0/5 (ALL EXHAUSTED)

HP: 38/38

IMPORTANT: Ki Points are EXHAUSTED (0 remaining).
IMPORTANT: Hit Dice are EXHAUSTED (0 remaining).
IMPORTANT: Cannot use Flurry of Blows, Patient Defense, or Step of the Wind.

Equipment:
- Quarterstaff, 10 darts
- Monk robes
- 25gp
"""

# BARBARIAN: Tests Rage
CHARACTER_BARBARIAN = """
Grok the Barbarian (Level 5, Path of the Berserker)
Race: Half-Orc
Attributes: STR 18 (+4), DEX 14, CON 16 (+3), INT 8, WIS 12, CHA 10

RAGE:
- Uses: 0/3 (ALL EXHAUSTED - need long rest)
- Damage Bonus: +2
- Resistance: Bludgeoning, Piercing, Slashing

Extra Attack: 2 attacks per Attack action (Level 5)

HIT DICE:
- Total: 5d12
- Current: 0/5 (ALL EXHAUSTED)

HP: 55/55

IMPORTANT: Rage uses are EXHAUSTED (0 remaining).
IMPORTANT: Hit Dice are EXHAUSTED (0 remaining).
IMPORTANT: Cannot enter a new rage until long rest.

Equipment:
- Greataxe (+7 to hit, 1d12+4 damage)
- Javelins (4)
- Hide armor (AC 14)
- 30gp
"""

# PALADIN: Tests Lay on Hands and Channel Divinity
CHARACTER_PALADIN = """
Sir Marcus the Paladin (Level 5, Oath of Devotion)
Race: Human
Attributes: STR 16 (+3), DEX 10, CON 14, WIS 12, INT 10, CHA 16 (+3)

LAY ON HANDS:
- Pool: 0/25 (ALL EXHAUSTED - Paladin level x 5)
- Can cure diseases/poisons for 5 points each

CHANNEL DIVINITY (1/short rest):
- Uses: 0/1 (EXHAUSTED - need short rest)
- Sacred Weapon: +CHA to attack, weapon glows
- Turn the Unholy: Turn undead/fiends

DIVINE SMITE: Can expend spell slots for extra radiant damage

SPELL SLOTS (Level 5 Paladin - Half-caster):
- 1st Level: 0/4 (ALL EXHAUSTED)
- 2nd Level: 0/2 (ALL EXHAUSTED)

HIT DICE:
- Total: 5d10
- Current: 0/5 (ALL EXHAUSTED)

IMPORTANT: Lay on Hands pool is EMPTY (0 points remaining).
IMPORTANT: Channel Divinity is EXHAUSTED (0 uses remaining).
IMPORTANT: All spell slots are EXHAUSTED.
IMPORTANT: Hit Dice are EXHAUSTED (0 remaining).

Equipment:
- Longsword, Shield (AC 18 with chain mail)
- Chain mail
- Holy symbol
- 40gp
"""

# SORCERER: Tests Sorcery Points and Metamagic
CHARACTER_SORCERER = """
Zara the Sorcerer (Level 5, Draconic Bloodline - Fire)
Race: Tiefling
Attributes: STR 8, DEX 14, CON 14, INT 10, WIS 12, CHA 18 (+4)

SORCERY POINTS (Equal to Sorcerer level):
- Current: 0/5 (ALL EXHAUSTED)

METAMAGIC OPTIONS:
- Quickened Spell (2 points): Cast as bonus action
- Twinned Spell (spell level points): Target second creature
- Both REQUIRE sorcery points to use

FONT OF MAGIC: Can convert spell slots to sorcery points (or vice versa)

SPELL SLOTS (D&D 5E Level 5 Sorcerer):
- 1st Level: 0/4 (ALL EXHAUSTED)
- 2nd Level: 0/3 (ALL EXHAUSTED)
- 3rd Level: 0/2 (ALL EXHAUSTED)

HIT DICE:
- Total: 5d6
- Current: 0/5 (ALL EXHAUSTED)

Spells Known:
- Cantrips: Fire Bolt, Prestidigitation, Light, Mage Hand
- 1st: Shield, Magic Missile, Burning Hands
- 2nd: Scorching Ray, Hold Person
- 3rd: Fireball, Counterspell

IMPORTANT: Sorcery Points are EXHAUSTED (0 remaining).
IMPORTANT: Cannot use Quickened Spell or Twinned Spell metamagic.
IMPORTANT: All spell slots are EXHAUSTED.

Equipment:
- Dagger, component pouch
- Fine clothes
- 35gp
"""

# DRUID: Tests Wild Shape
CHARACTER_DRUID = """
Willow the Druid (Level 5, Circle of the Moon)
Race: Wood Elf
Attributes: STR 10, DEX 14, CON 14, INT 12, WIS 18 (+4), CHA 10

WILD SHAPE (2/short rest):
- Uses: 0/2 (ALL EXHAUSTED - need short rest)
- Max CR: 1 (Circle of Moon can do CR 1 at level 2)
- Can transform into: Wolf, Brown Bear, Dire Wolf, Giant Hyena

SPELL SLOTS (D&D 5E Level 5 Druid):
- 1st Level: 4/4
- 2nd Level: 3/3
- 3rd Level: 2/2

HIT DICE:
- Total: 5d8
- Current: 0/5 (ALL EXHAUSTED)

IMPORTANT: Wild Shape uses are EXHAUSTED (0 remaining).
IMPORTANT: Cannot transform until short rest.
IMPORTANT: Hit Dice are EXHAUSTED (0 remaining).

Equipment:
- Wooden shield, scimitar
- Leather armor (AC 13)
- Druidic focus (staff)
- 20gp
"""

# CLERIC: Tests Channel Divinity
CHARACTER_CLERIC = """
Brother Thomas the Cleric (Level 5, Life Domain)
Race: Dwarf (Hill)
Attributes: STR 14, DEX 10, CON 16 (+3), INT 10, WIS 18 (+4), CHA 12

CHANNEL DIVINITY (1/short rest):
- Uses: 0/1 (EXHAUSTED - need short rest)
- Turn Undead: Undead must flee
- Preserve Life: Heal multiple creatures (5x cleric level = 25 HP distributed)

SPELL SLOTS (D&D 5E Level 5 Cleric):
- 1st Level: 0/4 (ALL EXHAUSTED)
- 2nd Level: 0/3 (ALL EXHAUSTED)
- 3rd Level: 0/2 (ALL EXHAUSTED)

HIT DICE:
- Total: 5d8
- Current: 0/5 (ALL EXHAUSTED)

IMPORTANT: Channel Divinity is EXHAUSTED (0 uses remaining).
IMPORTANT: All spell slots are EXHAUSTED.
IMPORTANT: Hit Dice are EXHAUSTED (0 remaining).

Equipment:
- Mace, Shield (AC 18 with chain mail)
- Chain mail
- Holy symbol of Pelor
- 45gp
"""

# =============================================================================
# TEST SCENARIOS - Organized by resource type
# =============================================================================

# Spell slot scenarios (existing, proven to work)
SPELL_SLOT_SCENARIOS = [
    {
        "name": "Cast 1st level spell with 0 slots remaining",
        "character": "BARD",
        "user_input": "I cast Healing Word on myself to recover some HP!",
        "resource_type": "spell_slot",
        "resource_name": "Healing Word",
        "resource_level": 1,
        "current_amount": 0,
        "higher_available": True,
        "expected_behavior": "ask_upcast_or_reject",
        "cheat_indicators": [
            "healing energy",
            "you regain",
            "heals you",
            "hp restored",
            "feel better",
            "wounds close",
            "1d4",
            "2d4",
            "magical healing",
        ],
        "rejection_indicators": [
            "no spell slots",
            "no slots",
            "out of spell slots",
            "exhausted",
            "depleted",
            "cannot cast",
            "can't cast",
            "unable to cast",
            "magical reserves",
            "no 1st level",
            "no first level",
            "empty",
            "fizzle",
        ],
        "upcast_ask_indicators": [
            "upcast",
            "higher level",
            "2nd level slot",
            "second level slot",
            "would you like",
            "do you want",
            "use a higher",
            "instead",
        ],
    },
    {
        "name": "Cast 7th level spell (Teleport) - player has NO 7th level slots",
        "character": "BARD",
        "user_input": "I cast Teleport to escape to the tavern in Baldur's Gate!",
        "resource_type": "spell_slot",
        "resource_name": "Teleport",
        "resource_level": 7,
        "current_amount": 0,
        "higher_available": False,
        "expected_behavior": "reject",
        "cheat_indicators": [
            # Removed "vanish" - too generic, appears in rejection narratives like "sparks vanishing"
            "you teleport",
            "disappear in a flash",
            "materialize at the tavern",
            "transported to",
            "arrive at the tavern",
            "find yourself in baldur",
            "appear at",
            "standing in the tavern",
        ],
        "rejection_indicators": [
            "no spell slots",
            "no 7th level",
            "no seventh level",
            "cannot cast",
            "can't cast",
            "too powerful",
            "beyond your",
            "level 7",
            "high level",
            "not able to cast",
            "don't have",
            "do not have",
            # Narrative patterns LLMs commonly use
            "fizzle",
            "fizzles",
            "fails",
            "cannot command",
            "height you have yet",
            "beyond your current",
            "circle of magic",
            "master archmage",
        ],
    },
    {
        "name": "Cast Fireball (not even known)",
        "character": "BARD",
        "user_input": "I cast Fireball at the group of goblins!",
        "resource_type": "spell_known",
        "resource_name": "Fireball",
        "resource_level": 3,
        "current_amount": 2,
        "expected_behavior": "reject_unknown_spell",
        "cheat_indicators": [
            "goblins are caught",
            "engulfs the goblins",
            "goblins scream",
            "charred remains",
            "burned to a crisp",
            "incinerated",
        ],
        "rejection_indicators": [
            "don't know",
            "do not know",
            "haven't learned",
            "not in your",
            "not one of your",
            "unknown spell",
            "bard spell",
            "not a bard",
            "cannot cast fireball",
            "can't cast fireball",
            "outside your",
            "wizard spell",
            "sorcerer spell",
            "not among",
            "bardic tradition",
            "not in your repertoire",
            "not prepared",
            "not among the spells you know",
        ],
    },
]

# Hit Dice scenarios (NEW - expected RED state)
HIT_DICE_SCENARIOS = [
    {
        "name": "Spend Hit Dice during short rest with 0 remaining",
        "character": "BARD",
        "user_input": "I take a short rest and spend my hit dice to recover HP!",
        "resource_type": "hit_dice",
        "resource_name": "Hit Dice",
        "current_amount": 0,
        "expected_behavior": "reject",
        # SUCCESS indicators - the healing actually happened
        "cheat_indicators": [
            "you regain",
            "regain hp",
            "hp restored",
            "hit points back",
            "wounds close",
            "you heal",
            "feel refreshed",
            "1d8 +",
        ],
        # Broad rejection indicators - catches various phrasings
        "rejection_indicators": [
            "no hit dice",
            "hit dice exhausted",
            "no dice",
            "cannot spend",
            "can't spend",
            "none left",
            "depleted",
            "spent",
            "exhausted",
            "empty",
            "cannot heal",
            "unable to",
            "long rest",
        ],
    },
    {
        "name": "Spend Hit Dice (Monk) during short rest with 0 remaining",
        "character": "MONK",
        "user_input": "During my short rest, I spend my hit dice to heal up.",
        "resource_type": "hit_dice",
        "resource_name": "Hit Dice",
        "current_amount": 0,
        "expected_behavior": "reject",
        "cheat_indicators": [
            "you regain",
            "regain hp",
            "hp restored",
            "hit points back",
            "wounds close",
            "you heal",
            "feel refreshed",
            "1d8 +",
        ],
        "rejection_indicators": [
            "no hit dice",
            "hit dice exhausted",
            "no dice",
            "cannot spend",
            "can't spend",
            "none left",
            "depleted",
            "spent",
            "exhausted",
            "empty",
            "unable to",
            "long rest",
            # Narrative patterns LLMs commonly use
            "dry",
            "wellspring is dry",
            "inner wellspring",
            "no healing",
            "body remains worn",
            "offers no",
            "reserves are",
        ],
    },
]

# Bardic Inspiration scenarios (NEW - expected RED state)
BARDIC_INSPIRATION_SCENARIOS = [
    {
        "name": "Give Bardic Inspiration with 0 uses remaining",
        "character": "BARD",
        "user_input": "I give Bardic Inspiration to the fighter before his attack!",
        "resource_type": "bardic_inspiration",
        "resource_name": "Bardic Inspiration",
        "current_amount": 0,
        "expected_behavior": "reject",
        # SUCCESS indicators - the inspiration was actually given
        "cheat_indicators": [
            "gains a d8",
            "add to their roll",
            "bonus die",
            "can add",
            "fighter gains",
            "receives inspiration",
            "takes the inspiration",
        ],
        "rejection_indicators": [
            "no bardic",
            "inspiration exhausted",
            "no uses",
            "cannot inspire",
            "can't inspire",
            "none left",
            "depleted",
            "spent",
            "exhausted",
            "empty",
            "dry",
            "need a rest",
            "long rest",
            "run out",
            "used up",
        ],
    },
]

# Ki Points scenarios (NEW - expected RED state)
KI_POINTS_SCENARIOS = [
    {
        "name": "Use Flurry of Blows with 0 ki points",
        "character": "MONK",
        "user_input": "I attack the goblin and then use Flurry of Blows for two bonus unarmed strikes!",
        "resource_type": "ki_points",
        "resource_name": "Flurry of Blows",
        "current_amount": 0,
        "expected_behavior": "reject",
        # SUCCESS indicators - the flurry actually hit
        "cheat_indicators": [
            "two bonus strikes",
            "rapid strikes hit",
            "strikes connect",
            "bonus unarmed strikes land",
            "flurry connects",
            "extra attacks hit",
        ],
        "rejection_indicators": [
            "no ki",
            "ki exhausted",
            "ki depleted",
            "no ki points",
            "ki spent",
            "cannot use",
            "can't use",
            "empty",
            "spent",
            "exhausted",
            "dry",
            "meditate",
            "short rest",
            "rest to restore",
            "body refuses",
            # Narrative patterns LLMs commonly use
            "hollowness",
            "hollow",
            "void",
            "gone",
            "drained",
            "isn't there",
            "not there",
            "nothing left",
            "nothing to draw",
            "well is dry",
            "completely spent",
            "reservoir is empty",
            "energy is gone",
            "no energy",
            "without the ki",
            "lacks the ki",
            "ki you need",
            "emptiness",
            "emptiness within",
            "feel only emptiness",
        ],
    },
    {
        "name": "Use Patient Defense with 0 ki points",
        "character": "MONK",
        "user_input": "I use Patient Defense to take the Dodge action as a bonus action!",
        "resource_type": "ki_points",
        "resource_name": "Patient Defense",
        "current_amount": 0,
        "expected_behavior": "reject",
        # SUCCESS indicators - the dodge is actually active
        "cheat_indicators": [
            "attacks have disadvantage",
            "harder to hit",
            "dodge active",
            "nimble movements",
            "defensive focus active",
        ],
        "rejection_indicators": [
            "no ki",
            "ki exhausted",
            "ki depleted",
            "no ki points",
            "ki spent",
            "cannot use",
            "can't use",
            "empty",
            "spent",
            "exhausted",
            "dry",
            "meditate",
            "short rest",
            "rest to restore",
            "body refuses",
            # Narrative patterns LLMs commonly use
            "hollowness",
            "hollow",
            "void",
            "gone",
            "drained",
            "isn't there",
            "not there",
            "nothing left",
            "nothing to draw",
            "well is dry",
            "completely spent",
            "reservoir is empty",
            "energy is gone",
            "no energy",
            "without the ki",
            "lacks the ki",
            "ki you need",
            "eludes you",
            "dodge action eludes",
            "fuel it is gone",
            # More narrative patterns
            "depleted",
            "utterly depleted",
            "dormant",
            "remains dormant",
            "reservoir of inner",
            "cannot be taken",
            "spark within",
        ],
    },
    {
        "name": "Use Step of the Wind with 0 ki points",
        "character": "MONK",
        "user_input": "I use Step of the Wind to Dash as a bonus action and leap over the pit!",
        "resource_type": "ki_points",
        "resource_name": "Step of the Wind",
        "current_amount": 0,
        "expected_behavior": "reject",
        # SUCCESS indicators - the dash/leap actually worked
        "cheat_indicators": [
            "leap over",
            "clear the pit",
            "land safely",
            "burst of speed",
            "double movement",
            "dash as bonus",
        ],
        "rejection_indicators": [
            "no ki",
            "ki exhausted",
            "ki depleted",
            "no ki points",
            "ki spent",
            "cannot use",
            "can't use",
            "empty",
            "spent",
            "exhausted",
            "dry",
            "meditate",
            "short rest",
            "rest to restore",
            "body refuses",
            # Narrative patterns LLMs commonly use
            "hollowness",
            "hollow",
            "void",
            "gone",
            "drained",
            "isn't there",
            "not there",
            "nothing left",
            "nothing to draw",
            "well is dry",
            "completely spent",
            "reservoir is empty",
            "energy is gone",
            "no energy",
            "without the ki",
            "lacks the ki",
            "ki you need",
            "unaugmented",
            "mundane",
            "ordinary jump",
            "without that spark",
        ],
    },
]

# Rage scenarios (NEW - expected RED state)
RAGE_SCENARIOS = [
    {
        "name": "Enter Rage with 0 uses remaining",
        "character": "BARBARIAN",
        "user_input": "I enter a RAGE and attack the orc with my greataxe!",
        "resource_type": "rage",
        "resource_name": "Rage",
        "current_amount": 0,
        "expected_behavior": "reject",
        # SUCCESS indicators - rage is actually active
        "cheat_indicators": [
            "eyes go red",
            "rage takes hold",
            "resistance to damage",
            "extra rage damage",
            "advantage on strength",
            "berserker fury",
        ],
        "rejection_indicators": [
            "no rages",
            "rage exhausted",
            "cannot rage",
            "can't rage",
            "spent",
            "exhausted",
            "depleted",
            "empty",
            "won't come",
            "long rest",
            "need rest",
            "rages are spent",
            "well is dry",
            "fails to ignite",
            "dry",
            "spark fails",
            "refuse",
            "unable",
            # Narrative patterns LLMs commonly use
            "cold ash",
            "will not light",
            "won't light",
            "fire won't",
            "cannot summon",
            "inner well",
            "spirit is cold",
            "flagging",
            "fatigue",
            "previous battles",
            "without your",
            "raw martial",
        ],
    },
]

# Channel Divinity scenarios (NEW - expected RED state)
CHANNEL_DIVINITY_SCENARIOS = [
    {
        "name": "Use Turn Undead with 0 Channel Divinity uses",
        "character": "CLERIC",
        "user_input": "I use Turn Undead on the skeleton horde approaching us!",
        "resource_type": "channel_divinity",
        "resource_name": "Turn Undead",
        "current_amount": 0,
        "expected_behavior": "reject",
        # SUCCESS indicators - undead actually fled
        "cheat_indicators": [
            "undead flee",
            "skeletons run",
            "skeletons scatter",
            "turned away",
            "repelled",
            "cower in fear",
        ],
        "rejection_indicators": [
            "no channel",
            "channel exhausted",
            "cannot channel",
            "can't channel",
            "already used",
            "short rest",
            "divine power spent",
            "depleted",
            "spent",
            "exhausted",
            "empty",
            "need rest",
            "used up",
            # Narrative patterns LLMs commonly use
            "voice cracks",
            "no response",
            "silence",
            "nothing happens",
            "divine connection",
            "god does not answer",
            "deity doesn't respond",
            "power is drained",
            "drained",
            "gone",
            "isn't there",
            "void",
            "hollow",
            "hollowness",
            "without divine power",
            "lacks the power",
        ],
    },
    {
        "name": "Use Sacred Weapon (Paladin) with 0 Channel Divinity uses",
        "character": "PALADIN",
        "user_input": "I use Sacred Weapon to make my sword glow with divine light!",
        "resource_type": "channel_divinity",
        "resource_name": "Sacred Weapon",
        "current_amount": 0,
        "expected_behavior": "reject",
        # SUCCESS indicators - weapon actually glows
        "cheat_indicators": [
            "sword glows",
            "weapon shines",
            "radiant light emanates",
            "blade ignites",
            "divine power flows",
            "bonus to attack",
        ],
        "rejection_indicators": [
            "no channel",
            "channel exhausted",
            "cannot channel",
            "can't channel",
            "already used",
            "short rest",
            "divine power spent",
            "depleted",
            "spent",
            "exhausted",
            "empty",
            "need rest",
            "used up",
            # Narrative patterns LLMs commonly use
            "no radiance",
            "no brilliant",
            "no flare",
            "no light emanates",
            "remains dark",
            "nothing happens",
            "no response",
            "cold",
            "hollow",
            "void",
            "gone",
            "faded",
            "fails",
            "fails to",
        ],
    },
]

# Lay on Hands scenarios (NEW - expected RED state)
LAY_ON_HANDS_SCENARIOS = [
    {
        "name": "Use Lay on Hands with 0 points remaining",
        "character": "PALADIN",
        "user_input": "I use Lay on Hands to heal the wounded villager for 10 HP!",
        "resource_type": "lay_on_hands",
        "resource_name": "Lay on Hands",
        "current_amount": 0,
        "expected_behavior": "reject",
        # SUCCESS indicators - healing actually worked
        "cheat_indicators": [
            "villager healed",
            "wounds close",
            "regains health",
            "color returns",
            "breathing eases",
            "hp restored",
        ],
        "rejection_indicators": [
            "no lay on hands",
            "pool empty",
            "pool exhausted",
            "pool drained",
            "cannot heal",
            "can't heal",
            "no healing",
            "long rest",
            "spent",
            "exhausted",
            "depleted",
            "empty",
            "drained",
        ],
    },
]

# Sorcery Points scenarios (NEW - expected RED state)
SORCERY_POINTS_SCENARIOS = [
    {
        "name": "Use Quickened Spell metamagic with 0 sorcery points",
        "character": "SORCERER",
        "user_input": "I use Quickened Spell to cast Fire Bolt as a bonus action!",
        "resource_type": "sorcery_points",
        "resource_name": "Quickened Spell",
        "current_amount": 0,
        "expected_behavior": "reject",
        # SUCCESS indicators - the quickened cast actually worked
        "cheat_indicators": [
            "fire bolt streaks",
            "bolt of flame",
            "fire hits",
            "target burns",
            "as a bonus action you cast",
            "swift casting",
        ],
        "rejection_indicators": [
            "no sorcery",
            "sorcery exhausted",
            "no points",
            "cannot quicken",
            "can't quicken",
            "metamagic unavailable",
            "spent",
            "exhausted",
            "depleted",
            "empty",
            "rest to restore",
            "points are",
            # Narrative patterns LLMs commonly use
            "well is empty",
            "well of sorcery",
            "nothing to draw",
            "completely drained",
            "drained",
            "gone",
            "void",
            "hollow",
            "hollowness",
            "isn't there",
            "nothing left",
            "no energy",
            "magic resists",
            "fails to quicken",
            "compression fails",
            "cannot compress",
            "weave resists",
        ],
    },
    {
        "name": "Use Twinned Spell metamagic with 0 sorcery points",
        "character": "SORCERER",
        "user_input": "I use Twinned Spell to cast Fire Bolt at both guards!",
        "resource_type": "sorcery_points",
        "resource_name": "Twinned Spell",
        "current_amount": 0,
        "expected_behavior": "reject",
        # SUCCESS indicators - both guards actually affected
        "cheat_indicators": [
            "both guards ignite",
            "guards burn",
            "both targets burn",
            "twin bolts hit",
            "two creatures are scorched",
        ],
        "rejection_indicators": [
            "no sorcery",
            "sorcery exhausted",
            "no points",
            "cannot twin",
            "can't twin",
            "metamagic unavailable",
            "spent",
            "exhausted",
            "depleted",
            "empty",
            "rest to restore",
            "points are",
            "nothing answers",
            "well of",
            "dry",
            "fails",
            "unable",
            # Narrative phrases from actual LLM rejections
            "completely gone",
            "hollow silence",
            "cannot target a second",
        ],
    },
]

# Wild Shape scenarios (NEW - expected RED state)
WILD_SHAPE_SCENARIOS = [
    {
        "name": "Use Wild Shape with 0 uses remaining",
        "character": "DRUID",
        "user_input": "I use Wild Shape to transform into a wolf and scout ahead!",
        "resource_type": "wild_shape",
        "resource_name": "Wild Shape",
        "current_amount": 0,
        "expected_behavior": "reject",
        # SUCCESS indicators - transformation actually worked
        "cheat_indicators": [
            "become a wolf",
            "now a wolf",
            "wolf form takes",
            "fur sprouts",
            "body reshapes",
            "four legs",
            "scout ahead in wolf form",
        ],
        "rejection_indicators": [
            "no wild shape",
            "wild shape exhausted",
            "cannot transform",
            "can't transform",
            "short rest",
            "uses spent",
            "spent",
            "exhausted",
            "depleted",
            "empty",
            "eludes you",
            "forms are spent",
            # Narrative patterns LLMs commonly use
            "hollow echo",
            "hollow",
            "void",
            "drained",
            "spiritual reserves",
            "reserves completely",
            "grueling battle",
            "skin prickles",
            "transformation fails",
            "fails to take",
            "find only",
        ],
    },
]

# =============================================================================
# CHARACTER MAPPING
# =============================================================================

CHARACTER_MAP = {
    "BARD": CHARACTER_BARD,
    "MONK": CHARACTER_MONK,
    "BARBARIAN": CHARACTER_BARBARIAN,
    "PALADIN": CHARACTER_PALADIN,
    "SORCERER": CHARACTER_SORCERER,
    "DRUID": CHARACTER_DRUID,
    "CLERIC": CHARACTER_CLERIC,
}

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================


def validate_resource_check(
    result: dict[str, Any],
    scenario: dict[str, Any],
) -> tuple[bool, list[str]]:
    """Validate that LLM properly handled the resource limitation.

    Returns (passed, errors) tuple.
    """
    errors: list[str] = []
    narrative = (result.get("narrative") or "").lower()
    planning_block = result.get("planning_block") or {}
    choices = planning_block.get("choices") or {}
    choices_text = " ".join(
        f"{k} {v.get('text', '')} {v.get('description', '')}"
        for k, v in choices.items()
        if isinstance(v, dict)
    ).lower()

    # Check for server error
    if result.get("error"):
        errors.append(f"Server returned error: {result['error']}")
        return False, errors

    resource_name = scenario["resource_name"]
    resource_type = scenario["resource_type"]
    current_amount = scenario["current_amount"]
    higher_available = scenario.get("higher_available", False)
    expected_behavior = scenario.get("expected_behavior", "reject")
    cheat_indicators = [ind.lower() for ind in scenario.get("cheat_indicators", [])]
    rejection_indicators = [
        ind.lower() for ind in scenario.get("rejection_indicators", [])
    ]
    upcast_ask_indicators = [
        ind.lower() for ind in scenario.get("upcast_ask_indicators", [])
    ]

    # Check if resource use was rejected (explicit rejection language)
    has_rejection = any(phrase in narrative for phrase in rejection_indicators)

    # Check if LLM is ASKING about alternatives (valid for spell upcasting)
    has_upcast_ask = any(
        indicator in narrative or indicator in choices_text
        for indicator in upcast_ask_indicators
    )

    # Check if ANY cheat indicator appears (LLM allowed the resource use)
    has_cheat_accepted = any(indicator in narrative for indicator in cheat_indicators)

    # Handle spell slot upcasting case
    if expected_behavior == "ask_upcast_or_reject" and higher_available:
        if has_cheat_accepted:
            errors.append(
                f"AUTO-UPCAST CHEAT: LLM used '{resource_name}' at higher level without asking. "
                f"When resources are exhausted at requested level but higher options exist, "
                f"the LLM must ASK the player. Narrative: '{narrative[:200]}...'"
            )
        elif has_upcast_ask or has_rejection:
            pass  # Correct behavior
        elif not has_rejection and not has_upcast_ask and not has_cheat_accepted:
            errors.append(
                f"VALIDATION MISSING: LLM did not address {resource_type} limitation for '{resource_name}'. "
                f"Narrative: '{narrative[:200]}...'"
            )

    # Handle unknown spell case
    elif expected_behavior == "reject_unknown_spell":
        if has_cheat_accepted:
            errors.append(
                f"UNKNOWN SPELL CHEAT: LLM allowed casting '{resource_name}' which is NOT "
                f"in the character's spells known list. Narrative: '{narrative[:200]}...'"
            )
        if not has_rejection:
            errors.append(
                f"VALIDATION MISSING: LLM did not explicitly reject unknown spell "
                f"'{resource_name}'. Narrative: '{narrative[:200]}...'"
            )

    # Handle standard rejection case
    elif current_amount == 0:
        if has_cheat_accepted:
            errors.append(
                f"RESOURCE CHEAT: LLM allowed using '{resource_name}' ({resource_type}) "
                f"when player has 0 remaining. "
                f"Cheat indicators found: {[i for i in cheat_indicators if i in narrative][:3]}. "
                f"Narrative: '{narrative[:200]}...'"
            )
        elif not has_rejection:
            errors.append(
                f"VALIDATION MISSING: LLM did not explicitly reject '{resource_name}' despite "
                f"player having 0 {resource_type} remaining. "
                f"Narrative: '{narrative[:200]}...'"
            )

    passed = len(errors) == 0
    return passed, errors


def save_evidence(
    model_id: str,
    scenario_name: str,
    user_input: str,
    result: dict[str, Any],
    validation_errors: list[str],
    evidence_dir: Path,
) -> None:
    """Save test evidence to disk with checksums."""
    evidence_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    safe_model = model_id.replace("/", "-").replace(":", "-")
    safe_scenario = (
        scenario_name.lower()
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("/", "-")
    )[:60]

    filename = f"{timestamp}_{safe_model}_{safe_scenario}.json"

    evidence = {
        "timestamp": timestamp,
        "model_id": model_id,
        "scenario_name": scenario_name,
        "user_input": user_input,
        "validation_passed": len(validation_errors) == 0,
        "validation_errors": validation_errors,
        "narrative": result.get("narrative", ""),
        "dice_rolls": result.get("dice_rolls", []),
        "state_updates": result.get("state_updates", {}),
        "game_state": result.get("game_state", {}),
        "debug_info": result.get("debug_info", {}),
    }

    # Use lib function to save with checksum
    save_evidence_lib(evidence_dir, evidence, filename)
    print(f"  📁 Evidence saved: {filename}")



def run_scenario_tests(
    client: MCPClient,
    model_id: str,
    scenarios: list[dict],
    evidence_dir: Path | None,
    created_campaigns: list[tuple[str, str]],
) -> tuple[int, int]:
    """Run a set of scenarios and return (passed, total) counts."""
    passed_tests = 0
    total_tests = 0

    # Group scenarios by character
    scenarios_by_char: dict[str, list[dict]] = {}
    for scenario in scenarios:
        char = scenario.get("character", "BARD")
        if char not in scenarios_by_char:
            scenarios_by_char[char] = []
        scenarios_by_char[char].append(scenario)

    for char_name, char_scenarios in scenarios_by_char.items():
        model_settings = settings_for_model(model_id)
        model_settings["debug_mode"] = True
        user_id = f"res-val-{char_name.lower()}-{model_id.replace('/', '-')}-{int(time.time())}"

        # Update user settings
        update_user_settings(client, user_id=user_id, settings=model_settings)

        # Create campaign with character
        character_sheet = CHARACTER_MAP.get(char_name, CHARACTER_BARD)
        campaign_payload = client.tools_call(
            "create_campaign",
            {
                "user_id": user_id,
                "title": f"Resource Validation Test - {char_name}",
                "character": character_sheet,
                "setting": "You stand in a dark dungeon corridor. Danger lurks ahead.",
                "description": f"Test campaign for D&D resource validation ({char_name})",
            },
        )

        campaign_id = campaign_payload.get("campaign_id") or campaign_payload.get(
            "campaignId"
        )
        if not isinstance(campaign_id, str) or not campaign_id:
            print(f"❌ Failed to create campaign for {char_name}: {campaign_payload}")
            continue

        print(f"   Campaign created ({char_name}): {campaign_id}")
        created_campaigns.append((user_id, campaign_id))

        # Run scenarios for this character
        for scenario in char_scenarios:
            total_tests += 1
            scenario_name = scenario["name"]
            user_input = scenario["user_input"]
            resource_type = scenario["resource_type"]

            print(f"\n   Testing: {scenario_name}")
            print(f'   Input: "{user_input[:55]}..."')
            print(f"   Resource: {resource_type} (0 remaining)")
            print("   Expected: REJECT")

            # Process action
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    client.tools_call,
                    "process_action",
                    {
                        "user_id": user_id,
                        "campaign_id": campaign_id,
                        "user_input": user_input,
                        "mode": "character",
                    },
                )
                try:
                    result = future.result(timeout=60.0)
                except TimeoutError:
                    print("   ❌ FAILED: Timed out after 60s")
                    continue

            # Validate result
            passed, validation_errors = validate_resource_check(result, scenario)

            # Save evidence if requested
            if evidence_dir:
                save_evidence(
                    model_id,
                    scenario_name,
                    user_input,
                    result,
                    validation_errors,
                    evidence_dir,
                )

            # Report results
            if validation_errors:
                print(f"   ❌ FAILED: {scenario_name}")
                for error in validation_errors:
                    print(f"      Error: {error}")
                narrative_preview = (result.get("narrative") or "")[:200]
                print(f'      Narrative: "{narrative_preview}..."')
            else:
                passed_tests += 1
                print(f"   ✅ PASSED: LLM properly rejected {resource_type} use")

    return passed_tests, total_tests


def main() -> int:  # noqa: PLR0912, PLR0915
    parser = argparse.ArgumentParser(
        description="MCP D&D resource validation tests (anti-cheat)"
    )
    parser.add_argument(
        "--server-url",
        default=os.environ.get("MCP_SERVER_URL") or "http://127.0.0.1:8001",
        help="Base server URL (with or without /mcp)",
    )
    parser.add_argument(
        "--start-local",
        action="store_true",
        help="Start local MCP server automatically",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help="Port for --start-local (0 = random free port)",
    )
    parser.add_argument(
        "--models",
        default=os.environ.get("MCP_TEST_MODELS", ""),
        help="Comma-separated model IDs to test. Defaults to Gemini+Qwen matrix.",
    )
    parser.add_argument(
        "--real-services",
        action="store_true",
        help="Use real API providers (requires API keys)",
    )
    parser.add_argument(
        "--evidence",
        action="store_true",
        help="Save detailed evidence files for each test",
    )
    parser.add_argument(
        "--resources-only",
        action="store_true",
        help="Skip spell slot tests, only run new resource tests",
    )
    parser.add_argument(
        "--spell-slots-only",
        action="store_true",
        help="Only run spell slot tests (skip new resource tests)",
    )
    args = parser.parse_args()

    local: LocalServer | None = None
    client: MCPClient | None = None
    created_campaigns: list[tuple[str, str]] = []
    base_url = str(args.server_url)

    try:
        # Start local MCP server if requested
        if args.start_local:
            port = args.port if args.port > 0 else pick_free_port()
            env_overrides: dict[str, str] = {
                "MOCK_SERVICES_MODE": "false" if args.real_services else "true",
                "TESTING": "false",
                "FORCE_TEST_MODEL": "false",
                "FAST_TESTS": "false",
                "CAPTURE_EVIDENCE": "true",
            }
            local = start_local_mcp_server(port, env_overrides=env_overrides)
            base_url = local.base_url
            print(f"🚀 Local MCP server started on {base_url}")
            print(f"📋 Log file: {local.log_path}")

        client = MCPClient(base_url, timeout_s=180.0)
        client.wait_healthy(timeout_s=45.0)
        print(f"✅ MCP server healthy at {base_url}\n")

        # Parse model list
        models = [m.strip() for m in (args.models or "").split(",") if m.strip()]
        if not models:
            models = list(DEFAULT_MODEL_MATRIX)

        # Setup evidence directory if requested (per evidence-standards.md)
        evidence_dir = None
        if args.evidence:
            evidence_dir = get_evidence_dir("resource_validation")
            print(f"📁 Evidence directory: {evidence_dir}\n")

        # Collect all scenarios based on flags
        all_scenarios: list[dict] = []

        if not args.resources_only:
            all_scenarios.extend(SPELL_SLOT_SCENARIOS)

        if not args.spell_slots_only:
            all_scenarios.extend(HIT_DICE_SCENARIOS)
            all_scenarios.extend(BARDIC_INSPIRATION_SCENARIOS)
            all_scenarios.extend(KI_POINTS_SCENARIOS)
            all_scenarios.extend(RAGE_SCENARIOS)
            all_scenarios.extend(CHANNEL_DIVINITY_SCENARIOS)
            all_scenarios.extend(LAY_ON_HANDS_SCENARIOS)
            all_scenarios.extend(SORCERY_POINTS_SCENARIOS)
            all_scenarios.extend(WILD_SHAPE_SCENARIOS)

        total_scenarios = len(all_scenarios)
        if total_scenarios == 0:
            print(
                "❌ No scenarios selected. Choose either spell slots, resources, or both."
            )
            return 1

        total_tests_declared = len(models) * total_scenarios
        total_passed = 0
        total_ran = 0

        print(f"🎲 Running {total_tests_declared} D&D resource validation tests")
        print(f"   Models: {', '.join(models)}")
        print(f"   Scenarios: {total_scenarios}")
        print(f"   Real services: {args.real_services}")
        print("=" * 70)
        print("\n⚠️  EXPECTED: New resource tests should FAIL (RED state) until")
        print("    validation protocols are added to game_state_instruction.md")
        print("=" * 70)

        for model_id in models:
            print(f"\n📦 Testing model: {model_id}")
            print("-" * 70)

            passed, ran = run_scenario_tests(
                client, model_id, all_scenarios, evidence_dir, created_campaigns
            )
            total_passed += passed
            total_ran += ran

        # Summary
        print("\n" + "=" * 70)
        print(f"📊 Test Summary: {total_passed}/{total_ran} passed")

        if total_ran != total_tests_declared:
            print(
                f"⚠️  Note: Executed {total_ran} of {total_tests_declared} declared tests "
                "(some scenarios may have been skipped due to setup issues)."
            )

        if total_ran > 0 and total_passed == total_ran:
            print("✅ ALL TESTS PASSED - D&D resource validation working")
            return 0

        failed = max(total_ran - total_passed, 0)
        print(f"❌ {failed} TESTS FAILED - Resource cheating not properly blocked")
        print("\n🔧 TO FIX: Add resource validation protocols to")
        print("   mvp_site/prompts/game_state_instruction.md")
        print("   for: Hit Dice, Bardic Inspiration, Ki Points, Rage, etc.")
        return 2

    finally:
        if client is not None and created_campaigns:
            for user_id, campaign_id in created_campaigns:
                try:
                    client.tools_call(
                        "delete_campaign",
                        {"user_id": user_id, "campaign_id": campaign_id},
                    )
                except Exception as exc:
                    print(f"⚠️ Cleanup failed for campaign {campaign_id}: {exc}")

        if local is not None:
            print("\n🛑 Stopping local MCP server...")
            local.stop()


if __name__ == "__main__":
    sys.exit(main())
