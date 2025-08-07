#!/usr/bin/env python3
"""
Real-time validation demonstration.
Shows how validation would work during actual gameplay.
"""

import time

# Import our components
from game_state_integration import MockGameState, NarrativeValidationMixin


class GameSession:
    """Simulates a game session with real-time validation."""

    def __init__(self):
        self.game_state = MockGameState()
        self.narrative_service = NarrativeValidationMixin()
        self.validation_stats = {
            "total_narratives": 0,
            "valid_narratives": 0,
            "desync_prevented": 0,
            "total_time": 0.0,
        }

    def simulate_player_action(self, action: str) -> dict:
        """Simulate a player action that triggers narrative generation."""

        start_time = time.time()

        # Update game state based on action
        if "hide" in action.lower():
            self.game_state.entity_states["Rowan"] = ["hidden"]
        elif "separate" in action.lower():
            self.game_state.party_members = ["Gideon"]  # Rowan leaves
        elif "rejoin" in action.lower():
            self.game_state.party_members = ["Gideon", "Rowan"]
            self.game_state.entity_states["Rowan"] = ["conscious"]

        # Generate narrative with validation
        result = self.narrative_service.generate_narrative_with_validation(
            self.game_state, f"Describe the result of: {action}"
        )

        # Update stats
        elapsed = time.time() - start_time
        self.validation_stats["total_narratives"] += 1
        self.validation_stats["total_time"] += elapsed

        if result["validation"]["is_valid"]:
            self.validation_stats["valid_narratives"] += 1
        # Check if we prevented a desync
        elif result["validation"]["confidence"] > 0.7:
            self.validation_stats["desync_prevented"] += 1

        return {
            "action": action,
            "narrative": result["narrative"],
            "validation": result["validation"],
            "time_ms": elapsed * 1000,
            "game_state": {
                "location": self.game_state.current_location,
                "party": self.game_state.party_members.copy(),
                "states": self.game_state.entity_states.copy(),
            },
        }

    def get_performance_metrics(self) -> dict:
        """Get real-time performance metrics."""
        if self.validation_stats["total_narratives"] == 0:
            return {"error": "No narratives generated yet"}

        return {
            "narratives_generated": self.validation_stats["total_narratives"],
            "validation_accuracy": self.validation_stats["valid_narratives"]
            / self.validation_stats["total_narratives"],
            "desyncs_prevented": self.validation_stats["desync_prevented"],
            "avg_validation_time_ms": (self.validation_stats["total_time"] * 1000)
            / self.validation_stats["total_narratives"],
            "estimated_hourly_cost": self.validation_stats["total_narratives"]
            * 0.000175
            * (3600 / self.validation_stats["total_time"]),
        }


def simulate_gameplay_session():
    """Simulate a typical gameplay session with various actions."""

    print("=== Real-Time Validation Demo ===")
    print("Simulating gameplay session with live validation...\n")

    session = GameSession()

    # Simulate various player actions
    actions = [
        "Look around the cell",
        "Gideon searches for hidden passages",
        "Rowan casts detect magic",
        "Tell Rowan to hide in the shadows",
        "The party splits up to cover more ground",
        "Gideon continues alone",
        "Call for Rowan to rejoin",
        "Prepare for combat together",
        "Rest and recover",
    ]

    for i, action in enumerate(actions, 1):
        print(f"\n--- Action {i}: {action} ---")

        # Simulate action
        result = session.simulate_player_action(action)

        # Display results
        print(f"Narrative: {result['narrative']}")
        print(
            f"Valid: {result['validation']['is_valid']} "
            f"(confidence: {result['validation']['confidence']:.2f})"
        )

        if result["validation"]["missing_entities"]:
            print(f"Missing: {', '.join(result['validation']['missing_entities'])}")

        print(f"Time: {result['time_ms']:.1f}ms")

        # Show game state changes
        if i > 1:  # Skip first action
            print(f"Party: {', '.join(result['game_state']['party'])}")
            if any(
                "hidden" in states for states in result["game_state"]["states"].values()
            ):
                print("Note: Some entities are hidden")

        # Simulate time between actions
        time.sleep(0.5)

    # Show final metrics
    print("\n=== Session Performance Metrics ===")
    metrics = session.get_performance_metrics()

    print(f"Total narratives: {metrics['narratives_generated']}")
    print(f"Validation accuracy: {metrics['validation_accuracy']:.1%}")
    print(f"Desyncs prevented: {metrics['desyncs_prevented']}")
    print(f"Avg validation time: {metrics['avg_validation_time_ms']:.1f}ms")
    print(f"Estimated hourly cost: ${metrics['estimated_hourly_cost']:.2f}")

    return session


def demonstrate_caching_impact():
    """Show the impact of caching on performance."""

    print("\n=== Caching Impact Demo ===")

    game_state = MockGameState()

    # First call - no cache
    start = time.time()
    manifest1 = game_state.get_active_entity_manifest()
    time1 = (time.time() - start) * 1000

    # Second call - cached
    start = time.time()
    manifest2 = game_state.get_active_entity_manifest()
    time2 = (time.time() - start) * 1000

    print(f"First call (no cache): {time1:.3f}ms")
    print(f"Second call (cached): {time2:.3f}ms")
    print(f"Speedup: {time1 / time2:.1f}x")

    # Verify same result
    assert manifest1 == manifest2, "Cache returned different result!"
    print("✓ Cache consistency verified")


def demonstrate_edge_case_handling():
    """Show how the system handles edge cases in real-time."""

    print("\n=== Edge Case Handling Demo ===")

    session = GameSession()

    edge_cases = [
        {
            "action": "Someone attacks from the shadows",
            "narrative": "A figure strikes from the darkness. He parries desperately.",
            "challenge": "Ambiguous pronouns",
        },
        {
            "action": "The party encounters Marcus and Elena",
            "narrative": "Marcus and Elena greet the party warmly.",
            "challenge": "Wrong characters mentioned",
        },
        {
            "action": "Gideon shouts for help",
            "narrative": "Gid-- his cry is cut short by an explosion.",
            "challenge": "Partial name",
        },
    ]

    for case in edge_cases:
        print(f"\nChallenge: {case['challenge']}")
        print(f"Action: {case['action']}")

        # Override the mock generator
        original_method = session.narrative_service._mock_generate_narrative
        session.narrative_service._mock_generate_narrative = lambda p: case["narrative"]

        result = session.simulate_player_action(case["action"])

        print(f"Narrative: {result['narrative']}")
        print(
            f"Valid: {result['validation']['is_valid']} "
            f"(confidence: {result['validation']['confidence']:.2f})"
        )

        # Restore original method
        session.narrative_service._mock_generate_narrative = original_method


if __name__ == "__main__":
    # Run all demos
    session = simulate_gameplay_session()
    demonstrate_caching_impact()
    demonstrate_edge_case_handling()

    print("\n✓ Real-time validation demonstration complete!")
