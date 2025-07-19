#!/usr/bin/env python3
"""
Test entity tracking on REAL Sariel campaign first 10 interactions
This uses the actual player inputs and game states from the campaign
"""

import json
import os
from datetime import datetime

# Ensure we're using the venv
venv_path = "/home/jleechan/.claude-squad/worktrees/statesync2_184d8886fb5997c5/prototype/tests/milestone_0.4/venv"
if os.path.exists(venv_path):
    activate_this = os.path.join(venv_path, "bin", "activate_this.py")
    if os.path.exists(activate_this):
        exec(open(activate_this).read(), {"__file__": activate_this})

from test_structured_generation import TestApproach
from test_structured_generation_real import RealLLMTestHarness


def load_real_campaign_data():
    """Load the actual Sariel campaign first 10 interactions"""
    # Try to load from the JSON log file
    json_path = "/home/jleechan/.claude-squad/worktrees/statesync2_184d8886fb5997c5/prototype/tests/milestone_0.4/tmp/sariel_v2_first_10_log.json"
    if os.path.exists(json_path):
        with open(json_path) as f:
            return json.load(f)

    # Otherwise parse from the full campaign file
    campaign_path = "/home/jleechan/projects/worldarchitect.ai/tmp/sariel_v2_latest.txt"
    if not os.path.exists(campaign_path):
        raise FileNotFoundError(f"Campaign file not found: {campaign_path}")

    # This would require parsing the full campaign file
    # For now, we'll use the JSON if available
    raise NotImplementedError("Full campaign parsing not implemented")


def extract_entities_from_context(interaction_data, previous_state=None):
    """Extract expected entities based on campaign context"""
    entities = set()

    # Always include the player character
    entities.add("Sariel")

    # Check player input for entity mentions
    player_input = interaction_data.get("player_input", {}).get("content", "").lower()

    # Specific entity detection based on real campaign
    if "cassian" in player_input:
        entities.add("Cassian")
    if "valerius" in player_input:
        entities.add("Valerius")
    if "cressida" in player_input or "lady cressida" in player_input:
        entities.add("Lady Cressida Valeriana")
    if "elara" in player_input:
        entities.add("Elara")

    # Check location for context
    location = interaction_data.get("location", "")
    if "Valerius's Study" in location:
        entities.add("Valerius")
    if "Lady Cressida" in location:
        entities.add("Lady Cressida Valeriana")

    # Add entities from previous narrative context if available
    if previous_state and "entities_present" in previous_state:
        entities.update(previous_state["entities_present"])

    return list(entities)


def build_prompt_from_interaction(interaction_data, approach):
    """Build a prompt that matches the real campaign interaction"""
    player_input = interaction_data["player_input"]["content"]
    location = interaction_data["location"]
    timestamp = interaction_data["timestamp"]

    # Build context from the campaign
    prompt = f"""You are the Game Master for a D&D campaign.

Current Status:
- Time: {timestamp}
- Location: {location}
- Player Character: Sariel (a member of House Arcanus)

Player says: "{player_input}"

Generate a narrative response that continues the story."""

    if approach in [TestApproach.PYDANTIC_ONLY, TestApproach.COMBINED]:
        # Add entity tracking instructions
        expected_entities = extract_entities_from_context(interaction_data)
        prompt += f"""

IMPORTANT: You must mention ALL of these entities in your narrative:
{", ".join(expected_entities)}

Format your response as JSON with these fields:
- narrative: the story text
- entities_mentioned: array of all character names mentioned
- location_confirmed: the current location"""

    return prompt


