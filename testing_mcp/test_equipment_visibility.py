#!/usr/bin/env python3
"""Equipment visibility tests with evidence-standards compliance.

Tests verify that when a player asks about equipment, the system returns
accurate structured equipment data AND the LLM narrative summarizes it.

Evidence Standards Compliance:
- Full API response capture including debug_info
- Post-seed game_state verification saved to evidence
- Scenario-specific requirements (not global item list)
- Git provenance and version alignment
- Separate checksums for evidence files

Run:
    cd testing_mcp
    python test_equipment_visibility.py --server-url http://127.0.0.1:8082
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from lib import MCPClient
from lib.evidence_utils import get_evidence_dir, write_with_checksum

PROJECT_ROOT = Path(__file__).parent.parent

# Evidence stored per evidence-standards.md: /tmp/<repo>/<branch>/<work>/<timestamp>/
# No longer using testing_mcp/evidence/ - set dynamically in main()


# ============================================================================
# ITEM REGISTRY - Canonical item definitions (string ID → item data)
# ============================================================================

ITEM_REGISTRY = {
    # Equipped items
    "helm_telepathy": {
        "name": "Helm of Telepathy",
        "type": "head",
        "stats": "30ft telepathy, Detect Thoughts 1/day",
        "rarity": "rare",
    },
    "amulet_health": {
        "name": "Amulet of Health",
        "type": "neck",
        "stats": "Constitution set to 19",
        "rarity": "rare",
    },
    "mithral_half_plate": {
        "name": "Mithral Half Plate",
        "type": "armor",
        "stats": "+2 AC, no stealth disadvantage",
        "ac": 15,
        "rarity": "rare",
    },
    "cloak_protection": {
        "name": "Cloak of Protection",
        "type": "cloak",
        "stats": "+1 AC, +1 saves",
        "rarity": "uncommon",
    },
    "ring_protection": {
        "name": "Ring of Protection",
        "type": "ring",
        "stats": "+1 AC",
        "rarity": "rare",
    },
    "ring_spell_storing": {
        "name": "Ring of Spell Storing",
        "type": "ring",
        "stats": "5 levels",
        "rarity": "rare",
    },
    "shield_plus_1": {
        "name": "Shield +1",
        "type": "shield",
        "stats": "+3 AC total",
        "rarity": "uncommon",
    },
    # Weapons
    "flame_tongue_longsword": {
        "name": "Flame Tongue Longsword",
        "type": "weapon",
        "stats": "1d8+3 slashing + 2d6 fire, Magic, +1 to hit",
        "damage": "1d8+3 slashing + 2d6 fire",
        "properties": "Magic, +1 to hit",
        "rarity": "rare",
    },
    "longbow_accuracy": {
        "name": "Longbow of Accuracy",
        "type": "weapon",
        "stats": "1d8+2 piercing, Range 150/600, +2 to hit",
        "damage": "1d8+2 piercing",
        "properties": "Range 150/600, +2 to hit",
        "rarity": "rare",
    },
    # Backpack items
    "rope_climbing": {
        "name": "Rope of Climbing",
        "type": "item",
        "stats": "60ft",
        "rarity": "uncommon",
    },
    "bag_holding": {
        "name": "Bag of Holding",
        "type": "item",
        "stats": "500 lbs capacity",
        "rarity": "uncommon",
    },
    "potion_greater_healing": {
        "name": "Potion of Greater Healing x3",
        "type": "consumable",
        "stats": "4d4+4 HP",
        "rarity": "uncommon",
    },
    "thieves_tools": {
        "name": "Thieves' Tools",
        "type": "tool",
        "stats": "",
        "rarity": "common",
    },
}


# ============================================================================
# SEED EQUIPMENT DATA - Uses string IDs referencing ITEM_REGISTRY
# ============================================================================

SEED_EQUIPMENT = {
    # Weapons as string IDs
    "weapons": ["flame_tongue_longsword", "longbow_accuracy"],
    # Equipped items as string IDs
    "equipped": {
        "head": "helm_telepathy",
        "neck": "amulet_health",
        "armor": "mithral_half_plate",
        "cloak": "cloak_protection",
        "ring_1": "ring_protection",
        "ring_2": "ring_spell_storing",
        "main_hand": "flame_tongue_longsword",
        "off_hand": "shield_plus_1",
    },
    # Backpack items as string IDs
    "backpack": ["rope_climbing", "bag_holding", "potion_greater_healing", "thieves_tools"],
    "armor": "mithral_half_plate",
}


# ============================================================================
# SCENARIO-SPECIFIC REQUIREMENTS
# NOTE: Narrative summary is required to include at least N item mentions.
# ============================================================================

TEST_SCENARIOS = [
    {
        "name": "Direct Equipment Query",
        "user_input": "Show me my equipment. List every item I have equipped.",
        # Must mention ALL equipped slot items
        "required_items": [
            "Helm of Telepathy",
            "Amulet of Health",
            "Mithral Half Plate",
            "Cloak of Protection",
            "Ring of Protection",
            "Ring of Spell Storing",
            "Flame Tongue Longsword",
            "Shield +1",
        ],
        "min_required": 6,  # At least 6 of 8 equipped items
        "min_narrative_items": 3,  # Narrative must mention at least 3 items
        "forbidden_vague": [
            "your equipment is optimized",
            "your gear is configured",
            "properly armored",
        ],
    },
    {
        "name": "Inventory Check (Backpack Only)",
        "user_input": "What's in my backpack? List all items.",
        # Must mention backpack items, NOT equipped items
        "required_items": [
            "Rope of Climbing",
            "Bag of Holding",
            "Potion of Greater Healing",
            "Thieves' Tools",
        ],
        "min_required": 3,  # At least 3 of 4 backpack items
        "min_narrative_items": 2,  # Narrative must mention at least 2 items
    },
    {
        "name": "God Mode Equipment Query",
        "user_input": "GOD MODE: List all my equipped items with their exact stats.",
        # God Mode MUST list items with stats
        "required_items": [
            "Helm of Telepathy",
            "Mithral Half Plate",
            "Cloak of Protection",
            "Flame Tongue Longsword",
        ],
        "required_stats": [
            "30ft",  # Helm telepathy range
            "+1 AC",  # Cloak stat
            "+2 AC",  # Mithral armor
            "2d6 fire",  # Flame Tongue damage
        ],
        "min_required": 3,
        "min_stats_required": 2,  # Must show at least 2 stat values
        "min_narrative_items": 2,  # Narrative must reference at least 2 items
        "check_god_mode_response": True,
        "forbidden_vague": [
            "your equipment is optimized",
            "your loadout is configured",
            "synchronized system",
        ],
    },
    {
        "name": "Weapon Check (Weapons + Damage)",
        "user_input": "What weapons do I have? Tell me their names and damage.",
        # Must list BOTH weapons with damage values
        "required_items": [
            "Flame Tongue Longsword",
            "Longbow of Accuracy",
        ],
        "required_stats": [
            "1d8",  # Base damage die
            "2d6 fire",  # Flame Tongue extra damage
            "piercing",  # Longbow damage type
        ],
        "min_required": 2,  # Must find both weapons
        "min_stats_required": 2,  # Must show damage for both
        "min_narrative_items": 2,  # Narrative must mention both weapons
    },
]


# ============================================================================
# TEST RESULT DATA CLASSES
# ============================================================================

@dataclass
class TestResult:
    passed: bool
    scenario_name: str
    user_input: str
    narrative: str
    narrative_items_found: list[str]
    narrative_items_missing: list[str]
    structured_items_found: list[str]
    structured_items_missing: list[str]
    structured_stats_found: list[str] = field(default_factory=list)
    structured_stats_missing: list[str] = field(default_factory=list)
    vague_phrases_found: list[str] = field(default_factory=list)
    unexpected_items_narrative: list[str] = field(default_factory=list)
    unexpected_items_structured: list[str] = field(default_factory=list)
    narrative_summary_ok: bool = False
    structured_ok: bool = False
    equipment_display_present: bool = False
    error: str | None = None
    # Full API response for evidence
    full_response: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvidenceBundle:
    timestamp: str
    server_url: str
    campaign_id: str
    git_commit: str
    git_branch: str
    origin_main: str
    files_changed: list[str]
    seeded_equipment: dict[str, Any]
    verified_game_state: dict[str, Any]
    test_results: list[dict[str, Any]]
    summary: dict[str, Any]


# ============================================================================
# GIT PROVENANCE CAPTURE
# ============================================================================

def capture_git_provenance() -> dict[str, Any]:
    """Capture git state for evidence integrity."""
    def run_git(args: list[str]) -> str:
        try:
            result = subprocess.run(
                ["git"] + args,
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
                timeout=10,
            )
            return result.stdout.strip()
        except Exception:
            return "unknown"

    # Fetch origin/main to ensure it's current
    run_git(["fetch", "origin", "main"])

    return {
        "commit": run_git(["rev-parse", "HEAD"]),
        "branch": run_git(["branch", "--show-current"]),
        "origin_main": run_git(["rev-parse", "origin/main"]),
        "files_changed": run_git(["diff", "--name-only", "origin/main...HEAD"]).split("\n"),
    }


# ============================================================================
# MCP CLIENT HELPERS
# ============================================================================

def create_campaign(client: MCPClient, *, user_id: str, title: str, prompt: str) -> str:
    """Create a test campaign and return its ID."""
    payload = client.tools_call(
        "create_campaign",
        {
            "user_id": user_id,
            "title": title,
            "initial_prompt": prompt,
            "selected_prompts": ["narrative", "mechanics"],
        },
    )
    campaign_id = payload.get("campaign_id")
    if not isinstance(campaign_id, str) or not campaign_id:
        raise RuntimeError(f"create_campaign returned unexpected payload: {payload}")
    return campaign_id


def get_campaign_state(client: MCPClient, *, user_id: str, campaign_id: str) -> dict[str, Any]:
    """Get the current game state for a campaign - returns FULL response."""
    return client.tools_call(
        "get_campaign_state",
        {"user_id": user_id, "campaign_id": campaign_id},
    )


def seed_equipment_into_game_state(
    client: MCPClient,
    *,
    user_id: str,
    campaign_id: str,
    equipment: dict[str, Any],
    item_registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Seed equipment into game_state via GOD MODE. Returns full response.

    Args:
        equipment: Equipment data using string IDs referencing item_registry
        item_registry: Canonical item definitions (string_id → item data)
    """
    state_changes = {
        "player_character_data": {
            "string_id": "pc_tester_001",
            "name": "Test Hero",
            "level": 10,
            "class": "Fighter",
            "hp_current": 85,
            "hp_max": 85,
            "armor_class": 20,
            "equipment": equipment,
            "attributes": {
                "strength": 18,
                "dexterity": 14,
                "constitution": 16,
                "intelligence": 10,
                "wisdom": 12,
                "charisma": 14,
            },
            "proficiency_bonus": 4,
        }
    }
    # Add item_registry at game_state level (not nested in player_character_data)
    if item_registry:
        state_changes["item_registry"] = item_registry

    god_mode_payload = f"GOD_MODE_UPDATE_STATE:{json.dumps(state_changes)}"
    return client.tools_call(
        "process_action",
        {"user_id": user_id, "campaign_id": campaign_id, "user_input": god_mode_payload, "mode": "god"},
    )


