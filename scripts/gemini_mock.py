#!/usr/bin/env python3
"""
Mock Gemini API for testing Milestone 0.4
Simulates API behavior without actual calls
"""

import asyncio
import json
import random
import re
from dataclasses import dataclass
from typing import Any


@dataclass
class GeminiResponse:
    """Mock response from Gemini API"""

    text: str
    tokens_used: int
    generation_time_ms: float
    model: str = "gemini-1.5-flash"


class MockGeminiAPI:
    """Mock Gemini API for testing"""

    def __init__(self, config: dict[str, Any] = None):
        self.config = config or {
            "model": "gemini-1.5-flash",
            "temperature": 0.7,
            "max_tokens": 500,
            "timeout_seconds": 30,
        }
        self.call_count = 0
        self.total_tokens = 0
        self.failure_rate = 0.05  # 5% failure rate for testing

    async def generate_narrative_async(
        self, prompt: str, approach: str = "baseline"
    ) -> GeminiResponse:
        """Async generation with realistic delays"""
        # Simulate API delay
        delay = random.uniform(0.5, 2.0)
        await asyncio.sleep(delay)

        # Simulate failures
        if random.random() < self.failure_rate:
            raise Exception("Mock API timeout")

        # Generate based on approach
        response_text = self._generate_mock_response(prompt, approach)

        # Calculate metrics
        tokens = len(prompt.split()) + len(response_text.split())

        return GeminiResponse(
            text=response_text, tokens_used=tokens, generation_time_ms=delay * 1000
        )

    def generate_narrative(
        self, prompt: str, approach: str = "baseline"
    ) -> GeminiResponse:
        """Sync wrapper for generation"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.generate_narrative_async(prompt, approach)
            )
        finally:
            loop.close()

    def _generate_mock_response(self, prompt: str, approach: str) -> str:
        """Generate mock response based on approach"""

        # Extract entities from prompt
        entities = self._extract_entities_from_prompt(prompt)

        if approach == "json_structured":
            # Return JSON response
            included = entities[:3] if len(entities) > 3 else entities
            response = {
                "narrative": f"The party gathered together. {' and '.join(included)} discussed their plans.",
                "entities_mentioned": included,
                "location_confirmed": "The Silver Stag Tavern",
            }
            return json.dumps(response, indent=2)

        if approach == "xml_structured":
            # Return XML response
            included = entities[:3] if len(entities) > 3 else entities
            narrative = f"{' and '.join(included)} stood ready for action."
            return f"""<narrative>
    <location>The Silver Stag Tavern</location>
    <required_entities>
        {chr(10).join(f"        <entity>{e}</entity>" for e in included)}
    </required_entities>
    <story>
        {narrative}
    </story>
</narrative>"""

        if approach == "chain_of_thought":
            # Include thinking process
            included = entities[:2] if len(entities) > 2 else entities
            return f"""Who is present:
- {entities[0]}: present and ready
{f"- {entities[1]}: present" if len(entities) > 1 else ""}
{f"- {entities[2]}: absent" if len(entities) > 2 else ""}

Narrative: {included[0]} surveyed the scene{f" while {included[1]} stood nearby" if len(included) > 1 else ""}."""

        if approach == "validation_hints":
            # Include all entities explicitly
            narrative_parts = ["In the scene,"]
            for i, entity in enumerate(entities):
                if i == len(entities) - 1:
                    narrative_parts.append(f"and {entity}")
                else:
                    narrative_parts.append(f"{entity},")
            narrative_parts.append("were all present.")
            return " ".join(narrative_parts)

        # Baseline - miss some entities
        if entities:
            return (
                f"{entities[0]} looked around the area, ready for whatever came next."
            )
        return "The scene was quiet."

    def _extract_entities_from_prompt(self, prompt: str) -> list[str]:
        """Extract entity names from prompt"""
        entities = []

        # Look for common patterns
        if "Present:" in prompt:
            # Minimal prompt style
            line = prompt.split("Present:")[1].split("\n")[0]
            entities = [e.strip() for e in line.split(",")]
        elif "<entity>" in prompt:
            # XML style

            entities = re.findall(r"<entity>(.*?)</entity>", prompt)
        elif '"entities_mentioned"' in prompt:
            # JSON style - extract from requirements
            if "Lyra" in prompt:
                entities = ["Lyra", "Theron", "Marcus", "Elara"]
        else:
            # Try to find character names (capitalized words)

            words = re.findall(r"\b[A-Z][a-z]+\b", prompt)
            # Filter common words
            entities = [
                w
                for w in words
                if w
                not in [
                    "The",
                    "Location",
                    "Character",
                    "Narrative",
                    "Generate",
                    "Continue",
                    "Write",
                    "Present",
                    "REQUIREMENTS",
                ]
            ]

        return entities[:4]  # Limit to 4 for testing

    def batch_generate(self, prompts: list[tuple[str, str]]) -> list[GeminiResponse]:
        """Batch generation for multiple prompts"""
        results = []
        for prompt, approach in prompts:
            try:
                result = self.generate_narrative(prompt, approach)
                results.append(result)
                self.call_count += 1
                self.total_tokens += result.tokens_used
            except Exception as e:
                # Return error response
                results.append(
                    GeminiResponse(
                        text=f"Error: {str(e)}", tokens_used=0, generation_time_ms=0
                    )
                )
        return results

    def get_stats(self) -> dict[str, Any]:
        """Get API usage statistics"""
        return {
            "total_calls": self.call_count,
            "total_tokens": self.total_tokens,
            "estimated_cost": self.total_tokens * 0.000001,  # Mock pricing
            "model": self.config["model"],
        }


def test_mock_api():
    """Test the mock API"""
    api = MockGeminiAPI()

    print("Testing Mock Gemini API")
    print("=" * 60)

    # Test different approaches
    test_prompts = [
        ("Generate a story", "baseline"),
        ('{"narrative": "test"}', "json_structured"),
        ("<entity>Lyra</entity>", "xml_structured"),
    ]

    for prompt, approach in test_prompts:
        print(f"\nApproach: {approach}")
        try:
            response = api.generate_narrative(prompt, approach)
            print(f"Response: {response.text[:100]}...")
            print(f"Tokens: {response.tokens_used}")
            print(f"Time: {response.generation_time_ms:.0f}ms")
        except Exception as e:
            print(f"Error: {e}")

    print(f"\nStats: {api.get_stats()}")


if __name__ == "__main__":
    test_mock_api()
