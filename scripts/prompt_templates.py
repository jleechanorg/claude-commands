#!/usr/bin/env python3
"""
Prompt templates for different approaches in Milestone 0.4
"""

from typing import Any

from schemas.entities_simple import SceneManifest, create_from_game_state

from scripts.test_scenarios import get_scenario


class PromptTemplates:
    """Collection of prompt templates for different approaches"""

    @staticmethod
    def get_baseline_prompt(game_state: dict[str, Any], context: str = "") -> str:
        """Current-style prompt (baseline approach)"""
        location = game_state.get("location", "the location")
        pc_name = game_state.get("player_character_data", {}).get(
            "name", "the character"
        )

        return f"""Continue the narrative from this game state:
Location: {location}
Character: {pc_name}

{context}

Write a narrative paragraph continuing the story."""


    @staticmethod
    def get_structured_json_prompt(manifest: SceneManifest) -> str:
        """Structured prompt with JSON schema"""
        return f"""{manifest.to_prompt_format()}

Generate a narrative response following this JSON structure:
{{
    "narrative": "The narrative text describing the scene",
    "entities_mentioned": ["list", "of", "character", "names"],
    "location_confirmed": "{manifest.current_location.display_name}"
}}

REQUIREMENTS:
- Include ALL visible, conscious characters listed above
- Maintain narrative flow and quality
- Be specific about who is present"""


    @staticmethod
    def get_xml_structured_prompt(manifest: SceneManifest) -> str:
        """XML-formatted structure prompt"""
        entities = manifest.get_expected_entities()

        return f"""{manifest.to_prompt_format()}

Generate narrative in this XML format:

<narrative>
    <location>{manifest.current_location.display_name}</location>
    <required_entities>
        {chr(10).join(f"        <entity>{e}</entity>" for e in entities)}
    </required_entities>
    <story>
        [Your narrative here - must mention ALL required entities]
    </story>
</narrative>"""


    @staticmethod
    def get_chain_of_thought_prompt(
        game_state: dict[str, Any], expected_entities: list[str]
    ) -> str:
        """Chain-of-thought entity tracking prompt"""
        location = game_state.get("location", "the location")

        return f"""Location: {location}

First, identify who is present:
{chr(10).join(f"- {entity}: [present/absent/status]" for entity in expected_entities)}

Then write a narrative that includes ALL present characters.

Think step by step:
1. Who is here?
2. What are they doing?
3. How do they interact?

Narrative:"""


    @staticmethod
    def get_minimal_prompt(expected_entities: list[str], location: str) -> str:
        """Minimal intervention prompt (list only)"""
        return f"""Location: {location}
Present: {", ".join(expected_entities)}

Continue the narrative. Include everyone listed above."""


    @staticmethod
    def get_validation_hints_prompt(manifest: SceneManifest) -> str:
        """Prompt with validation hints embedded"""
        entities = manifest.get_expected_entities()

        return f"""{manifest.to_prompt_format()}

CRITICAL VALIDATION REQUIREMENTS:
1. Must mention each character by name: {", ".join(entities)}
2. Use exact names as provided (case-sensitive)
3. Confirm location: {manifest.current_location.display_name}
4. Account for any special conditions (hidden, injured, etc.)

Write a narrative paragraph that will pass entity validation."""



def get_prompt_for_approach(
    approach: str,
    game_state: dict[str, Any],
    manifest: SceneManifest = None,
    expected_entities: list[str] = None,
) -> str:
    """Get appropriate prompt for the testing approach"""

    templates = PromptTemplates()

    if approach == "baseline":
        return templates.get_baseline_prompt(game_state)
    if approach == "json_structured":
        return templates.get_structured_json_prompt(manifest)
    if approach == "xml_structured":
        return templates.get_xml_structured_prompt(manifest)
    if approach == "chain_of_thought":
        return templates.get_chain_of_thought_prompt(game_state, expected_entities)
    if approach == "minimal":
        location = game_state.get("location", "Unknown")
        return templates.get_minimal_prompt(expected_entities, location)
    if approach == "validation_hints":
        return templates.get_validation_hints_prompt(manifest)
    # Default to baseline
    return templates.get_baseline_prompt(game_state)


def test_prompts():
    """Test prompt generation"""

    # Get a test scenario
    scenario = get_scenario("multi_character")
    game_state = scenario["game_state"]
    expected = scenario["expected_entities"]

    # Create manifest
    manifest = create_from_game_state(game_state, 1, 1)

    print("PROMPT TEMPLATE EXAMPLES")
    print("=" * 60)

    # Test each template
    templates = [
        ("Baseline", "baseline"),
        ("JSON Structured", "json_structured"),
        ("XML Structured", "xml_structured"),
        ("Chain of Thought", "chain_of_thought"),
        ("Minimal", "minimal"),
        ("Validation Hints", "validation_hints"),
    ]

    for name, template_type in templates:
        print(f"\n{name}:")
        print("-" * 40)
        prompt = get_prompt_for_approach(template_type, game_state, manifest, expected)
        print(prompt[:300] + "..." if len(prompt) > 300 else prompt)


if __name__ == "__main__":
    test_prompts()
