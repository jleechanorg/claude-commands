#!/usr/bin/env python3
"""
Comprehensive test of Sariel campaign with FULL game state and entity validation
"""

import json
import logging
import os
import sys
import unittest
from typing import Any

from integration_test_lib import IntegrationTestSetup

# Import setup handled by __init__.py
from main import create_app

# Configure verbose logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Enable debug logging for key modules
logging.getLogger("gemini_service").setLevel(logging.DEBUG)
logging.getLogger("entity_tracking").setLevel(logging.DEBUG)
logging.getLogger("game_state").setLevel(logging.DEBUG)


class TestSarielFullValidation(unittest.TestCase):
    """Run Sariel campaign with comprehensive validation"""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

        # Load Sariel campaign prompts
        prompts_path = os.path.join(
            os.path.dirname(__file__), "data", "sariel_campaign_prompts.json"
        )
        with open(prompts_path) as f:
            cls.sariel_data = json.load(f)

    def test_sariel_full_replays(self):
        """Run 10 full replays with complete validation"""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE SARIEL CAMPAIGN VALIDATION TEST")
        print("Testing: ALL entities, game state fields, and narrative consistency")
        print("=" * 80)

        all_results = []

        for run in range(10):
            print(f"\n\n{'=' * 80}")
            print(f"RUN {run + 1}/10 - FULL VALIDATION")
            print(f"{'=' * 80}")

            run_result = self._run_single_campaign(run)
            all_results.append(run_result)

            # Print run summary
            print(f"\n{'=' * 40}")
            print(f"RUN {run + 1} SUMMARY:")
            print(f"- Total interactions: {run_result['total_interactions']}")
            print(f"- State update successes: {run_result['state_update_successes']}")
            print(f"- Entity tracking rate: {run_result['entity_tracking_rate']:.1%}")
            print(
                f"- Cassian problem: {'SOLVED ✓' if run_result['cassian_mentioned'] else 'FAILED ✗'}"
            )
            print(
                f"- Game state valid: {'YES ✓' if run_result['game_state_valid'] else 'NO ✗'}"
            )
            print(f"{'=' * 40}")

        # Final summary
        self._print_final_summary(all_results)

    def _run_single_campaign(self, run_number: int) -> dict[str, Any]:
        """Run a single campaign with full validation"""
        user_id = f"test-sariel-full-{run_number}"

        result = {
            "run": run_number + 1,
            "total_interactions": 0,
            "state_update_successes": 0,
            "entity_tracking_successes": 0,
            "cassian_mentioned": False,
            "game_state_valid": True,
            "validation_errors": [],
            "entities_tracked": {},
            "missing_entities": [],
            "game_states": [],
        }

        # Create campaign
        initial_prompt = self.sariel_data["prompts"][0]
        campaign_data = {
            "prompt": initial_prompt["input"],
            "title": f"Sariel Full Test {run_number}",
            "selected_prompts": ["narrative", "mechanics"],
        }

        response = self.client.post(
            "/api/campaigns",
            headers=IntegrationTestSetup.create_test_headers(user_id),
            data=json.dumps(campaign_data),
            content_type="application/json",
        )

        if response.status_code != 201:
            print(f"ERROR: Campaign creation failed: {response.status_code}")
            result["game_state_valid"] = False
            return result

        campaign_id = response.get_json()["campaign_id"]
        print(f"Created campaign: {campaign_id}")

        # Run first 5 interactions
        for i, prompt_data in enumerate(self.sariel_data["prompts"][1:6]):
            print(f"\n--- INTERACTION {i + 1}/5 ---")
            print(f"INPUT: {prompt_data['input']}")
            print(
                f"Expected entities: {prompt_data['context'].get('expected_entities', [])}"
            )

            result["total_interactions"] += 1

            # Submit interaction
            interaction_data = {
                "input": prompt_data["input"],
                "mode": prompt_data.get("mode", "character"),
            }

            response = self.client.post(
                f"/api/campaigns/{campaign_id}/interaction",
                headers=IntegrationTestSetup.create_test_headers(user_id),
                data=json.dumps(interaction_data),
                content_type="application/json",
            )

            if response.status_code != 200:
                print(f"ERROR: Interaction failed: {response.status_code}")
                result["validation_errors"].append(
                    f"Interaction {i + 1} failed: {response.status_code}"
                )
                continue

            response_data = response.get_json()
            narrative = response_data.get("narrative", "")

            # Print narrative preview
            print("\nNARRATIVE PREVIEW (first 200 chars):")
            print(narrative[:200] + "..." if len(narrative) > 200 else narrative)

            # Get game state after interaction
            state_response = self.client.get(
                f"/api/campaigns/{campaign_id}/state",
                headers=IntegrationTestSetup.create_test_headers(user_id),
            )

            if state_response.status_code == 200:
                game_state_data = state_response.get_json()
                result["game_states"].append(game_state_data)

                # Validate game state
                validation = self._validate_game_state(game_state_data, i + 1)
                if validation["valid"]:
                    result["state_update_successes"] += 1
                else:
                    result["validation_errors"].extend(validation["errors"])
                    result["game_state_valid"] = False

                # Print game state summary
                print("\nGAME STATE SUMMARY:")
                print(
                    f"- Player character: {game_state_data.get('player_character_data', {})}"
                )
                print(f"- NPCs: {list(game_state_data.get('npc_data', {}).keys())}")
                print(
                    f"- Location: {game_state_data.get('world_data', {}).get('current_location_name', 'Unknown')}"
                )
                print(
                    f"- Combat: {game_state_data.get('combat_state', {}).get('in_combat', False)}"
                )

                # Track entities
                expected_entities = prompt_data["context"].get("expected_entities", [])
                found_entities = self._check_entities_in_narrative(
                    narrative, expected_entities
                )

                if len(found_entities) == len(expected_entities):
                    result["entity_tracking_successes"] += 1

                result["entities_tracked"][f"interaction_{i + 1}"] = {
                    "expected": expected_entities,
                    "found": found_entities,
                    "missing": [
                        e for e in expected_entities if e not in found_entities
                    ],
                }

                print("\nENTITY TRACKING:")
                print(f"- Expected: {expected_entities}")
                print(f"- Found: {found_entities}")
                print(
                    f"- Missing: {[e for e in expected_entities if e not in found_entities]}"
                )

            # Check Cassian problem specifically
            if prompt_data["metadata"].get("is_cassian_problem", False):
                if "cassian" in narrative.lower():
                    result["cassian_mentioned"] = True
                    print("\n✓ CASSIAN PROBLEM SOLVED!")
                else:
                    print("\n✗ CASSIAN PROBLEM FAILED!")

        # Calculate entity tracking rate
        if result["total_interactions"] > 0:
            result["entity_tracking_rate"] = (
                result["entity_tracking_successes"] / result["total_interactions"]
            )
        else:
            result["entity_tracking_rate"] = 0

        return result

    def _validate_game_state(
        self, game_state: dict[str, Any], interaction_num: int
    ) -> dict[str, Any]:
        """Validate all fields in game state"""
        validation = {"valid": True, "errors": []}

        # Check required top-level fields
        required_fields = [
            "game_state_version",
            "player_character_data",
            "world_data",
            "npc_data",
            "custom_campaign_state",
            "combat_state",
        ]

        for field in required_fields:
            if field not in game_state:
                validation["valid"] = False
                validation["errors"].append(f"Missing required field: {field}")

        # Validate player character data
        pc_data = game_state.get("player_character_data", {})
        if not pc_data:
            validation["errors"].append("Player character data is empty")

        # Validate NPCs
        npc_data = game_state.get("npc_data", {})
        for npc_id, npc_info in npc_data.items():
            if not isinstance(npc_info, dict):
                validation["valid"] = False
                validation["errors"].append(
                    f"NPC {npc_id} data is not a dictionary: {type(npc_info)}"
                )

        # Validate combat state
        combat_state = game_state.get("combat_state", {})
        if not isinstance(combat_state.get("in_combat"), bool):
            validation["errors"].append("combat_state.in_combat should be boolean")

        return validation

    def _check_entities_in_narrative(
        self, narrative: str, expected_entities: list[str]
    ) -> list[str]:
        """Check which entities are mentioned in the narrative"""
        narrative_lower = narrative.lower()
        found = []

        for entity in expected_entities:
            if entity.lower() in narrative_lower:
                found.append(entity)

        return found

    def _print_final_summary(self, all_results: list[dict[str, Any]]):
        """Print comprehensive summary of all runs"""
        print(f"\n\n{'=' * 80}")
        print("FINAL COMPREHENSIVE SUMMARY")
        print(f"{'=' * 80}")

        # Overall stats
        total_runs = len(all_results)
        cassian_successes = sum(1 for r in all_results if r["cassian_mentioned"])
        valid_states = sum(1 for r in all_results if r["game_state_valid"])

        print("\nOVERALL RESULTS:")
        print(f"- Total runs: {total_runs}")
        print(
            f"- Cassian problem solved: {cassian_successes}/{total_runs} ({cassian_successes / total_runs * 100:.0f}%)"
        )
        print(
            f"- Valid game states: {valid_states}/{total_runs} ({valid_states / total_runs * 100:.0f}%)"
        )

        # Entity tracking stats
        total_entity_checks = sum(r["total_interactions"] for r in all_results)
        total_entity_successes = sum(
            r["entity_tracking_successes"] for r in all_results
        )

        print("\nENTITY TRACKING:")
        print(f"- Total entity checks: {total_entity_checks}")
        print(f"- Successful tracks: {total_entity_successes}")
        print(
            f"- Overall success rate: {total_entity_successes / total_entity_checks * 100:.1f}%"
        )

        # Common validation errors
        all_errors = []
        for r in all_results:
            all_errors.extend(r["validation_errors"])

        if all_errors:
            print("\nCOMMON VALIDATION ERRORS:")
            error_counts = {}
            for error in all_errors:
                error_type = error.split(":")[0]
                error_counts[error_type] = error_counts.get(error_type, 0) + 1

            for error_type, count in sorted(
                error_counts.items(), key=lambda x: x[1], reverse=True
            ):
                print(f"- {error_type}: {count} occurrences")

        # Per-run summary
        print("\nPER-RUN RESULTS:")
        for r in all_results:
            cassian = "✓" if r["cassian_mentioned"] else "✗"
            state = "✓" if r["game_state_valid"] else "✗"
            print(
                f"Run {r['run']}: Cassian {cassian}, State {state}, "
                f"Entity rate: {r['entity_tracking_rate']:.0%}, "
                f"State updates: {r['state_update_successes']}/{r['total_interactions']}"
            )


if __name__ == "__main__":
    unittest.main()
