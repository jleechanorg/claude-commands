#!/usr/bin/env python3
"""MCP Schema Validation Tests - validates LLM generates proper schema structures.

This test validates that the LLM correctly generates all schema structures we've added:
- Priority 1: Resources (gold, hit_dice, spell_slots, class_features, consumables)
- Priority 2: Attributes, Experience, Death Saves, Spells Known
- Priority 3: Status Conditions, Active Effects, Combat Stats, Items

The test processes actions that trigger updates to these schemas and validates:
1. LLM generates proper JSON structures in state_updates (response validation)
2. Python validation catches any schema violations
3. All required fields are present and correctly typed
4. State updates are correctly persisted to Firestore (Firestore validation)
5. Persisted Firestore state matches the response state_updates

Run (local MCP already running):
    cd testing_mcp
    python test_schema_validation_real_api.py --server-url http://127.0.0.1:8001

Run (start local MCP automatically - PR #3470):
    cd testing_mcp
    python test_schema_validation_real_api.py --start-local --real-services

PR #3470 Configuration:
    - Evidence collection: ALWAYS enabled (saved to /tmp subdirectory)
    - Model: ALWAYS gemini-3-flash-preview
    - Firestore validation: ALWAYS enabled (validates persistence)
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
import traceback
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
from lib.evidence_utils import (
    capture_provenance,
    create_evidence_bundle,
    get_evidence_dir,
    save_request_responses,
    write_with_checksum,
)
from lib import MCPClient
from lib.campaign_utils import create_campaign, process_action, get_campaign_state

# Import validation functions to test them
sys.path.insert(0, str(Path(__file__).parent.parent))
from mvp_site.narrative_response_schema import (
    _validate_resources,
    _validate_spell_slots,
    _validate_class_features,
    _validate_attributes,
    _validate_experience,
    _validate_death_saves,
    _validate_spells_known,
    _validate_status_conditions,
    _validate_active_effects,
    _validate_combat_stats,
    _validate_item,
)

# =============================================================================
# CHARACTER SETUP - Comprehensive character with all schema fields
# =============================================================================

CHARACTER_COMPREHENSIVE = """
Aric the Fighter (Level 5, Champion)
Race: Human
Attributes: STR 16, DEX 14, CON 15, INT 12, WIS 13, CHA 10

BASE ATTRIBUTES:
- STR: 16, DEX: 14, CON: 15, INT: 12, WIS: 13, CHA: 10

ATTRIBUTES (with equipment bonuses):
- STR: 18 (+2 from Belt of Giant Strength), DEX: 14, CON: 15, INT: 12, WIS: 13, CHA: 10

EXPERIENCE:
- Current: 6500
- Needed for next level: 14000

RESOURCES:
- Gold: 250
- Hit Dice: 3/5 used (2 remaining)
- Spell Slots: None (Fighter, no spells)
- Class Features: Action Surge (1/1), Second Wind (1/1)

COMBAT STATS:
- Initiative: +2
- Speed: 30 feet
- Passive Perception: 11

STATUS CONDITIONS: []
ACTIVE EFFECTS: []
DEATH SAVES: {"successes": 0, "failures": 0}

EQUIPMENT:
- Main Hand: Longsword +1 (type: weapon, damage: 1d8, damage_type: slashing, bonus: 1)
- Armor: Chain Mail (type: armor, armor_class: 16, armor_type: heavy)
- Belt: Belt of Giant Strength (STR +2)

SPELLS KNOWN: [] (Fighter, no spells)
"""

CHARACTER_SPELLCASTER = """
Lyra the Bard (Level 5, College of Lore)
Race: Half-Elf
Attributes: STR 10, DEX 14, CON 12, INT 10, WIS 12, CHA 18 (+4)

BASE ATTRIBUTES:
- STR: 10, DEX: 14, CON: 12, INT: 10, WIS: 12, CHA: 18

ATTRIBUTES (same as base):
- STR: 10, DEX: 14, CON: 12, INT: 10, WIS: 12, CHA: 18

EXPERIENCE:
- Current: 6500
- Needed for next level: 14000

RESOURCES:
- Gold: 150
- Hit Dice: 2/5 used (3 remaining)
- Spell Slots:
  - Level 1: 2/4 (2 remaining)
  - Level 2: 1/3 (1 remaining)
  - Level 3: 2/2 (2 remaining)
- Class Features:
  - Bardic Inspiration: 2/4 (2 remaining)

COMBAT STATS:
- Initiative: +2
- Speed: 30 feet
- Passive Perception: 13

