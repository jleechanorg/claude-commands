#!/usr/bin/env python3
"""
Mock integration with game_state.py interface.
Demonstrates how validators would integrate with the actual game system.
"""

from datetime import datetime
from typing import Any


# Mock GameState class (simplified version)
class MockGameState:
    """Mock version of the actual GameState class."""

    def __init__(self):
        self.current_location = "Kaelan's Cell"
        self.party_members = ["Gideon", "Rowan"]
        self.entity_states = {
            "Gideon": ["conscious", "armed"],
            "Rowan": ["conscious", "healing"],
        }
        self.last_narrative = ""
        self._manifest_cache = None
        self._manifest_timestamp = None

    def get_active_entity_manifest(self) -> dict[str, Any]:
        """
        Generate manifest of all active entities in current scene.
        This would be the actual implementation in game_state.py
        """
        # Check cache
        current_time = datetime.now()
        if (
            self._manifest_cache
            and self._manifest_timestamp
            and (current_time - self._manifest_timestamp).seconds < 60
        ):
            return self._manifest_cache

        # Generate manifest
        manifest = {
            "location": self.current_location,
            "entities": [],
            "timestamp": current_time.isoformat(),
            "entity_count": 0,
        }

        for member in self.party_members:
            entity = {
                "id": f"{member.lower()}_001",
                "name": member,
                "type": "player_character",
                "status": self.entity_states.get(member, ["conscious"]),
                "descriptors": self._get_descriptors(member),
            }
            manifest["entities"].append(entity)

        manifest["entity_count"] = len(manifest["entities"])

        # Cache result
        self._manifest_cache = manifest
        self._manifest_timestamp = current_time

        return manifest

    def _get_descriptors(self, entity_name: str) -> list[str]:
        """Get descriptors for entity."""
        descriptors = {
            "Gideon": ["gideon", "ser vance", "knight", "warrior"],
            "Rowan": ["rowan", "healer", "cleric", "priestess"],
        }
        return descriptors.get(entity_name, [entity_name.lower()])

    def validate_narrative_consistency(
        self, narrative_text: str, strictness: str = "normal"
    ) -> dict[str, Any]:
        """
        Validate narrative against current entity manifest.
        This is where our validators would be integrated.
        """
        # Import our validators
        from .validators.fuzzy_token_validator import FuzzyTokenValidator
        from .validators.hybrid_validator import HybridValidator

        # Get current manifest
        manifest = self.get_active_entity_manifest()
        expected_entities = [e["name"] for e in manifest["entities"]]

        # Choose validator based on strictness
        if strictness == "strict":
            validator = HybridValidator(combination_strategy="unanimous")
        elif strictness == "lenient":
            validator = FuzzyTokenValidator(fuzzy_threshold=0.6)
        else:  # normal
            validator = FuzzyTokenValidator()

        # Validate narrative
        try:
            result = validator.validate(
                narrative_text=narrative_text,
                expected_entities=expected_entities,
                location=self.current_location,
            )

            # Convert to game state format
            return {
                "is_valid": result.all_entities_present,
                "missing_entities": result.entities_missing,
                "extra_entities": [],  # Not tracked in our simple version
                "confidence": result.confidence,
                "validation_errors": getattr(result, "errors", []),
                "warnings": getattr(result, "warnings", []),
            }

        except Exception as e:
            return {
                "is_valid": False,
                "missing_entities": expected_entities,
                "extra_entities": [],
                "confidence": 0.0,
                "validation_errors": [str(e)],
                "warnings": ["Validation failed"],
            }


# Integration example for gemini_service.py
class NarrativeValidationMixin:
    """
    Mixin for gemini_service.py to add validation.
    Would be integrated into the actual service.
    """

    def generate_narrative_with_validation(
        self, game_state: MockGameState, prompt: str
    ) -> dict[str, Any]:
        """Generate narrative and validate consistency."""

        # Step 1: Get entity manifest
        manifest = game_state.get_active_entity_manifest()

        # Step 2: Inject manifest into prompt (SECURITY: sanitize first)
        sanitized_entities = [self._sanitize(e["name"]) for e in manifest["entities"]]
        enhanced_prompt = f"""
[SYSTEM: Scene Manifest - Characters present: {", ".join(sanitized_entities)}]
Location: {self._sanitize(manifest["location"])}

{prompt}
"""

        # Step 3: Generate narrative (mock)
        narrative = self._mock_generate_narrative(enhanced_prompt)

        # Step 4: Validate result
        validation = game_state.validate_narrative_consistency(narrative)

        # Step 5: Handle validation failure
        if not validation["is_valid"] and validation["confidence"] < 0.7:
            # Log error
            print(f"NARRATIVE_DESYNC: Missing {validation['missing_entities']}")

            # Retry with stronger prompt
            enhanced_prompt += (
                f"\nIMPORTANT: Include {', '.join(validation['missing_entities'])}"
            )
            narrative = self._mock_generate_narrative(enhanced_prompt)

            # Re-validate
            validation = game_state.validate_narrative_consistency(narrative)

        return {
            "narrative": narrative,
            "validation": validation,
            "manifest_used": manifest,
        }

    def _sanitize(self, text: str) -> str:
        """Sanitize text to prevent prompt injection."""
        # Remove special characters that could break prompts
        return text.replace('"', "").replace("'", "").replace("\\", "")

    def _mock_generate_narrative(self, prompt: str) -> str:
        """Mock narrative generation."""
        if "Gideon" in prompt and "Rowan" in prompt:
            return "Gideon raised his sword as Rowan began chanting a healing spell."
        return "The adventurers prepared for what lay ahead."


# Demo integration
def demo_integration():
    """Demonstrate the integration in action."""

    print("=== Game State Integration Demo ===\n")

    # Create game state
    game_state = MockGameState()
    print(f"Location: {game_state.current_location}")
    print(f"Party: {', '.join(game_state.party_members)}")
    print()

    # Test narratives
    test_cases = [
        {
            "narrative": "Gideon stepped forward, shield raised. Rowan followed closely behind.",
            "expected": "VALID",
        },
        {
            "narrative": "The knight advanced alone through the darkness.",
            "expected": "MISSING: Rowan",
        },
        {
            "narrative": "Marcus and Elena explored the cell.",
            "expected": "MISSING: Gideon, Rowan",
        },
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['expected']}")
        print(f"Narrative: {test['narrative']}")

        result = game_state.validate_narrative_consistency(test["narrative"])

        print(f"Valid: {result['is_valid']}")
        print(f"Confidence: {result['confidence']:.2f}")
        if result["missing_entities"]:
            print(f"Missing: {', '.join(result['missing_entities'])}")
        print()

    # Demonstrate service integration
    print("=== Service Integration Demo ===\n")

    service = NarrativeValidationMixin()
    result = service.generate_narrative_with_validation(
        game_state, "Describe the party preparing for battle"
    )

    print(f"Generated: {result['narrative']}")
    print(f"Valid: {result['validation']['is_valid']}")
    print(f"Confidence: {result['validation']['confidence']:.2f}")


if __name__ == "__main__":
    demo_integration()