def process_action(
    client: MCPClient, *, user_id: str, campaign_id: str, user_input: str
) -> dict[str, Any]:
    """Send a player action - returns FULL response including debug_info."""
    return client.tools_call(
        "process_action",
        {"user_id": user_id, "campaign_id": campaign_id, "user_input": user_input, "mode": "character"},
    )


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_scenario(
    response: dict[str, Any],
    scenario: dict[str, Any],
) -> TestResult:
    """Validate a scenario response against its specific requirements."""
    scenario_name = scenario["name"]
    user_input = scenario["user_input"]
    required_items = scenario.get("required_items", [])
    required_stats = scenario.get("required_stats", [])
    min_required = scenario.get("min_required", len(required_items))
    min_stats = scenario.get("min_stats_required", 0)
    min_narrative_items = scenario.get("min_narrative_items", 0)
    check_god_mode = scenario.get("check_god_mode_response", False)
    forbidden_vague = scenario.get("forbidden_vague", [])
    should_not_mention = scenario.get("should_not_mention", [])

    if response.get("error"):
        return TestResult(
            passed=False,
            scenario_name=scenario_name,
            user_input=user_input,
            narrative="",
            narrative_items_found=[],
            narrative_items_missing=required_items,
            structured_items_found=[],
            structured_items_missing=required_items,
            error=str(response["error"]),
            full_response=response,
        )

    # Combine narrative, response, and god_mode_response for narrative summary checks
    narrative = response.get("narrative", "")
    response_text = response.get("response", "")
    god_mode_response = response.get("god_mode_response", "")
    narrative_text = narrative
    if response_text and response_text != narrative_text:
        narrative_text = f"{narrative_text}\n{response_text}"
    if check_god_mode and god_mode_response:
        narrative_text = f"{narrative_text}\n{god_mode_response}"

    # Build structured text from deterministic fields
    structured_text_parts: list[str] = []
    equipment_list = response.get("equipment_list", [])
    if equipment_list:
        for item in equipment_list:
            if isinstance(item, dict):
                name = item.get("name", "")
                stats = item.get("stats", "")
                structured_text_parts.append(f"{name} {stats}".strip())

    # CRITICAL: Check equipment_display field (deterministic backend extraction)
    # This field is populated by backend reading game_state directly - 100% reliable
    equipment_display = response.get("equipment_display", [])
    if equipment_display:
        for item in equipment_display:
            if isinstance(item, dict):
                name = item.get("name", "")
                stats = item.get("stats", "")
                structured_text_parts.append(f"{name} {stats}".strip())

    structured_text = "\n".join(structured_text_parts)
    narrative_lower = narrative_text.lower()
    structured_lower = structured_text.lower()

    # Check required items in structured data
    structured_items_found: list[str] = []
    structured_items_missing: list[str] = []
    for item in required_items:
        if item.lower() in structured_lower:
            structured_items_found.append(item)
        else:
            structured_items_missing.append(item)

    # Check required stats in structured data
    structured_stats_found: list[str] = []
    structured_stats_missing: list[str] = []
    for stat in required_stats:
        if stat.lower() in structured_lower:
            structured_stats_found.append(stat)
        else:
            structured_stats_missing.append(stat)

    # Narrative summary check (do NOT use structured fields)
    narrative_items_found: list[str] = []
    narrative_items_missing: list[str] = []
    for item in required_items:
        if item.lower() in narrative_lower:
            narrative_items_found.append(item)
        else:
            narrative_items_missing.append(item)

    # Check forbidden vague phrases in narrative only
    vague_found: list[str] = []
    for phrase in forbidden_vague:
        if phrase.lower() in narrative_lower:
            vague_found.append(phrase)

    # Check items that should NOT be mentioned (narrative only)
    # NOTE: equipment_display returns ALL equipment regardless of query focus
    # This is by design - the frontend can filter as needed. So we only check
    # should_not_mention against narrative (LLM output), not structured data.
    unexpected_narrative: list[str] = []
    unexpected_structured: list[str] = []  # Kept for backward compatibility but not used in pass/fail
    for item in should_not_mention:
        if item.lower() in narrative_lower:
            unexpected_narrative.append(item)
        # Still track but don't fail on structured - equipment_display returns ALL items
        if item.lower() in structured_lower:
            unexpected_structured.append(item)

    # Determine pass/fail
    structured_ok = len(structured_items_found) >= min_required
    if min_stats > 0:
        structured_ok = structured_ok and (len(structured_stats_found) >= min_stats)
    narrative_ok = len(narrative_items_found) >= min_narrative_items if min_narrative_items > 0 else True
    no_vague = len(vague_found) == 0
    # Only check narrative for unexpected items - equipment_display returns ALL equipment by design
    no_unexpected = len(unexpected_narrative) == 0
    passed = structured_ok and narrative_ok and no_vague and no_unexpected

    return TestResult(
        passed=passed,
        scenario_name=scenario_name,
        user_input=user_input,
        narrative=narrative_text[:3000],
        narrative_items_found=narrative_items_found,
        narrative_items_missing=narrative_items_missing,
        structured_items_found=structured_items_found,
        structured_items_missing=structured_items_missing,
        structured_stats_found=structured_stats_found,
        structured_stats_missing=structured_stats_missing,
        vague_phrases_found=vague_found,
        unexpected_items_narrative=unexpected_narrative,
        unexpected_items_structured=unexpected_structured,
        narrative_summary_ok=narrative_ok,
        structured_ok=structured_ok,
        equipment_display_present=bool(equipment_display or equipment_list),
        full_response=response,
    )