STATUS CONDITIONS: ["Poisoned"]
ACTIVE EFFECTS: ["Bless: +1d4 to attack rolls and saving throws"]
DEATH SAVES: {"successes": 1, "failures": 0}

EQUIPMENT:
- Main Hand: Rapier (type: weapon, damage: 1d8, damage_type: piercing)
- Armor: Leather Armor (type: armor, armor_class: 13, armor_type: light)

SPELLS KNOWN:
- {"name": "Charm Person", "level": 1, "school": "enchantment"}
- {"name": "Healing Word", "level": 1, "school": "evocation"}
- {"name": "Hold Person", "level": 2, "school": "enchantment"}
- {"name": "Hypnotic Pattern", "level": 3, "school": "illusion"}
"""

# =============================================================================
# TEST SCENARIOS - Actions that trigger schema updates
# =============================================================================

SCENARIOS = [
    {
        "name": "Update resources (gold, hit_dice)",
        "character": "COMPREHENSIVE",
        "user_input": "I take a short rest and spend 1 hit die to recover HP. I also find 50 gold coins.",
        "expected_updates": {
            "resources": ["gold", "hit_dice"],
        },
    },
    {
        "name": "Update spell slots",
        "character": "SPELLCASTER",
        "user_input": "I cast Healing Word at 1st level to heal myself.",
        "expected_updates": {
            "resources": ["spell_slots"],
        },
    },
    {
        "name": "Update class features (bardic inspiration)",
        "character": "SPELLCASTER",
        "user_input": "I use Bardic Inspiration to inspire my ally.",
        "expected_updates": {
            "resources": ["class_features"],
        },
    },
    {
        "name": "Update experience",
        "character": "COMPREHENSIVE",
        "user_input": "I defeat the goblin and gain experience.",
        "expected_updates": {
            "experience": ["current"],
        },
    },
    {
        "name": "Update death saves",
        "character": "COMPREHENSIVE",
        "user_input": "I make a death saving throw.",
        "expected_updates": {
            "death_saves": ["successes", "failures"],
        },
    },
    {
        "name": "Update status conditions",
        "character": "SPELLCASTER",
        "user_input": "I get hit by a poison attack and become poisoned.",
        "expected_updates": {
            "status_conditions": [],
        },
    },
    {
        "name": "Update active effects",
        "character": "SPELLCASTER",
        "user_input": "I cast Haste on myself.",
        "expected_updates": {
            "active_effects": [],
        },
    },
    {
        "name": "Update combat stats",
        "character": "COMPREHENSIVE",
        "user_input": "I roll initiative for combat.",
        "expected_updates": {
            "combat_stats": ["initiative"],
        },
    },
    {
        "name": "Update attributes",
        "character": "COMPREHENSIVE",
        "user_input": "I equip a Belt of Giant Strength that increases my STR to 20.",
        "expected_updates": {
            "attributes": ["STR"],
        },
    },
]


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_schema_structure(
    state_updates: dict[str, Any], expected_updates: dict[str, list[str]]
) -> list[str]:
    """Validate that state_updates contains proper schema structures."""
    errors = []

    player_data = state_updates.get("player_character_data", {})
    if not isinstance(player_data, dict):
        return ["player_character_data must be a dict"]

    # Validate resources
    if "resources" in expected_updates:
        resources = player_data.get("resources")
        if resources is None:
            errors.append("resources is missing but expected in expected_updates")
        elif not isinstance(resources, dict):
            errors.append("resources must be a dict")
        else:
            resource_errors = _validate_resources(resources)
            errors.extend([f"resources.{e}" for e in resource_errors])

            # Validate spell_slots if present (with type guard)
            if "spell_slots" in resources:
                spell_slots = resources["spell_slots"]
                if not isinstance(spell_slots, dict):
                    errors.append("resources.spell_slots must be a dict")
                else:
                    spell_slot_errors = _validate_spell_slots(spell_slots)
                    errors.extend([f"resources.spell_slots.{e}" for e in spell_slot_errors])

            # Validate class_features if present (with type guard)
            if "class_features" in resources:
                class_features = resources["class_features"]
                if not isinstance(class_features, dict):
                    errors.append("resources.class_features must be a dict")
                else:
                    class_feature_errors = _validate_class_features(class_features)
                    errors.extend([f"resources.class_features.{e}" for e in class_feature_errors])

    # Validate attributes
    if "attributes" in expected_updates:
        # Attributes are validated from player_data directly, not a nested object
        attribute_errors = _validate_attributes(player_data)
        errors.extend([f"attributes.{e}" for e in attribute_errors])

    # Validate experience
    if "experience" in expected_updates:
        experience = player_data.get("experience")
        if experience is None:
            errors.append("experience is missing but expected in expected_updates")
        elif not isinstance(experience, dict):
            errors.append("experience must be a dict")
        else:
            experience_errors = _validate_experience(experience)
            errors.extend([f"experience.{e}" for e in experience_errors])

    # Validate death_saves
    if "death_saves" in expected_updates:
        death_saves = player_data.get("death_saves")
        if death_saves is None:
            errors.append("death_saves is missing but expected in expected_updates")
        elif not isinstance(death_saves, dict):
            errors.append("death_saves must be a dict")
        else:
            death_saves_errors = _validate_death_saves(death_saves)
            errors.extend([f"death_saves.{e}" for e in death_saves_errors])

    # Validate spells_known
    spells_known = player_data.get("spells_known")
    if spells_known is not None:
        if not isinstance(spells_known, list):
            errors.append("spells_known must be an array")
        else:
            spells_known_errors = _validate_spells_known(spells_known)
            errors.extend([f"spells_known.{e}" for e in spells_known_errors])

    # Validate status_conditions
    status_conditions = player_data.get("status_conditions")
    if status_conditions is not None:
        status_conditions_errors = _validate_status_conditions(status_conditions)
        errors.extend([f"status_conditions.{e}" for e in status_conditions_errors])

    # Validate active_effects
    active_effects = player_data.get("active_effects")
    if active_effects is not None:
        active_effects_errors = _validate_active_effects(active_effects)
        errors.extend([f"active_effects.{e}" for e in active_effects_errors])

    # Validate combat_stats
    combat_stats = player_data.get("combat_stats")
    if combat_stats is not None:
        if not isinstance(combat_stats, dict):
            errors.append("combat_stats must be a dict")
        else:
            combat_stats_errors = _validate_combat_stats(combat_stats)
            errors.extend([f"combat_stats.{e}" for e in combat_stats_errors])

    # Validate equipment items
    equipment = player_data.get("equipment")
    if equipment is not None and isinstance(equipment, dict):
        for slot_name, item in equipment.items():
            if item is not None and isinstance(item, dict):
                item_errors = _validate_item(item, f"equipment.{slot_name}")
                errors.extend([f"equipment.{slot_name}.{e}" for e in item_errors])
            elif isinstance(item, list):
                for idx, sub_item in enumerate(item):
                    if isinstance(sub_item, dict):
                        item_errors = _validate_item(sub_item, f"equipment.{slot_name}[{idx}]")
                        errors.extend([f"equipment.{slot_name}[{idx}].{e}" for e in item_errors])

    return errors


def validate_firestore_persistence(
    client: MCPClient,
    user_id: str,
    campaign_id: str,
    state_updates: dict[str, Any],
    expected_updates: dict[str, list[str]],
) -> list[str]:
    """Validate that state_updates were correctly persisted to Firestore."""
    errors = []
    
    try:
        # Fetch campaign state from Firestore
        firestore_state = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
        
        # Extract player character data from Firestore (nested under game_state)
        firestore_game_state = firestore_state.get("game_state", {})
        firestore_player_data = firestore_game_state.get("player_character_data", {})
        if not isinstance(firestore_player_data, dict):
            errors.append("Firestore game_state.player_character_data is not a dict")
            return errors
        
        # Validate that expected updates are present in Firestore
        response_player_data = state_updates.get("player_character_data", {})
        
        # Check resources
        if "resources" in expected_updates:
            firestore_resources = firestore_player_data.get("resources", {})
            response_resources = response_player_data.get("resources", {})
            
            # Validate resources schema in Firestore
            if firestore_resources:
                resource_errors = _validate_resources(firestore_resources)
                errors.extend([f"firestore.resources.{e}" for e in resource_errors])
            
            # Compare key fields between response and Firestore
            for field in expected_updates.get("resources", []):
                if field == "gold":
                    firestore_gold = firestore_resources.get("gold")
                    response_gold = response_resources.get("gold")
                    if firestore_gold != response_gold:
                        errors.append(
                            f"Firestore gold mismatch: response={response_gold}, firestore={firestore_gold}"
                        )
                elif field == "hit_dice":
                    firestore_hd = firestore_resources.get("hit_dice", {})
                    response_hd = response_resources.get("hit_dice", {})
                    if firestore_hd.get("used") != response_hd.get("used"):
                        errors.append(
                            f"Firestore hit_dice.used mismatch: response={response_hd.get('used')}, "
                            f"firestore={firestore_hd.get('used')}"
                        )
                elif field == "spell_slots":
                    firestore_slots = firestore_resources.get("spell_slots", {})
                    response_slots = response_resources.get("spell_slots", {})
                    if firestore_slots and response_slots:
                        slot_errors = _validate_spell_slots(firestore_slots)
                        errors.extend([f"firestore.resources.spell_slots.{e}" for e in slot_errors])
                elif field == "class_features":
                    firestore_features = firestore_resources.get("class_features", {})
                    response_features = response_resources.get("class_features", {})
                    if firestore_features and response_features:
                        feature_errors = _validate_class_features(firestore_features)
                        errors.extend([f"firestore.resources.class_features.{e}" for e in feature_errors])
        
        # Check attributes
        if "attributes" in expected_updates:
            firestore_attrs = firestore_player_data.get("base_attributes", {})
            if firestore_attrs:
                attr_errors = _validate_attributes(firestore_player_data)
                errors.extend([f"firestore.attributes.{e}" for e in attr_errors])
        
        # Check experience
        if "experience" in expected_updates:
            firestore_exp = firestore_player_data.get("experience", {})
            if firestore_exp:
                exp_errors = _validate_experience(firestore_exp)
                errors.extend([f"firestore.experience.{e}" for e in exp_errors])
        
        # Check death_saves
        if "death_saves" in expected_updates:
            firestore_ds = firestore_player_data.get("death_saves", {})
            if firestore_ds:
                ds_errors = _validate_death_saves(firestore_ds)
                errors.extend([f"firestore.death_saves.{e}" for e in ds_errors])
        
        # Check status_conditions
        firestore_sc = firestore_player_data.get("status_conditions")
        if firestore_sc is not None:
            sc_errors = _validate_status_conditions(firestore_sc)
            errors.extend([f"firestore.status_conditions.{e}" for e in sc_errors])
        
        # Check active_effects
        firestore_ae = firestore_player_data.get("active_effects")
        if firestore_ae is not None:
            ae_errors = _validate_active_effects(firestore_ae)
            errors.extend([f"firestore.active_effects.{e}" for e in ae_errors])
        
        # Check combat_stats
        firestore_cs = firestore_player_data.get("combat_stats", {})
        if firestore_cs:
            cs_errors = _validate_combat_stats(firestore_cs)
            errors.extend([f"firestore.combat_stats.{e}" for e in cs_errors])
        
    except Exception as e:
        errors.append(f"Firestore validation failed with exception: {e}")
        errors.append(f"Traceback: {traceback.format_exc()}")
    
    return errors


def run_schema_validation_test(
    client: MCPClient,
    model_id: str,
    scenario: dict,
    character_sheet: str,
    evidence_dir: Path | None,
    created_campaigns: list[tuple[str, str]] | None = None,
) -> tuple[bool, list[str], dict[str, Any], Path | None]:
    """Run a single schema validation test scenario."""
    user_id = f"schema-val-{int(time.time())}-{model_id.replace('/', '-')}"
    model_settings = settings_for_model(model_id)
    model_settings["debug_mode"] = True
    update_user_settings(client, user_id=user_id, settings=model_settings)

    # Create campaign
    campaign_id = create_campaign(
        client,
        user_id,
        title=f"Schema Validation Test - {scenario['name']}",
        character=character_sheet,
        setting="You stand in a dark dungeon corridor. Danger lurks ahead.",
        description=f"Test campaign for schema validation: {scenario['name']}",
    )
    
    # Track campaign for cleanup
    if created_campaigns is not None:
        created_campaigns.append((user_id, campaign_id))

    print(f"\n   Testing: {scenario['name']}")
    print(f'   Input: "{scenario["user_input"]}"')
    print(f"   Campaign: {campaign_id}")

    # Process action
    result = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=scenario["user_input"],
        mode="character",
    )

    # Validate schema structures in response
    state_updates = result.get("state_updates", {})
    validation_errors = validate_schema_structure(
        state_updates, scenario.get("expected_updates", {})
    )

    # Validate Firestore persistence
    firestore_errors = validate_firestore_persistence(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        state_updates=state_updates,
        expected_updates=scenario.get("expected_updates", {}),
    )
    
    # Combine all errors
    all_errors = validation_errors + firestore_errors
    passed = len(all_errors) == 0

    # Save evidence (ALWAYS enabled for PR #3470)
    evidence_file: Path | None = None
    if evidence_dir:
        # Fetch Firestore state for evidence
        firestore_state = {}
        try:
            firestore_state = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
        except Exception as e:
            firestore_state = {"error": str(e)}
        
        evidence = {
            "timestamp": datetime.now(UTC).isoformat(),
            "model_id": model_id,
            "scenario_name": scenario["name"],
            "user_input": scenario["user_input"],
            "validation_passed": passed,
            "validation_errors": validation_errors,
            "firestore_validation_errors": firestore_errors,
            "narrative": result.get("narrative", ""),
            "state_updates": state_updates,
            "firestore_state": firestore_state,
            "game_state": result.get("game_state", {}),
        }
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        safe_model = model_id.replace("/", "-").replace(":", "-")
        safe_scenario = scenario["name"].lower().replace(" ", "_")[:60]
        filename = f"{timestamp}_{safe_model}_{safe_scenario}.json"
        evidence_path = evidence_dir / filename
        # Use default=str to handle non-serializable values (e.g., datetime objects, sets)
        # This ensures we collect maximum evidence even on partial failures
        evidence_json = json.dumps(evidence, indent=2, default=str)
        write_with_checksum(evidence_path, evidence_json)
        evidence_file = evidence_path
        print(f"  📁 Evidence saved: {filename}")
        
        if firestore_errors:
            print(f"  ⚠️  Firestore validation errors: {len(firestore_errors)}")
            for error in firestore_errors[:3]:
                print(f"     - {error}")

    return passed, all_errors, result, evidence_file


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Schema validation tests")
    parser.add_argument(
        "--server-url",
        type=str,
        help="MCP server URL (default: http://127.0.0.1:8001)",
        default="http://127.0.0.1:8001",
    )
    parser.add_argument(
        "--start-local",
        action="store_true",
        help="Start local MCP server automatically",
    )
    parser.add_argument(
        "--real-services",
        action="store_true",
        help="Use real LLM services (not mocked)",
    )
    parser.add_argument(
        "--no-evidence",
        dest="evidence",
        action="store_false",
        default=True,
        help="Disable evidence bundle creation (enabled by default)",
    )
    parser.add_argument(
        "--models",
        type=str,
        nargs="+",
        help="Model IDs to test (default: gemini-3-flash-preview). PR #3470: Always uses gemini-3-flash-preview",
        default=["gemini-3-flash-preview"],
    )

    args = parser.parse_args()
    
    # PR #3470: Force gemini-3-flash-preview and evidence collection
    # Evidence always saved to /tmp subdirectory, Firestore validation always enabled
    args.models = ["gemini-3-flash-preview"]
    args.evidence = True

    # Start local server if requested
    local_server: LocalServer | None = None
    if args.start_local:
        port = pick_free_port()
        env_overrides: dict[str, str] = {
            "MOCK_SERVICES_MODE": "false" if args.real_services else "true",
            "TESTING": "false",
            "FORCE_TEST_MODEL": "false",
            "FAST_TESTS": "false",
            "CAPTURE_EVIDENCE": "true",
        }
        local_server = start_local_mcp_server(port, env_overrides=env_overrides)
        args.server_url = local_server.base_url
        print(f"🚀 Local MCP server started on {args.server_url}")
        print(f"📋 Log file: {local_server.log_path}")

    try:
        # Create MCP client
        client = MCPClient(base_url=args.server_url, timeout_s=600.0)
        client.wait_healthy(timeout_s=45.0)
        print(f"✅ MCP server healthy at {args.server_url}\n")

        # Setup evidence directory (ALWAYS enabled for PR #3470)
        # Evidence always saved to /tmp subdirectory for schema validation tests
        evidence_dir = get_evidence_dir("schema_validation_real_api")
        evidence_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Evidence directory: {evidence_dir}")
        print(f"   PR #3470: Evidence collection ALWAYS enabled, Firestore validation ALWAYS enabled")

        # Capture provenance
        capture_provenance(args.server_url)

        # Character map
        CHARACTER_MAP = {
            "COMPREHENSIVE": CHARACTER_COMPREHENSIVE,
            "SPELLCASTER": CHARACTER_SPELLCASTER,
        }

        # Run tests for each model
        total_passed = 0
        total_tests = 0
        all_results = []
        individual_evidence_files: list[Path] = []  # Track individual test result files
        created_campaigns: list[tuple[str, str]] = []  # Track campaigns for cleanup

        for model_id in args.models:
            print(f"\n{'='*80}")
            print(f"Testing model: {model_id}")
            print(f"{'='*80}")

            # Run all scenarios
            test_scenarios = SCENARIOS
            print(f"Running {len(test_scenarios)} scenarios...")

            for scenario in test_scenarios:
                character_name = scenario.get("character", "COMPREHENSIVE")
                character_sheet = CHARACTER_MAP.get(character_name, CHARACTER_COMPREHENSIVE)

                total_tests += 1
                try:
                    passed, errors, result, evidence_file = run_schema_validation_test(
                        client, model_id, scenario, character_sheet, evidence_dir, created_campaigns
                    )
                    if evidence_file:
                        individual_evidence_files.append(evidence_file)

                    if passed:
                        print(f"  ✅ PASSED (response + Firestore validation)")
                        total_passed += 1
                    else:
                        response_errors = [e for e in errors if not e.startswith("firestore.")]
                        firestore_errors = [e for e in errors if e.startswith("firestore.")]
                        print(f"  ❌ FAILED: {len(errors)} validation errors")
                        if response_errors:
                            print(f"     Response validation errors: {len(response_errors)}")
                            for error in response_errors[:3]:
                                print(f"       - {error}")
                        if firestore_errors:
                            print(f"     Firestore validation errors: {len(firestore_errors)}")
                            for error in firestore_errors[:3]:
                                print(f"       - {error}")
                        if len(errors) > 6:
                            print(f"     ... and {len(errors) - 6} more errors")

                    all_results.append(
                        {
                            "model": model_id,
                            "scenario": scenario["name"],
                            "passed": passed,
                            "errors": errors,
                        }
                    )
                except Exception as e:
                    print(f"  ❌ ERROR: {e}")
                    traceback.print_exc()
                    all_results.append(
                        {
                            "model": model_id,
                            "scenario": scenario["name"],
                            "passed": False,
                            "errors": [str(e)],
                        }
                    )
                    # No evidence file on error

        # Summary
        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}")
        print(f"Total tests: {total_tests}")
        print(f"Passed: {total_passed}")
        print(f"Failed: {total_tests - total_passed}")
        if total_tests > 0:
            print(f"Success rate: {total_passed / total_tests * 100:.1f}%")
        else:
            print("Success rate: N/A (no tests run)")

        # Create evidence bundle (ALWAYS enabled for PR #3470)
        if evidence_dir:
            provenance = capture_provenance(args.server_url)
            bundle_files = create_evidence_bundle(
                evidence_dir,
                test_name="schema_validation_real_api",
                provenance=provenance,
                results={
                    "total_tests": total_tests,
                    "passed": total_passed,
                    "failed": total_tests - total_passed,
                    "success_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0.0,
                    "scenarios": all_results,
                },
                server_log_path=Path(local_server.log_path) if local_server else None,
            )
            
            # Copy individual test result files into artifacts directory
            if individual_evidence_files and bundle_files.get("_bundle_dir"):
                artifacts_dir = bundle_files["_bundle_dir"] / "artifacts"
                artifacts_dir.mkdir(exist_ok=True)
                copied_count = 0
                for evidence_file in individual_evidence_files:
                    if evidence_file.exists():
                        dest_file = artifacts_dir / evidence_file.name
                        shutil.copy2(evidence_file, dest_file)
                        # Write checksum for copied file
                        write_with_checksum(dest_file, dest_file.read_text())
                        copied_count += 1
                print(f"\n📦 Evidence bundle created at: {bundle_files['_bundle_dir']}")
                print(f"   Copied {copied_count} individual test result files to artifacts/")
            else:
                print(f"\n📦 Evidence bundle created at: {evidence_dir}")

        # Exit with error code if any tests failed
        if total_passed < total_tests:
            sys.exit(1)

    finally:
        # Cleanup campaigns to prevent data leaks in real-services mode
        if client is not None and created_campaigns:
            print(f"\n🧹 Cleaning up {len(created_campaigns)} test campaigns...")
            for user_id, campaign_id in created_campaigns:
                try:
                    client.tools_call(
                        "delete_campaign",
                        {"user_id": user_id, "campaign_id": campaign_id},
                    )
                except Exception as exc:
                    print(f"⚠️ Cleanup failed for campaign {campaign_id}: {exc}")
        
        if local_server:
            print("\n🛑 Stopping local server...")
            local_server.stop()


if __name__ == "__main__":
    main()
