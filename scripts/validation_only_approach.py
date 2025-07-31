#!/usr/bin/env python3
"""
Milestone 0.4 - Approach 1: Validation-Only Implementation
This approach uses post-generation validation to detect entity desyncs.
"""

import json
import os
import sys
import time
from datetime import datetime

# Add prototype to path for validators
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prototype"
    ),
)
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mvp_site"
    ),
)


# Simple entity validator without external dependencies
class SimpleEntityValidator:
    """Basic entity validation using string matching."""

    def validate_entity(self, text: str, entity: str) -> bool:
        """Check if entity is mentioned in text."""
        # Simple case-insensitive substring matching
        # In production, use FuzzyTokenValidator
        text_lower = text.lower()
        entity_lower = entity.lower()

        # Check for exact match or partial match
        if entity_lower in text_lower:
            return True

        # Check for first/last name match for character names
        name_parts = entity.split()
        if len(name_parts) > 1:
            for part in name_parts:
                if part.lower() in text_lower:
                    return True

        return False


class ValidationOnlyApproach:
    """
    Implements validation-only approach for entity tracking.
    This validates after generation without modifying the prompts.
    """

    def __init__(self):
        self.validator = SimpleEntityValidator()
        self.results = []

    def extract_entities_from_state(self, game_state: dict) -> dict[str, set[str]]:
        """Extract all entities that should be mentioned from game state."""
        entities = {
            "player_characters": set(),
            "npcs": set(),
            "locations": set(),
            "items": set(),
            "active_entities": set(),  # Entities that MUST be mentioned
        }

        # Extract player character(s)
        pc_data = game_state.get("player_character_data", {})
        if isinstance(pc_data, dict):
            if "name" in pc_data:
                entities["player_characters"].add(pc_data["name"])
                entities["active_entities"].add(pc_data["name"])
            # Handle multiple PCs
            for _key, value in pc_data.items():
                if isinstance(value, dict) and "name" in value:
                    entities["player_characters"].add(value["name"])
                    entities["active_entities"].add(value["name"])

        # Extract NPCs
        npc_data = game_state.get("npc_data", {})
        if isinstance(npc_data, dict):
            for npc_name, npc_info in npc_data.items():
                # Add NPC name (key)
                entities["npcs"].add(npc_name)
                # Check if NPC is in current location or recently active
                if isinstance(npc_info, dict):
                    # Simple heuristic: if NPC has recent interaction or is marked present
                    if npc_info.get("present", False) or npc_info.get(
                        "recently_active", False
                    ):
                        entities["active_entities"].add(npc_name)

        # Extract current location
        world_data = game_state.get("world_data", {})
        if isinstance(world_data, dict):
            current_loc = world_data.get("current_location", "")
            if current_loc:
                entities["locations"].add(current_loc)
                entities["active_entities"].add(current_loc)

        # Extract combat participants
        combat_state = game_state.get("combat_state", {})
        if combat_state.get("in_combat", False):
            participants = combat_state.get("participants", [])
            for p in participants:
                if isinstance(p, dict) and "name" in p:
                    entities["active_entities"].add(p["name"])
                elif isinstance(p, str):
                    entities["active_entities"].add(p)

        return entities

    def validate_narrative(self, narrative: str, entities: dict[str, set[str]]) -> dict:
        """Validate that all required entities are mentioned in the narrative."""
        validation_result = {
            "timestamp": datetime.now().isoformat(),
            "narrative_length": len(narrative),
            "validation_time_ms": 0,
            "entities_expected": len(entities["active_entities"]),
            "entities_found": 0,
            "entities_missing": [],
            "desync_detected": False,
            "details": {},
        }

        start_time = time.time()

        # Check each active entity
        missing_entities = []
        found_entities = []

        for entity in entities["active_entities"]:
            # Use fuzzy validator to check if entity is mentioned
            is_present = self.validator.validate_entity(narrative, entity)

            if is_present:
                found_entities.append(entity)
            else:
                missing_entities.append(entity)

        validation_time = (time.time() - start_time) * 1000  # Convert to ms

        # Update results
        validation_result["validation_time_ms"] = validation_time
        validation_result["entities_found"] = len(found_entities)
        validation_result["entities_missing"] = missing_entities
        validation_result["desync_detected"] = len(missing_entities) > 0
        validation_result["desync_rate"] = (
            len(missing_entities) / len(entities["active_entities"])
            if entities["active_entities"]
            else 0
        )

        # Add detailed breakdown
        validation_result["details"] = {
            "found_entities": found_entities,
            "all_player_characters": list(entities["player_characters"]),
            "all_npcs": list(entities["npcs"]),
            "current_location": list(entities["locations"]),
        }

        return validation_result

    def test_campaign_scenario(
        self, campaign_id: str, scenario_name: str, game_state: dict, narrative: str
    ) -> dict:
        """Test a single scenario from a campaign."""
        print(f"\nTesting {campaign_id} - {scenario_name}")

        # Extract entities
        entities = self.extract_entities_from_state(game_state)

        # Validate narrative
        result = self.validate_narrative(narrative, entities)

        # Add metadata
        result["campaign_id"] = campaign_id
        result["scenario_name"] = scenario_name
        result["approach"] = "validation_only"

        # Store result
        self.results.append(result)

        # Print summary
        if result["desync_detected"]:
            print(
                f"  ❌ Desync detected! Missing {len(result['entities_missing'])} entities:"
            )
            for entity in result["entities_missing"]:
                print(f"     - {entity}")
        else:
            print(f"  ✅ All {result['entities_found']} entities mentioned correctly")

        print(f"  ⏱️  Validation time: {result['validation_time_ms']:.2f}ms")

        return result

    def generate_report(self, output_path: str = None):
        """Generate a summary report of all test results."""
        if not self.results:
            print("No results to report")
            return None

        # Calculate aggregate statistics
        total_tests = len(self.results)
        total_desyncs = sum(1 for r in self.results if r["desync_detected"])
        total_entities = sum(r["entities_expected"] for r in self.results)
        total_missing = sum(len(r["entities_missing"]) for r in self.results)
        avg_validation_time = (
            sum(r["validation_time_ms"] for r in self.results) / total_tests
        )

        report = {
            "approach": "validation_only",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "tests_with_desync": total_desyncs,
                "overall_desync_rate": total_desyncs / total_tests,
                "total_entities_expected": total_entities,
                "total_entities_missing": total_missing,
                "entity_detection_rate": (total_entities - total_missing)
                / total_entities
                if total_entities > 0
                else 0,
                "avg_validation_time_ms": avg_validation_time,
            },
            "by_campaign": {},
            "detailed_results": self.results,
        }

        # Group by campaign
        for result in self.results:
            campaign_id = result["campaign_id"]
            if campaign_id not in report["by_campaign"]:
                report["by_campaign"][campaign_id] = {
                    "total_scenarios": 0,
                    "scenarios_with_desync": 0,
                    "total_entities": 0,
                    "total_missing": 0,
                    "scenarios": [],
                }

            campaign_stats = report["by_campaign"][campaign_id]
            campaign_stats["total_scenarios"] += 1
            if result["desync_detected"]:
                campaign_stats["scenarios_with_desync"] += 1
            campaign_stats["total_entities"] += result["entities_expected"]
            campaign_stats["total_missing"] += len(result["entities_missing"])
            campaign_stats["scenarios"].append(result["scenario_name"])

        # Save report
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2)
            print(f"\n📊 Report saved to: {output_path}")

        # Print summary
        print("\n" + "=" * 60)
        print("VALIDATION-ONLY APPROACH RESULTS")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(
            f"Tests with Desync: {total_desyncs} ({total_desyncs / total_tests * 100:.1f}%)"
        )
        print(
            f"Entity Detection Rate: {report['summary']['entity_detection_rate'] * 100:.1f}%"
        )
        print(f"Average Validation Time: {avg_validation_time:.2f}ms")
        print("\nBy Campaign:")
        for campaign_id, stats in report["by_campaign"].items():
            desync_rate = stats["scenarios_with_desync"] / stats["total_scenarios"]
            print(
                f"  {campaign_id}: {stats['scenarios_with_desync']}/{stats['total_scenarios']} desyncs ({desync_rate * 100:.1f}%)"
            )

        return report


