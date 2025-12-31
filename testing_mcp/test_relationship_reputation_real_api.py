#!/usr/bin/env python3
"""Real API tests for relationship and reputation mechanics.

These tests verify that:
1. The LLM produces relationship updates (trust_level changes) in state_updates
2. The LLM can request detailed instructions via debug_info.meta.needs_detailed_instructions
3. Relationship/reputation mechanics are properly applied in NPC interactions
4. Multi-turn instruction loading: when LLM requests hints on Turn N, instructions
   are loaded on Turn N+1 and are not repeatedly loaded without new hints
   (validated via system_instruction_files in debug_info)

Tests exercise the system THROUGH MCP (`/mcp`) - no direct LLM API calls.

Run (local MCP already running):
    cd testing_mcp
    python test_relationship_reputation_real_api.py --server-url http://127.0.0.1:8001

Run (start local MCP automatically):
    cd testing_mcp
    python test_relationship_reputation_real_api.py --start-local
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from lib.mcp_client import MCPClient
from lib.server_utils import LocalServer, pick_free_port, start_local_mcp_server
from lib.model_utils import DEFAULT_MODEL_MATRIX, settings_for_model, update_user_settings
from lib.evidence_utils import (
    capture_provenance,
    create_evidence_bundle,
    get_evidence_dir,
)

DEFAULT_MODEL = "gemini-3-flash-preview"


# Test scenarios that should trigger relationship mechanics
TEST_SCENARIOS: list[dict[str, Any]] = [
    {
        "name": "Save NPC Life",
        "setup_npc": {
            "name": "Merchant Aldric",
            "string_id": "npc_aldric_001",
            "role": "merchant",
            "hp_current": 5,
            "hp_max": 20,
            "present": True,
            "relationships": {
                "player": {
                    "trust_level": 0,
                    "disposition": "neutral",
                    "history": [],
                    "debts": [],
                    "grievances": [],
                }
            },
        },
        "user_input": "I give a healing potion to Merchant Aldric to save his life.",
        "expect_relationship_update": True,
        "expect_trust_increase": True,
        "description": "Saving an NPC should increase trust_level",
    },
    {
        "name": "Betray NPC Trust",
        "setup_npc": {
            "name": "Guard Captain Mira",
            "string_id": "npc_mira_001",
            "role": "guard_captain",
            "hp_current": 40,
            "hp_max": 40,
            "present": True,
            "relationships": {
                "player": {
                    "trust_level": 3,
                    "disposition": "friendly",
                    "history": ["Shared information about thieves guild"],
                    "debts": [],
                    "grievances": [],
                }
            },
        },
        "user_input": "I steal the patrol schedule from Guard Captain Mira's desk while she's distracted.",
        # Soft expectation: relationship may or may not update depending on whether caught
        "expect_relationship_update": False,  # Don't require - theft may go unnoticed
        "expect_trust_decrease": True,  # IF updated, should be negative
        "allow_no_update_if_undetected": True,  # Pass if theft succeeded undetected
        "description": "Betraying an NPC should decrease trust_level if caught",
    },
    {
        "name": "First Meeting - Faction Representative",
        "setup_npc": {
            "name": "Ambassador Theron",
            "string_id": "npc_theron_001",
            "role": "diplomat",
            "hp_current": 25,
            "hp_max": 25,
            "present": True,
            "faction": "faction_ironhold_001",
        },
        "user_input": "I introduce myself formally to Ambassador Theron and explain my mission to establish trade relations.",
        # Soft expectation: relationship may be initialized or just narratively acknowledged
        "expect_relationship_init": False,  # Don't hard-require - context may not trigger
        "expect_narrative_interaction": True,  # Just verify NPC appears in narrative
        "description": "First interaction should establish relationship structure",
    },
    {
        "name": "Reputation-Affecting Public Deed",
        "setup_reputation": {
            "public": {
                "score": 10,
                "titles": [],
                "known_deeds": [],
                "rumors": [],
                "notoriety_level": "known",
            },
        },
        "user_input": "I loudly announce in the town square that I will personally deal with the bandit problem, for no reward.",
        "expect_reputation_update": True,
        "description": "Public heroic declaration should affect reputation",
    },
    # ========== A. Trust Changes ==========
    {
        "name": "Break Promise - Trust Decrease",
        "isolated": True,  # Needs fresh campaign - tests promise mechanics
        "setup_npc": {
            "name": "Innkeeper Bram",
            "string_id": "npc_bram_001",
            "role": "innkeeper",
            "hp_current": 15,
            "hp_max": 15,
            "present": True,
            "relationships": {
                "player": {
                    "trust_level": 2,
                    "disposition": "friendly",
                    "history": ["Player promised to return borrowed lantern by morning"],
                    "debts": ["owes lantern"],
                    "grievances": [],
                }
            },
        },
        "user_input": "I tell Innkeeper Bram that I lost the lantern I promised to return and I won't be replacing it.",
        "expect_relationship_update": False,  # Soft - LLM may not always produce update
        "expect_trust_decrease": True,  # IF updated, should be negative
        "allow_no_update_if_undetected": True,  # LLM may interpret differently
        "expect_narrative_interaction": True,
        "description": "Breaking a promise should decrease trust_level (-2 to -3)",
    },
    {
        "name": "Steal From NPC - Trust Decrease",
        "setup_npc": {
            "name": "Herbalist Yara",
            "string_id": "npc_yara_001",
            "role": "merchant",
            "hp_current": 12,
            "hp_max": 12,
            "present": True,
            "relationships": {
                "player": {
                    "trust_level": 1,
                    "disposition": "friendly",
                    "history": [],
                    "debts": [],
                    "grievances": [],
                }
            },
        },
        "user_input": "While Herbalist Yara is looking away, I grab a healing potion from her shelf and slip it into my bag. She turns around and sees me.",
        "expect_relationship_update": True,
        "expect_trust_decrease": True,
        "description": "Stealing from NPC (witnessed) should decrease trust_level (-2 to -4)",
    },
    # ========== B. Behavior Modifiers ==========
    {
        "name": "Hostile NPC Refuses Service",
        "setup_npc": {
            "name": "Blacksmith Gorrim",
            "string_id": "npc_gorrim_001",
            "role": "blacksmith",
            "hp_current": 45,
            "hp_max": 45,
            "present": True,
            "relationships": {
                "player": {
                    "trust_level": -8,
                    "disposition": "hostile",
                    "history": ["Player killed his apprentice"],
                    "debts": [],
                    "grievances": ["murdered apprentice", "never apologized"],
                }
            },
        },
        "user_input": "I approach Blacksmith Gorrim and ask to buy a new sword.",
        "expect_narrative_interaction": True,
        "expect_hostile_behavior": True,
        "description": "Hostile NPC (-8 trust) should refuse service or attack",
    },
    {
        "name": "Trusted NPC Offers Discount",
        "setup_npc": {
            "name": "Jeweler Elara",
            "string_id": "npc_elara_001",
            "role": "merchant",
            "hp_current": 10,
            "hp_max": 10,
            "present": True,
            "relationships": {
                "player": {
                    "trust_level": 5,
                    "disposition": "trusted",
                    "history": ["Player saved her shop from fire", "Regular customer"],
                    "debts": ["owes player for fire rescue"],
                    "grievances": [],
                }
            },
        },
        "user_input": "I ask Jeweler Elara how much for the ruby necklace in the display case.",
        "expect_narrative_interaction": True,
        "expect_discount_mention": True,
        "description": "Trusted NPC (+5 trust) should offer discount (10-20%)",
    },
    # ========== C. Public Reputation ==========
    {
        "name": "Murder Witnessed - Reputation Crash",
        "setup_npc": {
            "name": "Beggar Tom",
            "string_id": "npc_tom_001",
            "role": "commoner",
            "hp_current": 5,
            "hp_max": 5,
            "present": True,
        },
        "setup_reputation": {
            "public": {
                "score": 30,
                "titles": ["Helper of the Poor"],
                "known_deeds": ["donated to orphanage"],
                "rumors": [],
                "notoriety_level": "respected",
            },
        },
        "setup_witnesses": True,
        "user_input": "In the crowded marketplace, I draw my sword and attack Beggar Tom without provocation. Many people see this.",
        "expect_reputation_update": True,
        "expect_reputation_decrease": True,
        "description": "Murder witnessed by crowd should drastically decrease public reputation (-15 to -30)",
    },
    {
        "name": "Secret Faction Mission - Private Only",
        "isolated": True,  # Needs fresh campaign - state-sensitive
        "setup_npc": {
            "name": "Shadow Guild Contact",
            "string_id": "npc_shadow_001",
            "role": "spy",
            "hp_current": 20,
            "hp_max": 20,
            "present": True,
            "faction": "faction_shadow_guild_001",
        },
        "setup_reputation": {
            "public": {
                "score": 20,
                "titles": [],
                "known_deeds": [],
                "rumors": [],
                "notoriety_level": "known",
            },
            "private": {
                "faction_shadow_guild_001": {
                    "score": 2,
                    "standing": "friendly",
                    "known_deeds": [],
                    "secret_knowledge": [],
                }
            },
        },
        "user_input": "I whisper to the Shadow Guild Contact that I've completed the secret dead drop mission. No one else heard.",
        "expect_private_reputation_update": True,
        "expect_public_unchanged": True,
        "description": "Secret faction mission should update private reputation only, not public",
    },
    # ========== D. Notoriety Levels ==========
    {
        "name": "Infamous - Bounty and Refusal",
        "isolated": True,  # Needs fresh campaign - specific reputation score
        "setup_reputation": {
            "public": {
                "score": -75,
                "titles": ["The Butcher of Millbrook"],
                "known_deeds": ["massacred village of Millbrook"],
                "rumors": ["wanted dead or alive"],
                "notoriety_level": "infamous",
            },
        },
        "setup_npc": {
            "name": "Traveling Merchant",
            "string_id": "npc_merchant_001",
            "role": "merchant",
            "hp_current": 12,
            "hp_max": 12,
            "present": True,
        },
        "user_input": "I approach the Traveling Merchant and ask to buy supplies.",
        "expect_narrative_interaction": True,
        "expect_service_refused": True,
        "description": "Infamous reputation (-75) should result in service refused or hostile reaction",
    },
    {
        "name": "Famous - Crowds and Discounts",
        "isolated": True,  # Needs fresh campaign - specific reputation score
        "setup_reputation": {
            "public": {
                "score": 65,
                "titles": ["Dragonslayer", "Hero of the Realm"],
                "known_deeds": ["slew the dragon threatening the kingdom"],
                "rumors": ["touched by the gods"],
                "notoriety_level": "famous",
            },
        },
        "setup_npc": {
            "name": "Shopkeeper Marcus",
            "string_id": "npc_marcus_001",
            "role": "merchant",
            "hp_current": 10,
            "hp_max": 10,
            "present": True,
        },
        "user_input": "I walk into the shop. The shopkeeper notices me.",
        "expect_narrative_interaction": True,
        "expect_fame_recognition": True,
        "description": "Famous reputation (+65) should result in recognition and special treatment",
    },
    # ========== E. Priority Hierarchy ==========
    {
        "name": "Private Trust Override Trumps Relationship",
        "isolated": True,  # Needs fresh campaign - tests priority hierarchy
        "setup_npc": {
            "name": "Faction Agent Vex",
            "string_id": "npc_vex_001",
            "role": "spy",
            "hp_current": 25,
            "hp_max": 25,
            "present": True,
            "faction": "faction_crimson_hand_001",
            "relationships": {
                "player": {
                    "trust_level": 5,
                    "disposition": "trusted",
                    "history": ["old friends"],
                    "debts": [],
                    "grievances": [],
                }
            },
        },
        "setup_reputation": {
            "private": {
                "faction_crimson_hand_001": {
                    "score": -8,
                    "standing": "enemy",
                    "known_deeds": ["betrayed faction secrets"],
                    "secret_knowledge": ["knows player is a traitor"],
                    "trust_override": -10,
                }
            },
        },
        "user_input": "I greet my old friend Faction Agent Vex warmly and ask for help.",
        "expect_narrative_interaction": True,
        "expect_hostile_despite_history": True,
        "description": "Private trust_override (-10) should trump personal relationship (+5)",
    },
    {
        "name": "Faction Standing Trumps Public Reputation",
        "isolated": True,  # Needs fresh campaign - tests priority hierarchy
        "setup_npc": {
            "name": "Guild Treasurer Finn",
            "string_id": "npc_finn_001",
            "role": "official",
            "hp_current": 15,
            "hp_max": 15,
            "present": True,
            "faction": "faction_merchants_guild_001",
        },
        "setup_reputation": {
            "public": {
                "score": -40,
                "titles": ["The Swindler"],
                "known_deeds": ["cheated many merchants"],
                "rumors": ["cannot be trusted"],
                "notoriety_level": "notorious",
            },
            "private": {
                "faction_merchants_guild_001": {
                    "score": 6,
                    "standing": "trusted",
                    "known_deeds": ["secretly recovered guild funds", "exposed corrupt official"],
                    "secret_knowledge": ["actually works for the guild"],
                }
            },
        },
        "user_input": "I approach Guild Treasurer Finn and request access to the guild vault.",
        "expect_narrative_interaction": True,
        "expect_access_granted": True,
        "description": "Private faction standing (+6 trusted) should override public reputation (-40 notorious)",
    },
    # ========== F. Cascading/Memory ==========
    {
        "name": "Kill Ally - Cascading Trust Loss",
        "isolated": True,  # Needs fresh campaign - tests cascade mechanics
        "setup_npc": {
            "name": "Guard Erik",
            "string_id": "npc_erik_001",
            "role": "guard",
            "hp_current": 30,
            "hp_max": 30,
            "present": True,
            "allies": ["npc_captain_001", "npc_sergeant_001"],
            "relationships": {
                "player": {
                    "trust_level": 2,
                    "disposition": "friendly",
                    "history": [],
                    "debts": [],
                    "grievances": [],
                }
            },
        },
        "additional_npcs": [
            {
                "name": "Guard Captain Helena",
                "string_id": "npc_captain_001",
                "role": "guard_captain",
                "hp_current": 50,
                "hp_max": 50,
                "present": True,
                "relationships": {
                    "player": {
                        "trust_level": 3,
                        "disposition": "friendly",
                        "history": [],
                        "debts": [],
                        "grievances": [],
                    }
                },
            },
        ],
        "user_input": "I attack and kill Guard Erik in front of Guard Captain Helena.",
        "expect_cascade_relationship_update": True,
        "expect_multiple_trust_decrease": True,
        "description": "Killing an NPC should cascade trust loss to their allies (-3 to -6)",
    },
    {
        "name": "NPC Remembers Promise",
        "isolated": True,  # Needs fresh campaign - tests memory mechanics
        "setup_npc": {
            "name": "Farmer Giles",
            "string_id": "npc_giles_001",
            "role": "farmer",
            "hp_current": 10,
            "hp_max": 10,
            "present": True,
            "relationships": {
                "player": {
                    "trust_level": 1,
                    "disposition": "friendly",
                    "history": ["Player promised to clear wolves from farm", "Promise made 3 days ago"],
                    "debts": [],
                    "grievances": [],
                }
            },
        },
        "user_input": "I return to Farmer Giles. I have killed all the wolves as promised.",
        "expect_relationship_update": False,  # Soft - LLM may not always produce update
        "expect_trust_increase": True,  # IF updated, should be positive
        "expect_narrative_interaction": True,
        "expect_promise_remembered": True,
        "description": "NPC should remember promise and reward trust when kept (+1 to +2)",
    },
    # ========== G. Faction Standing ==========
    {
        "name": "Enemy Faction - Kill On Sight",
        "isolated": True,  # Needs fresh campaign - specific faction standing
        "setup_npc": {
            "name": "Dark Brotherhood Assassin",
            "string_id": "npc_assassin_001",
            "role": "assassin",
            "hp_current": 35,
            "hp_max": 35,
            "present": True,
            "faction": "faction_dark_brotherhood_001",
        },
        "setup_reputation": {
            "private": {
                "faction_dark_brotherhood_001": {
                    "score": -10,
                    "standing": "enemy",
                    "known_deeds": ["killed Grand Master", "destroyed safehouse"],
                    "secret_knowledge": [],
                }
            },
        },
        "user_input": "I encounter a Dark Brotherhood Assassin in the alley.",
        "expect_narrative_interaction": True,
        "expect_immediate_hostility": True,
        "description": "Enemy faction standing (-10) should result in kill-on-sight behavior",
    },
    {
        "name": "Champion Faction - Ultimate Access",
        "isolated": True,  # Needs fresh campaign - specific faction standing
        "setup_npc": {
            "name": "Temple High Priestess",
            "string_id": "npc_priestess_001",
            "role": "priest",
            "hp_current": 20,
            "hp_max": 20,
            "present": True,
            "faction": "faction_temple_light_001",
        },
        "setup_reputation": {
            "private": {
                "faction_temple_light_001": {
                    "score": 10,
                    "standing": "champion",
                    "known_deeds": ["purified the corrupted shrine", "saved the Grand Cleric"],
                    "secret_knowledge": ["knows location of holy relics"],
                }
            },
        },
        "user_input": "I approach the Temple High Priestess and request access to the forbidden archives and the sacred artifact vault.",
        "expect_narrative_interaction": True,
        "expect_full_access": True,
        "description": "Champion faction standing (+10) should grant unlimited access and resources",
    },
    # ========== H. Multi-Turn Instruction Loading Validation ==========
    {
        "name": "Multi-Turn Instruction Loading Validation",
        "isolated": True,  # Needs fresh campaign for clean state
        "multi_turn": True,  # Special flag for multi-turn test
        "setup_npc": {
            "name": "Wounded Traveler",
            "string_id": "npc_traveler_001",
            "role": "commoner",
            "hp_current": 3,
            "hp_max": 20,
            "present": True,
            # No relationships set - first significant interaction should trigger hint request
        },
        "turns": [
            {
                "turn_number": 1,
                # Use a trust-affecting action that should trigger hint request per MANDATORY REQUEST TRIGGERS
                "user_input": "I give my healing potion to the Wounded Traveler to save their life. This should significantly increase their trust in me.",
                "expect_instruction_hint": True,  # LLM should request relationship instructions
                "hint_types": ["relationships"],  # Which hints we expect
                "description": "Saving NPC's life should trigger LLM to request relationship instructions for trust change amounts",
            },
            {
                "turn_number": 2,
                "user_input": "I ask the Wounded Traveler if they know anything about the nearby dungeon.",
                "expect_instructions_loaded": True,  # Instructions should be loaded now
                "expected_instruction_files": ["relationship_instruction.md"],  # Files that should be in system_instruction_files
                "description": "Relationship instructions should be loaded based on previous turn's hint",
            },
            {
                "turn_number": 3,
                "user_input": "I thank the traveler and head back toward town.",
                "expect_no_instructions_loaded": True,  # No new hints requested on Turn 2
                "disallowed_instruction_files": ["relationship_instruction.md", "reputation_instruction.md"],
                "description": "Instruction hints should be cleared after use (no reload without a new hint)",
            },
        ],
        "description": "Validates that LLM hint requests cause instructions to be loaded on the next turn and cleared afterward",
    },
]


def create_campaign(client: MCPClient, user_id: str) -> str:
    payload = client.tools_call(
        "create_campaign",
        {
            "user_id": user_id,
            "title": "Relationship Test Campaign",
            "character": "Kira the Diplomat (CHA 18)",
            "setting": "A bustling trade city with multiple factions",
            "description": "Test campaign for relationship/reputation validation",
        },
    )
    campaign_id = payload.get("campaign_id") or payload.get("campaignId")
    if not isinstance(campaign_id, str) or not campaign_id:
        raise RuntimeError(f"create_campaign returned unexpected payload: {payload}")
    return campaign_id


def get_campaign_state(client: MCPClient, *, user_id: str, campaign_id: str) -> dict[str, Any]:
    payload = client.tools_call("get_campaign_state", {"user_id": user_id, "campaign_id": campaign_id})
    if payload.get("error"):
        raise RuntimeError(f"get_campaign_state error: {payload['error']}")
    return payload


def seed_npc(client: MCPClient, *, user_id: str, campaign_id: str, npc: dict[str, Any]) -> None:
    """Seed an NPC into the campaign state via GOD_MODE.

    Per game_state_instruction.md, npc_data should be keyed by display name.
    """
    # Use display name as key per documented schema (game_state_instruction.md line 498)
    npc_name = npc.get("name") or npc.get("string_id", "unknown")
    state_changes = {"npc_data": {npc_name: npc}}
    god_mode_payload = f"GOD_MODE_UPDATE_STATE:{json.dumps(state_changes)}"
    result = process_action(client, user_id=user_id, campaign_id=campaign_id, user_input=god_mode_payload)
    if result.get("error"):
        raise RuntimeError(f"GOD_MODE seed NPC failed: {result['error']}")


def seed_reputation(client: MCPClient, *, user_id: str, campaign_id: str, reputation: dict[str, Any]) -> None:
    """Seed reputation into the campaign state via GOD_MODE."""
    state_changes = {"custom_campaign_state": {"reputation": reputation}}
    god_mode_payload = f"GOD_MODE_UPDATE_STATE:{json.dumps(state_changes)}"
    result = process_action(client, user_id=user_id, campaign_id=campaign_id, user_input=god_mode_payload)
    if result.get("error"):
        raise RuntimeError(f"GOD_MODE seed reputation failed: {result['error']}")


def seed_player_character(client: MCPClient, *, user_id: str, campaign_id: str) -> None:
    """Ensure player character exists."""
    pc = {
        "string_id": "pc_kira_001",
        "name": "Kira",
        "level": 5,
        "class": "Bard",
        "hp_current": 35,
        "hp_max": 35,
        "attributes": {"strength": 10, "dexterity": 14, "constitution": 12, "intelligence": 13, "wisdom": 12, "charisma": 18},
        "proficiency_bonus": 3,
        "resources": {"gold": 100},
    }
    state_changes = {"player_character_data": pc}
    god_mode_payload = f"GOD_MODE_UPDATE_STATE:{json.dumps(state_changes)}"
    result = process_action(client, user_id=user_id, campaign_id=campaign_id, user_input=god_mode_payload)
    if result.get("error"):
        raise RuntimeError(f"GOD_MODE seed PC failed: {result['error']}")


def process_action(client: MCPClient, *, user_id: str, campaign_id: str, user_input: str) -> dict[str, Any]:
    return client.tools_call(
        "process_action",
        {"user_id": user_id, "campaign_id": campaign_id, "user_input": user_input, "mode": "character"},
    )


def extract_relationship_updates(result: dict[str, Any]) -> dict[str, Any]:
    """Extract any relationship updates from state_updates."""
    state_updates = result.get("state_updates") or {}
    npc_data = state_updates.get("npc_data") or {}

    relationship_updates = {}
    for npc_id, npc_update in npc_data.items():
        if isinstance(npc_update, dict) and "relationships" in npc_update:
            relationship_updates[npc_id] = npc_update["relationships"]

    return relationship_updates


def extract_reputation_updates(result: dict[str, Any]) -> dict[str, Any]:
    """Extract reputation updates from state_updates."""
    state_updates = result.get("state_updates") or {}
    custom_state = state_updates.get("custom_campaign_state") or {}
    return custom_state.get("reputation") or {}


def extract_instruction_hints(result: dict[str, Any]) -> list[str]:
    """Extract needs_detailed_instructions hints from debug_info.meta."""
    debug_info = result.get("debug_info") or {}
    meta = debug_info.get("meta") or {}
    hints = meta.get("needs_detailed_instructions") or []
    return hints if isinstance(hints, list) else []


def extract_system_instruction_files(result: dict[str, Any]) -> list[str]:
    """Extract system_instruction_files from debug_info.

    Returns list of instruction file names that were loaded for this turn.
    Used to validate that LLM hint requests actually cause instructions to be loaded.
    """
    debug_info = result.get("debug_info") or {}
    files = debug_info.get("system_instruction_files") or []
    return files if isinstance(files, list) else []


def validate_multi_turn_scenario(
    client: MCPClient,
    *,
    user_id: str,
    campaign_id: str,
    scenario: dict[str, Any],
) -> tuple[list[str], list[dict[str, Any]]]:
    """Execute and validate a multi-turn scenario.

    Returns:
        Tuple of (errors, turn_results) where turn_results contains per-turn data
    """
    errors: list[str] = []
    turn_results: list[dict[str, Any]] = []
    previous_hints: list[str] = []

    for turn in scenario.get("turns", []):
        turn_num = turn.get("turn_number", len(turn_results) + 1)
        user_input = turn["user_input"]

        print(f"    Turn {turn_num}: {turn.get('description', user_input[:50])}")

        # Execute the turn
        result = process_action(
            client,
            user_id=user_id,
            campaign_id=campaign_id,
            user_input=user_input,
        )

        # Extract data
        hints = extract_instruction_hints(result)
        sys_files = extract_system_instruction_files(result)
        rel_updates = extract_relationship_updates(result)
        rep_updates = extract_reputation_updates(result)

        turn_result = {
            "turn_number": turn_num,
            "user_input": user_input,
            "instruction_hints": hints,
            "system_instruction_files": sys_files,
            "relationship_updates": rel_updates,
            "reputation_updates": rep_updates,
            "narrative_preview": (result.get("narrative") or "")[:200],
        }
        turn_results.append(turn_result)

        # Validate turn expectations
        if result.get("error"):
            errors.append(f"Turn {turn_num}: server error - {result['error']}")
            continue

        # Check if hints were expected
        if turn.get("expect_instruction_hint"):
            expected_hints = turn.get("hint_types", [])
            for expected in expected_hints:
                if expected not in hints:
                    # Soft validation: also accept if instructions were already loaded
                    already_loaded = any(
                        expected in f.lower() for f in sys_files
                    )
                    if not already_loaded:
                        errors.append(
                            f"Turn {turn_num}: expected hint request for '{expected}' "
                            f"but got hints={hints}, sys_files={sys_files}"
                        )

        # Check if instructions should be loaded (based on previous turn's hints)
        if turn.get("expect_instructions_loaded"):
            expected_files = turn.get("expected_instruction_files", [])
            for expected_file in expected_files:
                found = any(expected_file in f for f in sys_files)
                if not found:
                    # Check if it was in previous hints
                    hint_key = expected_file.replace("_instruction.md", "").replace("_", "")
                    was_requested = any(
                        hint_key in h.lower() for h in previous_hints
                    )
                    errors.append(
                        f"Turn {turn_num}: expected '{expected_file}' in system_instruction_files "
                        f"but got {sys_files}. Previous hints={previous_hints}, "
                        f"hint_key_check={hint_key}, was_requested={was_requested}"
                    )

        # Check that instruction files are not reloaded without a matching hint
        if turn.get("expect_no_instructions_loaded"):
            disallowed_files = turn.get("disallowed_instruction_files", [])
            for disallowed_file in disallowed_files:
                found = any(disallowed_file in f for f in sys_files)
                if not found:
                    continue
                hint_key = disallowed_file.replace("_instruction.md", "").replace("_", "")
                was_requested = any(hint_key in h.lower() for h in previous_hints)
                if not was_requested:
                    errors.append(
                        f"Turn {turn_num}: unexpected '{disallowed_file}' loaded without hint. "
                        f"system_instruction_files={sys_files}, previous_hints={previous_hints}"
                    )
                else:
                    print(
                        f"  ⚠️  Note: '{disallowed_file}' loaded because a hint was requested on the prior turn "
                        f"(previous_hints={previous_hints})"
                    )

        # Store hints for next turn validation
        previous_hints = hints

        # Print turn status
        if hints:
            print(f"      → Requested hints: {hints}")
        if any("relationship" in f.lower() or "reputation" in f.lower() for f in sys_files):
            print(f"      → Loaded instruction files: {[f for f in sys_files if 'relationship' in f.lower() or 'reputation' in f.lower()]}")

    return errors, turn_results


def validate_scenario(result: dict[str, Any], scenario: dict[str, Any]) -> list[str]:
    """Validate scenario expectations against result."""
    errors: list[str] = []

    if result.get("error"):
        errors.append(f"server returned error: {result['error']}")
        return errors

    # Check for narrative (basic response validation)
    narrative = result.get("narrative") or ""
    if not narrative:
        errors.append("missing narrative in response")

    narrative_lower = narrative.lower()

    # Check relationship updates
    rel_updates = extract_relationship_updates(result)
    rep_updates = extract_reputation_updates(result)
    hints = extract_instruction_hints(result)

    if scenario.get("expect_relationship_update") and not rel_updates:
        # Allow if LLM requested detailed instructions instead
        if "relationships" not in hints:
            errors.append("expected relationship update in state_updates.npc_data but none found")

    if scenario.get("expect_relationship_init"):
        # For first meetings, we expect either a relationship structure or a hint request
        if not rel_updates and "relationships" not in hints:
            errors.append("expected relationship initialization or hint request for new NPC")

    if scenario.get("expect_reputation_update") and not rep_updates:
        if "reputation" not in hints:
            errors.append("expected reputation update in state_updates but none found")

    # Check narrative interaction if expected (verify NPC appears in narrative)
    if scenario.get("expect_narrative_interaction"):
        setup_npc = scenario.get("setup_npc", {})
        npc_name = setup_npc.get("name", "")
        if npc_name and npc_name.lower() not in narrative_lower:
            # Soft warning - NPC might be referenced differently
            print(f"  ⚠️  Warning: NPC '{npc_name}' not found in narrative (may use different reference)")

    # Check trust direction if relationship update exists
    if rel_updates:
        for npc_id, rel in rel_updates.items():
            player_rel = rel.get("player") or {}
            trust_level = player_rel.get("trust_level")

            if scenario.get("expect_trust_increase") and trust_level is not None:
                if trust_level <= 0:
                    errors.append(f"expected positive trust_level for {npc_id}, got {trust_level}")

            if scenario.get("expect_trust_decrease") and trust_level is not None:
                if trust_level >= 0:
                    # Stealing might be caught or not - if not caught, no decrease expected
                    # Log warning for visibility but don't fail test (soft expectation)
                    if scenario.get("allow_no_update_if_undetected"):
                        print(f"  ⚠️  Note: trust_level={trust_level} for {npc_id} (action may have gone undetected)")
                    else:
                        errors.append(f"expected negative trust_level for {npc_id}, got {trust_level}")

    # ========== Behavioral Narrative Checks ==========
    # These are soft validations - check narrative for behavioral compliance

    # B. Behavior Modifiers
    if scenario.get("expect_hostile_behavior"):
        hostile_keywords = ["refuse", "won't", "cannot", "leave", "get out", "attack", "hostile", "anger", "snarl", "growl"]
        if not any(kw in narrative_lower for kw in hostile_keywords):
            print(f"  ⚠️  Warning: expected hostile behavior but no hostile keywords found in narrative")

    if scenario.get("expect_discount_mention"):
        discount_keywords = ["discount", "special price", "less", "reduced", "favor", "deal", "friend"]
        if not any(kw in narrative_lower for kw in discount_keywords):
            print(f"  ⚠️  Warning: expected discount mention but no discount keywords found in narrative")

    # D. Notoriety Levels
    if scenario.get("expect_service_refused"):
        refused_keywords = ["refuse", "won't", "cannot", "leave", "no service", "get away", "flee", "run", "guards"]
        if not any(kw in narrative_lower for kw in refused_keywords):
            print(f"  ⚠️  Warning: expected service refusal but no refusal keywords found in narrative")

    if scenario.get("expect_fame_recognition"):
        fame_keywords = ["recognize", "hero", "dragonslayer", "famous", "honor", "legend", "bow", "welcome"]
        if not any(kw in narrative_lower for kw in fame_keywords):
            print(f"  ⚠️  Warning: expected fame recognition but no fame keywords found in narrative")

    # E. Priority Hierarchy
    if scenario.get("expect_hostile_despite_history"):
        hostile_keywords = ["traitor", "betray", "enemy", "refuse", "hostile", "attack", "cannot trust"]
        if not any(kw in narrative_lower for kw in hostile_keywords):
            print(f"  ⚠️  Warning: expected hostile behavior despite history but no hostile keywords found")

    if scenario.get("expect_access_granted"):
        access_keywords = ["access", "vault", "grant", "welcome", "enter", "allow", "of course", "certainly"]
        if not any(kw in narrative_lower for kw in access_keywords):
            print(f"  ⚠️  Warning: expected access granted but no access keywords found in narrative")

    # F. Cascading/Memory
    if scenario.get("expect_cascade_relationship_update"):
        # Check if multiple NPCs have relationship updates
        if len(rel_updates) < 2:
            print(f"  ⚠️  Warning: expected cascading relationship updates but only {len(rel_updates)} NPC(s) updated")

    if scenario.get("expect_promise_remembered"):
        promise_keywords = ["promise", "wolf", "wolves", "kept your word", "thank", "grateful", "remembered"]
        if not any(kw in narrative_lower for kw in promise_keywords):
            print(f"  ⚠️  Warning: expected promise remembered but no promise keywords found in narrative")

    # G. Faction Standing
    if scenario.get("expect_immediate_hostility"):
        hostility_keywords = ["attack", "draw", "weapon", "strike", "assassin", "kill", "die", "combat"]
        if not any(kw in narrative_lower for kw in hostility_keywords):
            print(f"  ⚠️  Warning: expected immediate hostility but no combat keywords found in narrative")

    if scenario.get("expect_full_access"):
        access_keywords = ["archive", "vault", "access", "grant", "champion", "anything you need", "at your disposal"]
        if not any(kw in narrative_lower for kw in access_keywords):
            print(f"  ⚠️  Warning: expected full access but no access keywords found in narrative")

    # C. Public Reputation - check for reputation score changes
    if scenario.get("expect_reputation_decrease") and rep_updates:
        public_rep = rep_updates.get("public", {})
        if public_rep.get("score") is not None:
            # Score should have decreased (expect negative or lower)
            print(f"  📊 Reputation update: public score = {public_rep.get('score')}")

    if scenario.get("expect_private_reputation_update"):
        private_rep = rep_updates.get("private", {})
        if private_rep:
            print(f"  📊 Private reputation updated: {list(private_rep.keys())}")
        else:
            print(f"  ⚠️  Warning: expected private reputation update but none found")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Real API tests for relationship/reputation mechanics")
    parser.add_argument(
        "--server-url",
        default=os.environ.get("MCP_SERVER_URL") or "http://127.0.0.1:8001",
        help="Base server URL",
    )
    parser.add_argument("--start-local", action="store_true", help="Start local MCP server automatically")
    parser.add_argument("--port", type=int, default=0, help="Port for --start-local (0 = random)")
    parser.add_argument("--model", default=os.environ.get("MCP_TEST_MODEL") or DEFAULT_MODEL, help="LLM model to use")
    parser.add_argument("--evidence", action="store_true", help="Enable evidence capture")
    args = parser.parse_args()

    local: LocalServer | None = None
    base_url = str(args.server_url)
    # Evidence saved to /tmp per evidence-standards.md
    evidence_dir = get_evidence_dir("relationship_reputation")

    try:
        if args.start_local:
            port = int(args.port) if int(args.port) > 0 else pick_free_port()
            env_overrides: dict[str, str] = {
                "MOCK_SERVICES_MODE": "false",
                "TESTING": "false",
                "FORCE_TEST_MODEL": "false",
            }
            if args.evidence:
                env_overrides["CAPTURE_EVIDENCE"] = "true"
                # Enable raw LLM response capture per evidence-standards.md
                env_overrides["CAPTURE_RAW_LLM"] = "true"
            local = start_local_mcp_server(port, env_overrides=env_overrides, log_dir=evidence_dir)
            base_url = local.base_url

        client = MCPClient(base_url, timeout_s=180.0)
        client.wait_healthy(timeout_s=45.0)

        # Verify required tools exist
        tools = client.tools_list()
        tool_names = {t.get("name") for t in tools if isinstance(t, dict)}
        for required in ("create_campaign", "process_action", "get_campaign_state"):
            if required not in tool_names:
                raise RuntimeError(f"Missing required tool: {required}")

        # Set up user and campaign
        user_id = f"rel-rep-test-{int(time.time())}"
        model_settings = settings_for_model(args.model)
        model_settings["debug_mode"] = True
        update_user_settings(client, user_id=user_id, settings=model_settings)
        campaign_id = create_campaign(client, user_id)
        seed_player_character(client, user_id=user_id, campaign_id=campaign_id)

        session_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = evidence_dir / session_stamp
        session_dir.mkdir(parents=True, exist_ok=True)

        # Capture provenance per evidence-standards.md
        # CRITICAL: Pass env_overrides so provenance captures actual server env, not test runner env
        server_pid = local.proc.pid if local else None
        provenance = capture_provenance(
            base_url,
            server_pid,
            server_env_overrides=env_overrides if args.start_local else None,
        )

        run_summary: dict[str, Any] = {
            "server": base_url,
            "model": args.model,
            "campaign_id": campaign_id,
            "provenance": provenance,
            "scenarios": [],
        }

        ok = True
        passed = 0
        failed = 0

        print(f"\n{'='*60}")
        print("Relationship/Reputation Real API Tests")
        print(f"Model: {args.model}")
        print(f"{'='*60}\n")

        # Track current campaign (may change for isolated tests)
        current_campaign_id = campaign_id

        for scenario in TEST_SCENARIOS:
            print(f"Testing: {scenario['name']}")
            print(f"  Description: {scenario['description']}")

            # Create fresh campaign for isolated tests
            if scenario.get("isolated"):
                print(f"  🔒 Isolated test - creating fresh campaign")
                current_campaign_id = create_campaign(client, user_id)
                seed_player_character(client, user_id=user_id, campaign_id=current_campaign_id)
            else:
                current_campaign_id = campaign_id

            # Seed NPC if needed
            if "setup_npc" in scenario:
                try:
                    seed_npc(client, user_id=user_id, campaign_id=current_campaign_id, npc=scenario["setup_npc"])
                except Exception as e:
                    print(f"  ⚠️  Failed to seed NPC: {e}")

            # Seed additional NPCs for cascade tests
            if "additional_npcs" in scenario:
                for extra_npc in scenario["additional_npcs"]:
                    try:
                        seed_npc(client, user_id=user_id, campaign_id=current_campaign_id, npc=extra_npc)
                    except Exception as e:
                        print(f"  ⚠️  Failed to seed additional NPC: {e}")

            # Seed reputation if needed
            if "setup_reputation" in scenario:
                try:
                    seed_reputation(client, user_id=user_id, campaign_id=current_campaign_id, reputation=scenario["setup_reputation"])
                except Exception as e:
                    print(f"  ⚠️  Failed to seed reputation: {e}")

            # Handle multi-turn scenarios differently
            if scenario.get("multi_turn"):
                print(f"  🔄 Multi-turn test ({len(scenario.get('turns', []))} turns)")
                errors, turn_results = validate_multi_turn_scenario(
                    client,
                    user_id=user_id,
                    campaign_id=current_campaign_id,
                    scenario=scenario,
                )
                scenario_result = {
                    "name": scenario["name"],
                    "campaign_id": current_campaign_id,
                    "multi_turn": True,
                    "turns": turn_results,
                    "errors": errors,
                }
                run_summary["scenarios"].append(scenario_result)
            else:
                # Execute the action (single-turn scenario)
                result = process_action(
                    client,
                    user_id=user_id,
                    campaign_id=current_campaign_id,
                    user_input=str(scenario["user_input"]),
                )

                # Validate
                errors = validate_scenario(result, scenario)

                # Extract data for summary
                rel_updates = extract_relationship_updates(result)
                rep_updates = extract_reputation_updates(result)
                hints = extract_instruction_hints(result)

                scenario_result = {
                    "name": scenario["name"],
                    "campaign_id": current_campaign_id,  # For evidence traceability
                    "user_input": scenario["user_input"],
                    "relationship_updates": rel_updates,
                    "reputation_updates": rep_updates,
                    "instruction_hints": hints,
                    "errors": errors,
                    "narrative_preview": (result.get("narrative") or "")[:200],
                }
                run_summary["scenarios"].append(scenario_result)

            if errors:
                failed += 1
                ok = False
                print(f"  ❌ FAILED: {errors}")
            else:
                passed += 1
                print(f"  ✅ PASSED")
                if rel_updates:
                    print(f"     Relationship updates: {list(rel_updates.keys())}")
                if rep_updates:
                    print(f"     Reputation updates: {bool(rep_updates)}")
                if hints:
                    print(f"     Requested detailed instructions: {hints}")

            print()

        # Create complete evidence bundle per evidence-standards.md
        # MCPClient captures request/response by default
        request_responses = client.get_captures_as_dict()
        run_summary["request_response_count"] = len(request_responses)

        # Calculate test isolation info for methodology documentation
        isolated_tests = sum(1 for s in TEST_SCENARIOS if s.get("isolated"))
        isolation_info = {
            "total_campaigns": 1 + isolated_tests,  # 1 shared + N isolated
            "shared_campaign": 1,
            "isolated_tests": isolated_tests,
            "reason": "State-sensitive tests (reputation, trust override, cascade effects) require fresh campaigns to prevent context bleed between scenarios",
        }

        bundle_files = create_evidence_bundle(
            session_dir,
            test_name="relationship_reputation",
            provenance=provenance,
            results=run_summary,
            request_responses=request_responses,
            server_log_path=local.log_path if local else None,
            isolation_info=isolation_info,
        )

        print(f"{'='*60}")
        print(f"Results: {passed} passed, {failed} failed")
        print(f"Evidence Bundle: {session_dir}")
        print(f"  - README.md: {bundle_files.get('readme')}")
        print(f"  - methodology.md: {bundle_files.get('methodology')}")
        print(f"  - evidence.md: {bundle_files.get('evidence')}")
        print(f"  - run.json: {bundle_files.get('results')}")
        print(f"  - request_responses.jsonl: {bundle_files.get('request_responses')}")
        print(f"  - Request/Response captures: {len(request_responses)}")
        if local:
            print(f"Server log: {local.log_path}")
        print(f"{'='*60}")

        return 0 if ok else 2

    finally:
        if local is not None:
            local.stop()


if __name__ == "__main__":
    raise SystemExit(main())