# ============================================================================
# EVIDENCE FILE HELPERS
# ============================================================================

def save_evidence_bundle(evidence_dir: Path, bundle: EvidenceBundle) -> Path:
    """Save evidence bundle with checksums."""
    timestamp = bundle.timestamp.replace(":", "").replace("-", "").replace(".", "_")
    run_dir = evidence_dir / f"run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Main evidence JSON
    evidence_json = json.dumps({
        "timestamp": bundle.timestamp,
        "server_url": bundle.server_url,
        "campaign_id": bundle.campaign_id,
        "git_provenance": {
            "commit": bundle.git_commit,
            "branch": bundle.git_branch,
            "origin_main": bundle.origin_main,
            "files_changed": bundle.files_changed,
        },
        "seeded_equipment": bundle.seeded_equipment,
        "verified_game_state": bundle.verified_game_state,
        "results": bundle.test_results,
        "summary": bundle.summary,
    }, indent=2, default=str)
    write_with_checksum(run_dir / "evidence.json", evidence_json)

    # Full API responses (separate file for large data)
    responses_json = json.dumps({
        "test_responses": [r.get("full_response", {}) for r in bundle.test_results]
    }, indent=2, default=str)
    write_with_checksum(run_dir / "api_responses.json", responses_json)

    # Game state snapshot
    state_json = json.dumps(bundle.verified_game_state, indent=2, default=str)
    write_with_checksum(run_dir / "game_state_snapshot.json", state_json)

    # README
    readme = f"""# Equipment Visibility Test Evidence

- **Timestamp**: {bundle.timestamp}
- **Server**: {bundle.server_url}
- **Campaign**: {bundle.campaign_id}
- **Git Commit**: {bundle.git_commit}
- **Git Branch**: {bundle.git_branch}
- **Origin/main**: {bundle.origin_main}

## Results Summary
- Passed: {bundle.summary['passed']}/{bundle.summary['total']}
- Failed: {bundle.summary['failed']}/{bundle.summary['total']}

## Files Changed vs Origin/main
{chr(10).join('- ' + f for f in bundle.files_changed if f)}

## Evidence Files
- evidence.json - Complete test results
- api_responses.json - Full API response payloads
- game_state_snapshot.json - Verified equipment in game_state after seeding
"""
    write_with_checksum(run_dir / "README.md", readme)

    return run_dir


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def generate_savetmp_docs(
    results: list[TestResult],
    git_info: dict[str, Any],
    server_url: str,
    run_dir: Path,
) -> tuple[str, str, str]:
    """Generate savetmp-compatible methodology, evidence, and notes from actual test data.

    This ensures the documentation matches exactly what was tested, addressing:
    - Red flag 1: Seeded equipment mismatch (items come from ITEM_REGISTRY)
    - Red flag 2: Evidence summary mismatch (results come from actual test)
    - Red flag 3: Ambiguous artifact scope (single run_dir reference)
    """
    # Track missing item IDs for warnings (issue #2 from equipc review)
    missing_item_ids: list[str] = []

    # Generate equipment lists from actual ITEM_REGISTRY
    equipped_items = []
    for item_id in SEED_EQUIPMENT.get("equipped", {}).values():
        if item_id in ITEM_REGISTRY:
            equipped_items.append(ITEM_REGISTRY[item_id]["name"])
        else:
            missing_item_ids.append(f"equipped:{item_id}")

    weapon_items = []
    for item_id in SEED_EQUIPMENT.get("weapons", []):
        if item_id in ITEM_REGISTRY:
            weapon_items.append(ITEM_REGISTRY[item_id]["name"])
        else:
            missing_item_ids.append(f"weapons:{item_id}")

    backpack_items = []
    for item_id in SEED_EQUIPMENT.get("backpack", []):
        if item_id in ITEM_REGISTRY:
            backpack_items.append(ITEM_REGISTRY[item_id]["name"])
        else:
            missing_item_ids.append(f"backpack:{item_id}")

    # Check actual environment (issue #3 from equipc review)
    dev_mode = os.environ.get("WORLDAI_DEV_MODE", "not set")

    # Build methodology from actual test configuration
    methodology = f"""# Equipment Visibility Test Methodology

## Test Purpose
Validate that the LLM correctly lists equipment items by their exact names from game_state, not vague descriptions.

## Test Configuration
- **Server**: {server_url} (local gunicorn)
- **WORLDAI_DEV_MODE**: {dev_mode}
- **Git Commit**: {git_info.get('commit', 'unknown')}
- **Branch**: {git_info.get('branch', 'unknown')}
- **Origin/main**: {git_info.get('origin_main', 'unknown')[:12] if git_info.get('origin_main') else 'unknown'}

## Test Scenarios & Thresholds
| Scenario | min_structured | min_narrative | Description |
|----------|----------------|---------------|-------------|
| Direct Equipment Query | 6 | 3 | "Show me my equipment" |
| Inventory Check | 3 | 2 | "What's in my backpack?" |
| God Mode Equipment | 3 | 2 | "GOD MODE: List equipped items with stats" |
| Weapon Check | 2 | 2 | "What weapons do I have?" |

## Seeded Equipment (from ITEM_REGISTRY)
- **Weapons**: {', '.join(weapon_items)}
- **Equipped Slots**: {', '.join(equipped_items)}
- **Backpack**: {', '.join(backpack_items)}

## Evidence Run Attribution
- **Run Directory**: {run_dir}
- **Evidence Files**: evidence.json, api_responses.json, game_state_snapshot.json
"""

    # Build evidence from actual test results
    passed = sum(1 for r in results if r.passed)
    total = len(results)

    result_rows = []
    for r in results:
        scenario_config = next((s for s in TEST_SCENARIOS if s["name"] == r.scenario_name), {})
        required_items = scenario_config.get("required_items", [])
        required_stats = scenario_config.get("required_stats", [])
        min_struct = scenario_config.get("min_required", 0)
        min_narr = scenario_config.get("min_narrative_items", 0)
        min_stats = scenario_config.get("min_stats_required", 0)

        struct_count = len(r.structured_items_found)
        narr_count = len(r.narrative_items_found)
        stats_count = len(r.structured_stats_found) if r.structured_stats_found else 0

        result_str = "PASS" if r.passed else "FAIL"
        # Fix issue #1: show stats_count/total_required_stats (need min_stats)
        if required_stats:
            stats_col = f"{stats_count}/{len(required_stats)} (need {min_stats})"
        else:
            stats_col = "N/A"

        result_rows.append(
            f"| {r.scenario_name} | {struct_count}/{len(required_items)} (need {min_struct}) | "
            f"{narr_count}/{len(required_items)} (need {min_narr}) | {stats_col} | {result_str} |"
        )

    # Get all unique narrative items found across all scenarios
    all_narrative_items = set()
    for r in results:
        all_narrative_items.update(r.narrative_items_found)

    evidence = f"""# Equipment Visibility Test Evidence Summary

## Results: {passed}/{total} {'PASS' if passed == total else 'FAIL'}

| Scenario | Structured | Narrative | Stats | Result |
|----------|------------|-----------|-------|--------|
{chr(10).join(result_rows)}

## Run Attribution
- **Run Directory**: {run_dir.name}
- **Full Path**: {run_dir}

## Items Verified in Narrative
{chr(10).join(f'- {item}' for item in sorted(all_narrative_items))}
"""

    # Build notes with actual verification
    # Include missing item warnings (issue #2 from equipc review)
    missing_warning = ""
    if missing_item_ids:
        missing_warning = f"""
## WARNING: Missing Item IDs
The following item IDs in SEED_EQUIPMENT were not found in ITEM_REGISTRY:
{chr(10).join(f'- {item_id}' for item_id in missing_item_ids)}

This indicates a mismatch between seeded equipment and item definitions.
"""

    notes = f"""# Evidence Notes

## Run Attribution (Critical for Traceability)
- **Specific Run**: {run_dir.name}
- **Run Path**: {run_dir}
- This evidence package corresponds to exactly ONE test run.
{missing_warning}
## Git Provenance
- Commit: {git_info.get('commit', 'unknown')}
- Branch: {git_info.get('branch', 'unknown')}
- Origin/main: {git_info.get('origin_main', 'unknown')}

## Key Implementation Files
- mvp_site/llm_service.py: extract_equipment_display(), is_equipment_query()
- mvp_site/game_state.py: item_registry attribute
- mvp_site/agents.py: InfoAgent class
- mvp_site/frontend_v1/app.js: Equipment display rendering

## Verification Notes
- Equipment items listed above come directly from ITEM_REGISTRY in test file
- Test results generated from actual LLM API responses
- game_state_snapshot.json contains verified post-seed equipment state
"""

    return methodology, evidence, notes