# Example usage for testing
if __name__ == "__main__":
    print("Validation-Only Approach Test Runner")
    print("====================================")

    # Create test instance
    validator = ValidationOnlyApproach()

    # Example test case from Sariel campaign
    sariel_state = {
        "player_character_data": {
            "name": "Sariel Arcanus",
            "hp_current": 8,
            "hp_max": 8,
        },
        "npc_data": {
            "Cassian Arcanus": {
                "name": "Prince Cassian Arcanus",
                "present": True,
                "relationship": "brother",
            },
            "Valerius Arcanus": {
                "name": "Prince Valerius Arcanus",
                "present": False,
                "relationship": "brother",
            },
            "Lady Cressida Valeriana": {
                "name": "Lady Cressida Valeriana",
                "present": True,
                "relationship": "friend",
            },
        },
        "world_data": {"current_location": "Cressida's Chambers"},
    }

    # Example narrative with potential desync
    test_narrative = """
    Cressida's chambers offered a small respite from the cold judgment of the Spire.
    Your friend looked up from her desk, immediately softening with concern as she
    saw your tear-stained face. Without a word, she rose and embraced you, offering
    the comfort you desperately needed.
    """

    # Test the scenario
    result = validator.test_campaign_scenario(
        campaign_id="sariel_v2_real",
        scenario_name="Seeking Comfort from Cressida",
        game_state=sariel_state,
        narrative=test_narrative,
    )

    # Generate report
    validator.generate_report("analysis/validation_only_test.json")
