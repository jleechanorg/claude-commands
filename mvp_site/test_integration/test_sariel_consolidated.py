"""
Consolidated Sariel campaign test that combines functionality from multiple redundant tests.
This replaces: test_sariel_single_campaign_full.py, test_sariel_with_prompts.py,
and test_sariel_production_validation.py

Usage:
- Basic test: Run with default settings (1 campaign, 3 interactions)
- Full test: Set SARIEL_FULL_TEST=true for 10 interactions
- Debug mode: Set SARIEL_DEBUG_PROMPTS=true to log prompts
- Multiple runs: Set SARIEL_REPLAYS=5 to run 5 campaigns
"""

import json
import os
import sys
import unittest
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integration_test_lib import IntegrationTestSetup
from main import create_app


class TestSarielConsolidated(unittest.TestCase):
    """Consolidated Sariel campaign test with configurable options"""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

        # Configurable options via environment variables
        cls.debug_prompts = os.environ.get("SARIEL_DEBUG_PROMPTS", "").lower() == "true"
        cls.full_test = os.environ.get("SARIEL_FULL_TEST", "").lower() == "true"
        cls.num_replays = int(os.environ.get("SARIEL_REPLAYS", "1"))

        # Determine number of interactions
        cls.num_interactions = 10 if cls.full_test else 3

        print("\nSariel Test Configuration:")
        print(f"- Debug prompts: {cls.debug_prompts}")
        print(f"- Full test: {cls.full_test} ({cls.num_interactions} interactions)")
        print(f"- Number of replays: {cls.num_replays}")

    def test_sariel_campaign(self):
        """Run Sariel campaign with entity tracking validation"""

        total_success = 0
        total_entities_found = 0
        total_entities_expected = 0
        all_results = []

        # Load test data
        test_data_path = os.path.join(
            os.path.dirname(__file__), "data", "sariel_campaign_prompts.json"
        )
        with open(test_data_path) as f:
            test_data = json.load(f)

        # Run specified number of replays
        for replay_num in range(self.num_replays):
            print(f"\n{'=' * 60}")
            print(f"Running Sariel Campaign Replay {replay_num + 1}/{self.num_replays}")
            print(f"{'=' * 60}")

            # Create campaign with comprehensive options
            user_id = f"test-sariel-{replay_num}"
            campaign_data = {
                "prompt": test_data["prompts"][0]["input"],
                "title": f"Sariel Test Campaign {replay_num + 1}",
                "selected_prompts": ["narrative", "mechanics"],
                "custom_options": ["companions", "defaultWorld"],
            }

            response = self.client.post(
                "/api/campaigns",
                headers=IntegrationTestSetup.create_test_headers(user_id),
                data=json.dumps(campaign_data),
                content_type="application/json",
            )

            self.assertEqual(
                response.status_code,
                201,
                f"Failed to create campaign: {response.get_data(as_text=True)}",
            )
            campaign_id = response.get_json()["campaign_id"]

            # Run interactions
            for i in range(self.num_interactions):
                interaction_num = i + 2  # Starting from interaction 2

                # Use test data prompts if available, otherwise use default
                if interaction_num < len(test_data["prompts"]):
                    prompt_data = test_data["prompts"][interaction_num]
                    user_input = prompt_data["input"]
                    # Expected entities can be in 'expected_entities' or 'context.expected_entities'
                    expected_entities = prompt_data.get("expected_entities", [])
                    if not expected_entities and "context" in prompt_data:
                        expected_entities = prompt_data["context"].get(
                            "expected_entities", []
                        )
                else:
                    user_input = "1"  # Default choice
                    expected_entities = []

                # Debug prompt logging
                if self.debug_prompts:
                    print(f"\n--- Interaction {interaction_num} ---")
                    print(f"User input: {user_input}")

                # Submit interaction
                interaction_data = {"input": user_input, "mode": "character"}

                response = self.client.post(
                    f"/api/campaigns/{campaign_id}/interaction",
                    headers=IntegrationTestSetup.create_test_headers(user_id),
                    data=json.dumps(interaction_data),
                    content_type="application/json",
                )
                self.assertEqual(
                    response.status_code,
                    200,
                    f"Failed at interaction {interaction_num}",
                )

                # Parse response
                response_data = response.get_json()
                narrative = response_data.get("message", "")
                game_state_data = response_data.get("gameState", {})

                # Debug prompt logging - show first 50 lines
                if self.debug_prompts and hasattr(response, "_debug_prompt"):
                    print("\nFirst 50 lines of prompt sent to LLM:")
                    prompt_lines = response._debug_prompt.split("\n")[:50]
                    for line in prompt_lines:
                        print(line)

                # Validate entity tracking
                found_entities = self._validate_entities(narrative, expected_entities)
                total_entities_expected += len(expected_entities)
                total_entities_found += len(found_entities)

                # Validate game state updates
                state_validation = self._validate_game_state(
                    game_state_data, interaction_num
                )

                # Track results
                interaction_result = {
                    "replay": replay_num + 1,
                    "interaction": interaction_num,
                    "user_input": user_input,
                    "expected_entities": expected_entities,
                    "found_entities": found_entities,
                    "missing_entities": list(
                        set(expected_entities) - set(found_entities)
                    ),
                    "entity_success": len(found_entities) == len(expected_entities),
                    "state_valid": state_validation["valid"],
                    "field_count": state_validation["field_count"],
                }

                all_results.append(interaction_result)

                if interaction_result["entity_success"]:
                    total_success += 1

                # Print results for this interaction
                status = "✓" if interaction_result["entity_success"] else "✗"
                print(
                    f"Interaction {interaction_num}: {status} "
                    + f"(found {len(found_entities)}/{len(expected_entities)} entities, "
                    + f"{state_validation['field_count']} fields validated)"
                )

                if not interaction_result["entity_success"]:
                    print(f"  Missing: {interaction_result['missing_entities']}")

        # Calculate and print summary statistics
        total_interactions = self.num_replays * self.num_interactions
        success_rate = (
            (total_success / total_interactions) * 100 if total_interactions > 0 else 0
        )
        entity_rate = (
            (total_entities_found / total_entities_expected) * 100
            if total_entities_expected > 0
            else 0
        )

        print(f"\n{'=' * 60}")
        print("SUMMARY STATISTICS")
        print(f"{'=' * 60}")
        print(f"Total interactions: {total_interactions}")
        print(
            f"Successful interactions: {total_success}/{total_interactions} ({success_rate:.1f}%)"
        )
        print(
            f"Entities found: {total_entities_found}/{total_entities_expected} ({entity_rate:.1f}%)"
        )

        # Check for Cassian Problem
        cassian_problems = [
            r for r in all_results if "Cassian" in r["missing_entities"]
        ]
        if cassian_problems:
            print(f"\nCassian Problem occurrences: {len(cassian_problems)}")
            for cp in cassian_problems[:3]:  # Show first 3
                print(
                    f"  - Replay {cp['replay']}, Interaction {cp['interaction']}: {cp['user_input']}"
                )

        # Save detailed results if in debug mode
        if self.debug_prompts:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = f"test_results_sariel_{timestamp}.json"
            with open(results_file, "w") as f:
                json.dump(
                    {
                        "configuration": {
                            "debug_prompts": self.debug_prompts,
                            "full_test": self.full_test,
                            "num_replays": self.num_replays,
                            "num_interactions": self.num_interactions,
                        },
                        "summary": {
                            "total_interactions": total_interactions,
                            "success_rate": success_rate,
                            "entity_rate": entity_rate,
                        },
                        "detailed_results": all_results,
                    },
                    f,
                    indent=2,
                )
            print(f"\nDetailed results saved to: {results_file}")

        # Assert minimum success thresholds
        self.assertGreaterEqual(
            success_rate, 50.0, f"Success rate {success_rate:.1f}% below 50% threshold"
        )
        self.assertGreaterEqual(
            entity_rate,
            60.0,
            f"Entity tracking rate {entity_rate:.1f}% below 60% threshold",
        )

    def _validate_entities(self, narrative, expected_entities):
        """Validate that expected entities appear in the narrative"""
        found_entities = []
        narrative_lower = narrative.lower()

        for entity in expected_entities:
            if entity.lower() in narrative_lower:
                found_entities.append(entity)

        return found_entities

    def _validate_game_state(self, game_state, interaction_num):
        """Validate game state updates and count fields"""
        validation_result = {"valid": True, "field_count": 0, "issues": []}

        # Count player character fields
        if "player_character_data" in game_state:
            pc_data = game_state["player_character_data"]
            if isinstance(pc_data, dict):
                validation_result["field_count"] += len(pc_data)

                # Check critical fields
                critical_fields = ["name", "hp_current", "hp_max"]
                for field in critical_fields:
                    if field not in pc_data:
                        validation_result["issues"].append(f"Missing PC field: {field}")
                        validation_result["valid"] = False

        # Count NPC fields
        if "npc_data" in game_state:
            npc_data = game_state["npc_data"]
            if isinstance(npc_data, dict):
                for npc_id, npc_info in npc_data.items():
                    if isinstance(npc_info, dict):
                        validation_result["field_count"] += len(npc_info)

        # Count world data fields
        if "world_data" in game_state:
            world_data = game_state["world_data"]
            if isinstance(world_data, dict):
                validation_result["field_count"] += len(world_data)

        return validation_result


if __name__ == "__main__":
    unittest.main()