def main():
    """Test entity tracking on real Sariel campaign"""
    print("=== Testing Entity Tracking on REAL Sariel Campaign ===")
    print("First 10 actual player interactions")
    print()

    # Load real campaign data
    try:
        campaign_data = load_real_campaign_data()
    except Exception as e:
        print(f"Error loading campaign data: {e}")
        return

    print(f"Loaded {len(campaign_data['interactions'])} real interactions")
    print(f"Original test date: {campaign_data['test_date']}")
    print()

    # Initialize test harness
    harness = RealLLMTestHarness(use_real_api=True, dry_run=False)

    # Test each approach
    results_by_approach = {}

    for approach in [
        TestApproach.VALIDATION_ONLY,
        TestApproach.PYDANTIC_ONLY,
        TestApproach.COMBINED,
    ]:
        print(f"\n{'=' * 70}")
        print(f"Testing: {approach.value}")
        print(f"{'=' * 70}")

        approach_results = []
        cassian_tracked = False

        for i, interaction in enumerate(campaign_data["interactions"][:10]):
            print(f'\n[{i + 1}/10] Player: "{interaction["player_input"]["content"]}"')
            print(f"Location: {interaction['location']}")

            # Build prompt from real interaction
            prompt = build_prompt_from_interaction(interaction, approach)

            # Get expected entities
            expected_entities = extract_entities_from_context(interaction)
            print(f"Expected entities: {expected_entities}")

            try:
                # Generate narrative with real API
                if approach == TestApproach.VALIDATION_ONLY:
                    system_instruction = "You are a helpful D&D Game Master."
                elif approach == TestApproach.PYDANTIC_ONLY:
                    system_instruction = (
                        "Generate narrative with entity tracking in JSON format."
                    )
                else:  # COMBINED
                    system_instruction = "Generate narrative ensuring all entities are mentioned, return JSON."

                response = harness.gemini_client.generate_narrative(
                    prompt, system_instruction
                )

                if response["success"]:
                    narrative = response["text"]

                    # Parse entities based on approach
                    entities_found = []
                    if approach == TestApproach.VALIDATION_ONLY:
                        # Simple text search
                        for entity in expected_entities:
                            if entity.lower() in narrative.lower():
                                entities_found.append(entity)
                    else:
                        # Parse JSON response
                        try:
                            data = json.loads(narrative)
                            entities_found = data.get("entities_mentioned", [])
                            narrative = data.get("narrative", narrative)
                        except:
                            # Fallback to text search
                            for entity in expected_entities:
                                if entity.lower() in narrative.lower():
                                    entities_found.append(entity)

                    # Check if Cassian was tracked when mentioned
                    if "Cassian" in expected_entities and "Cassian" in entities_found:
                        cassian_tracked = True

                    entities_missing = [
                        e for e in expected_entities if e not in entities_found
                    ]

                    result = {
                        "interaction": i + 1,
                        "player_input": interaction["player_input"]["content"],
                        "expected": expected_entities,
                        "found": entities_found,
                        "missing": entities_missing,
                        "success": len(entities_missing) == 0,
                    }
                    approach_results.append(result)

                    if entities_missing:
                        print(f"❌ Missing: {entities_missing}")
                    else:
                        print("✅ All entities tracked!")

                else:
                    print(f"⚠️ API error: {response.get('error')}")

            except Exception as e:
                print(f"⚠️ Error: {str(e)}")

        # Store results
        results_by_approach[approach.value] = {
            "results": approach_results,
            "cassian_tracked": cassian_tracked,
        }

    # Final summary
    print("\n" + "=" * 80)
    print("FINAL RESULTS - REAL SARIEL CAMPAIGN")
    print("=" * 80)

    for approach, data in results_by_approach.items():
        results = data["results"]
        if not results:
            continue

        successful = sum(1 for r in results if r["success"])
        total = len(results)

        print(f"\n{approach}:")
        print(f"  Success Rate: {successful}/{total} ({successful / total * 100:.1f}%)")
        print(f"  Cassian Tracked: {'YES' if data['cassian_tracked'] else 'NO'}")

        # Show specific failures
        failures = [r for r in results if not r["success"]]
        if failures:
            print("  Failed interactions:")
            for f in failures[:3]:
                print(
                    f'    • #{f["interaction"]}: "{f["player_input"]}" - Missing {f["missing"]}'
                )

    # The Cassian Problem
    print("\n" + "-" * 60)
    print("THE CASSIAN PROBLEM (Interaction #2)")
    print("-" * 60)
    print('Player said: "ask for forgiveness. tell cassian i was scared and helpless"')

    for approach, data in results_by_approach.items():
        if len(data["results"]) >= 2:
            interaction_2 = data["results"][1]  # 0-indexed
            cassian_found = "Cassian" in interaction_2.get("found", [])
            print(f"{approach}: Cassian {'✓ TRACKED' if cassian_found else '✗ MISSED'}")

    # Save results
    output_file = (
        f"real_sariel_campaign_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(output_file, "w") as f:
        json.dump(
            {
                "test_date": datetime.now().isoformat(),
                "campaign": "sariel_v2_001",
                "interactions_tested": 10,
                "results": results_by_approach,
            },
            f,
            indent=2,
        )

    print(f"\n✅ Results saved to: {output_file}")

    # Cost summary
    cost_summary = harness.get_cost_summary()
    print(f"\nTotal API calls: {cost_summary['total_calls']}")
    print(f"Total cost: ${cost_summary['total_cost_usd']:.4f}")


if __name__ == "__main__":
    main()