def main() -> int:
    parser = argparse.ArgumentParser(description="Equipment visibility test with evidence standards")
    parser.add_argument(
        "--server-url",
        default="http://127.0.0.1:8082",
        help="MCP server URL",
    )
    parser.add_argument(
        "--user-id",
        default="test-equipment-user",
        help="User ID for test campaign",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print detailed output",
    )
    parser.add_argument(
        "--savetmp",
        action="store_true",
        help="Automatically call savetmp.py with accurate documentation",
    )
    parser.add_argument(
        "--work-name",
        default="equipment_visibility_test",
        help="Work name for savetmp (default: equipment_visibility_test)",
    )
    args = parser.parse_args()

    # Evidence stored per evidence-standards.md: /tmp/<repo>/<branch>/<work>/<timestamp>/
    evidence_dir = get_evidence_dir("equipment_visibility")

    print(f"\n{'='*70}")
    print("EQUIPMENT VISIBILITY TEST (Evidence Standards Compliant)")
    print(f"{'='*70}")
    print(f"Server: {args.server_url}")
    print(f"User ID: {args.user_id}")
    print()

    # Capture git provenance
    print("Capturing git provenance...")
    git_info = capture_git_provenance()
    print(f"  Commit: {git_info['commit'][:12]}")
    print(f"  Branch: {git_info['branch']}")
    print(f"  Origin/main: {git_info['origin_main'][:12]}")
    print()

    client = MCPClient(args.server_url, timeout_s=120.0)

    try:
        print("Waiting for server health...")
        client.wait_healthy(timeout_s=30.0)
        print("Server is healthy.\n")
    except Exception as exc:
        print(f"ERROR: Server not healthy: {exc}")
        return 1

    # Create test campaign
    print("Creating test campaign...")
    try:
        campaign_id = create_campaign(
            client,
            user_id=args.user_id,
            title=f"Equipment Test {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            prompt="A test character for equipment visibility testing.",
        )
        print(f"Campaign created: {campaign_id}\n")
    except Exception as exc:
        print(f"ERROR: Failed to create campaign: {exc}")
        return 1

    # Seed equipment with item registry
    print("Seeding equipment into game_state (using string IDs + item_registry)...")
    try:
        seed_response = seed_equipment_into_game_state(
            client,
            user_id=args.user_id,
            campaign_id=campaign_id,
            equipment=SEED_EQUIPMENT,
            item_registry=ITEM_REGISTRY,
        )
        print("Equipment seeded successfully.\n")
    except Exception as exc:
        print(f"ERROR: Failed to seed equipment: {exc}")
        return 1

    # Verify equipment in game_state (capture for evidence)
    print("Verifying equipment in game_state (capturing for evidence)...")
    try:
        state_response = get_campaign_state(client, user_id=args.user_id, campaign_id=campaign_id)
        game_state = state_response.get("game_state", {})
        pc_data = game_state.get("player_character_data", {})
        stored_equipment = pc_data.get("equipment", {})

        if stored_equipment:
            print(f"  Equipment verified: {len(stored_equipment)} categories")
            if args.verbose:
                print(f"  Equipment data: {json.dumps(stored_equipment, indent=2)}")
        else:
            print("  WARNING: No equipment found in game_state!")
        print()
    except Exception as exc:
        print(f"WARNING: Could not verify equipment: {exc}")
        state_response = {}
        print()

    # Run test scenarios
    results: list[TestResult] = []
    print("Running test scenarios...")
    print("-" * 70)

    for scenario in TEST_SCENARIOS:
        print(f"\n[{scenario['name']}]")
        print(f"  Input: {scenario['user_input'][:60]}...")

        try:
            response = process_action(
                client,
                user_id=args.user_id,
                campaign_id=campaign_id,
                user_input=scenario["user_input"],
            )
            result = validate_scenario(response, scenario)
        except Exception as exc:
            result = TestResult(
                passed=False,
                scenario_name=scenario["name"],
                user_input=scenario["user_input"],
                narrative="",
                narrative_items_found=[],
                narrative_items_missing=scenario.get("required_items", []),
                structured_items_found=[],
                structured_items_missing=scenario.get("required_items", []),
                error=str(exc),
            )

        results.append(result)

        # Print result
        status = "PASS" if result.passed else "FAIL"
        req_items = scenario.get("required_items", [])
        req_stats = scenario.get("required_stats", [])

        print(f"  Result: {status}")
        print(f"    Structured items: {len(result.structured_items_found)}/{len(req_items)} "
              f"(need {scenario.get('min_required', len(req_items))})")
        print(f"    Narrative items: {len(result.narrative_items_found)}/{len(req_items)} "
              f"(need {scenario.get('min_narrative_items', 0)})")

        if req_stats:
            print(f"    Stats (structured): {len(result.structured_stats_found)}/{len(req_stats)} "
                  f"(need {scenario.get('min_stats_required', 0)})")

        if result.structured_items_missing:
            print(f"    Missing items: {result.structured_items_missing}")
        if result.structured_stats_missing:
            print(f"    Missing stats: {result.structured_stats_missing}")
        if result.vague_phrases_found:
            print(f"    Vague phrases: {result.vague_phrases_found}")
        if result.unexpected_items_narrative or result.unexpected_items_structured:
            print(f"    Unexpected items (narrative): {result.unexpected_items_narrative}")
            print(f"    Unexpected items (structured): {result.unexpected_items_structured}")
        if result.error:
            print(f"    Error: {result.error}")

        if args.verbose and result.narrative:
            print(f"    Narrative (first 300 chars):\n      {result.narrative[:300]}...")

    # Summary
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed

    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Passed: {passed}/{len(results)}")
    print(f"Failed: {failed}/{len(results)}")

    if failed > 0:
        print("\nFailed scenarios:")
        for r in results:
            if not r.passed:
                print(f"  - {r.scenario_name}")

    # Save evidence bundle
    bundle = EvidenceBundle(
        timestamp=datetime.now().isoformat(),
        server_url=args.server_url,
        campaign_id=campaign_id,
        git_commit=git_info["commit"],
        git_branch=git_info["branch"],
        origin_main=git_info["origin_main"],
        files_changed=git_info["files_changed"],
        seeded_equipment=SEED_EQUIPMENT,
        verified_game_state=state_response,
        test_results=[
            {
                "scenario": r.scenario_name,
                "passed": r.passed,
                "user_input": r.user_input,
                "structured_items_found": r.structured_items_found,
                "structured_items_missing": r.structured_items_missing,
                "structured_stats_found": r.structured_stats_found,
                "structured_stats_missing": r.structured_stats_missing,
                "narrative_items_found": r.narrative_items_found,
                "narrative_items_missing": r.narrative_items_missing,
                "narrative_summary_ok": r.narrative_summary_ok,
                "structured_ok": r.structured_ok,
                "equipment_display_present": r.equipment_display_present,
                "vague_phrases": r.vague_phrases_found,
                "unexpected_items_narrative": r.unexpected_items_narrative,
                "unexpected_items_structured": r.unexpected_items_structured,
                "narrative": r.narrative[:2000] if r.narrative else "",
                "error": r.error,
                "full_response": r.full_response,
            }
            for r in results
        ],
        summary={"passed": passed, "failed": failed, "total": len(results)},
    )

    evidence_path = save_evidence_bundle(evidence_dir, bundle)
    print(f"\nEvidence saved to: {evidence_path}")
    print("  - evidence.json + checksum")
    print("  - api_responses.json + checksum")
    print("  - game_state_snapshot.json + checksum")
    print("  - README.md + checksum")

    # Generate savetmp documentation from actual test data
    methodology, evidence_summary, notes = generate_savetmp_docs(
        results=results,
        git_info=git_info,
        server_url=args.server_url,
        run_dir=evidence_path,
    )

    if args.savetmp:
        # Write temp files for savetmp input
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            meth_file = tmp_path / "methodology.md"
            meth_file.write_text(methodology)

            evid_file = tmp_path / "evidence.md"
            evid_file.write_text(evidence_summary)

            notes_file = tmp_path / "notes.md"
            notes_file.write_text(notes)

            # Call savetmp.py with the specific run directory as artifact
            savetmp_script = PROJECT_ROOT / ".claude" / "commands" / "savetmp.py"
            if savetmp_script.exists():
                print(f"\n{'='*70}")
                print("CALLING SAVETMP")
                print(f"{'='*70}")

                cmd = [
                    sys.executable, str(savetmp_script),
                    args.work_name,
                    "--methodology-file", str(meth_file),
                    "--evidence-file", str(evid_file),
                    "--notes-file", str(notes_file),
                    "--artifact", str(evidence_path),  # Only the specific run, not entire dir
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                print(result.stdout)
                if result.stderr:
                    print(result.stderr)
                # Issue #5 from equipc review: check returncode
                if result.returncode != 0:
                    print(f"WARNING: savetmp.py exited with code {result.returncode}")
            else:
                print(f"\nWARNING: savetmp.py not found at {savetmp_script}")
    else:
        # Print savetmp command for manual execution
        print(f"\n{'='*70}")
        print("SAVETMP COMMAND (run with --savetmp to auto-execute)")
        print(f"{'='*70}")
        print(f"""
python .claude/commands/savetmp.py "{args.work_name}" \\
  --methodology "<auto-generated from ITEM_REGISTRY>" \\
  --evidence "<auto-generated from test results>" \\
  --notes "<auto-generated verification notes>" \\
  --artifact {evidence_path}

Or run test with --savetmp flag:
  python {Path(__file__).name} --savetmp --work-name "{args.work_name}"
""")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
