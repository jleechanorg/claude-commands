"""
Fake LLM service for testing.
Returns realistic responses instead of Mock objects to avoid JSON serialization issues.
"""

import json
import re


class FakePart:
    """Fake part object for Gemini response structure."""

    def __init__(self, text: str = ""):
        self.text = text
        self.function_call = None  # No tool calls in fake response


class FakeLLMResponse:
    """Fake LLM response that behaves like the real thing."""

    def __init__(self, text: str, usage_metadata: dict | None = None):
        self.text = text
        self.usage_metadata = usage_metadata or {
            "input_tokens": 100,
            "output_tokens": 200,
            "total_tokens": 300,
        }
        # Create parts list with a FakePart containing the text
        self.parts = [FakePart(text)]
        self.candidates = [self]
        self.content = self

    def __str__(self):
        return self.text


class FakeGenerationConfig:
    """Fake generation config object."""

    def __init__(self, **kwargs):
        self.temperature = kwargs.get("temperature", 0.7)
        self.max_output_tokens = kwargs.get("max_output_tokens", 8192)
        self.response_schema = kwargs.get("response_schema")


class FakeModelAdapter:
    """Fake model adapter that generates realistic responses."""

    def __init__(self, model_name: str = "gemini-3-pro-preview"):
        self.model_name = model_name
        self._response_templates = {
            "campaign_creation": {
                "narrative": "The {setting} stretched before {character}, ancient and mysterious. As {character} stepped forward, the adventure began with a sense of destiny calling...",
                "mechanics": {
                    "health": 100,
                    "level": 1,
                    "experience": 0,
                    "stats": {
                        "strength": 15,
                        "dexterity": 12,
                        "constitution": 14,
                        "intelligence": 13,
                        "wisdom": 16,
                        "charisma": 11,
                    },
                },
                "scene": {
                    "id": 1,
                    "title": "The Journey Begins",
                    "location": "{setting}",
                    "npcs": [],
                    "objects": ["backpack", "sword", "map"],
                    "enemies": [],
                },
                "state_updates": {
                    "current_location": "{setting}",
                    "active_quest": "Begin the adventure",
                    "scene_number": 1,
                },
                "session_header": "Session 1: {setting}",
                "planning_block": {
                    "thinking": "The campaign is starting. I should offer initial path choices.",
                    "choices": {
                        "explore_area": {
                            "text": "Explore Area",
                            "description": "Look around the immediate vicinity",
                            "risk_level": "low",
                        },
                        "check_inventory": {
                            "text": "Check Gear",
                            "description": "Inspect your starting equipment",
                            "risk_level": "none",
                        },
                    },
                },
            },
            "story_continuation": {
                "narrative": "With determination, {character} {user_input}. The path ahead revealed new challenges and opportunities...",
                "mechanics": {"health": 95, "experience": 25},
                "scene": {
                    "id": 2,
                    "title": "The Plot Thickens",
                    "location": "Forest Path",
                    "npcs": ["Mysterious Stranger"],
                    "objects": ["ancient_rune", "healing_potion"],
                    "enemies": [],
                },
                "state_updates": {
                    "scenes_completed": 1,
                    "scene_number": 2,
                    "last_action": "{user_input}",
                },
                "session_header": "Session 1: Forest Path",
                "planning_block": {
                    "thinking": "The user performed an action. I should offer relevant follow-up choices.",
                    "choices": {
                        "talk_npc": {
                            "text": "Talk to Stranger",
                            "description": "Approach the mysterious figure",
                            "risk_level": "medium",
                        },
                        "examine_rune": {
                            "text": "Examine Rune",
                            "description": "Look closely at the ancient symbol",
                            "risk_level": "low",
                        },
                    },
                },
            },
        }

    def generate_content(
        self, prompt: str | dict, generation_config=None
    ) -> "FakeLLMResponse":
        """Generate a fake response based on prompt content.

        Args:
            prompt: Either a string prompt or structured JSON input dict
            generation_config: Generation configuration (optional)
        """

        # Handle structured JSON input
        if isinstance(prompt, dict):
            return self._handle_json_input(prompt)

        # Handle string prompt (legacy)
        return self._handle_string_prompt(prompt)

    def _handle_json_input(self, json_input: dict) -> "FakeLLMResponse":
        """Handle structured JSON input and return appropriate response."""
        message_type = json_input.get("message_type", "unknown")

        if message_type == "initial_story":
            template = self._response_templates["campaign_creation"]
            character_prompt = json_input.get("character_prompt", "")
            context = {"character": self._extract_character_from_text(character_prompt)}
        elif message_type == "story_continuation":
            template = self._response_templates["story_continuation"]
            user_action = json_input.get("user_action", "")
            context = {"user_input": user_action}
        else:
            # Default template for unknown message types
            template = self._response_templates["story_continuation"]
            context = {"user_input": str(json_input)}

        # Fill template with context
        response_data = self._fill_template(template, context)

        # Convert to JSON string as an LLM would return
        response_text = json.dumps(response_data, indent=2)

        return FakeLLMResponse(response_text)

    def _handle_string_prompt(self, prompt: str) -> "FakeLLMResponse":
        """Handle legacy string prompt."""
        # Extract context from prompt for more realistic responses
        context = self._extract_context(prompt)

        # Choose appropriate template
        if "create a campaign" in prompt.lower() or "new campaign" in prompt.lower():
            template = self._response_templates["campaign_creation"]
        else:
            template = self._response_templates["story_continuation"]

        # Fill template with context
        response_data = self._fill_template(template, context)

        # Convert to JSON string as an LLM would return
        response_text = json.dumps(response_data, indent=2)

        return FakeLLMResponse(response_text)

    def _extract_character_from_text(self, text: str) -> str:
        """Extract character name from character prompt text."""
        # Simple extraction - first capitalized word sequence
        words = text.split()
        for i, word in enumerate(words):
            if word and word[0].isupper():
                # Take up to 3 words as character name
                char_words = []
                for j in range(i, min(i + 3, len(words))):
                    if words[j] and words[j][0].isupper():
                        char_words.append(words[j])
                    else:
                        break
                if char_words:
                    return " ".join(char_words)
        return "Hero"  # Default fallback

    def _extract_context(self, prompt: str) -> dict[str, str]:
        """Extract character, setting, and other context from prompt."""
        context = {}

        # Extract character name - try multiple patterns
        char_match = re.search(r"Character[:\s]+([^,\n.]+)", prompt, re.IGNORECASE)
        if not char_match:
            char_match = re.search(
                r"for\s+([A-Z][a-zA-Z\s]+?)\s+in", prompt, re.IGNORECASE
            )
        if char_match:
            context["character"] = char_match.group(1).strip()
        else:
            context["character"] = "the adventurer"

        # Extract setting
        setting_match = re.search(r"Setting[:\s]+([^,\n.]+)", prompt, re.IGNORECASE)
        if setting_match:
            context["setting"] = setting_match.group(1).strip()
        else:
            context["setting"] = "a mysterious realm"

        # Extract user input for continuation
        input_match = re.search(r"User Input[:\s]*([^,\n.]+)", prompt, re.IGNORECASE)
        if input_match:
            context["user_input"] = input_match.group(1).strip()
        else:
            context["user_input"] = "moved forward cautiously"

        return context

    def _fill_template(self, template: dict, context: dict[str, str]) -> dict:
        """Fill template with extracted context."""

        def replace_placeholders(obj):
            if isinstance(obj, str):
                result = obj
                for key, value in context.items():
                    result = result.replace(f"{{{key}}}", value)
                return result
            if isinstance(obj, dict):
                return {k: replace_placeholders(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [replace_placeholders(item) for item in obj]
            return obj

        return replace_placeholders(template)


class FakeLLMClient:
    """Fake LLM client that behaves like google.genai.Client."""

    def __init__(self, api_key: str = "fake-api-key"):
        self.api_key = api_key
        self.models = FakeModelsManager()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class FakeModelsManager:
    """Fake models manager for token counting and model access."""

    def __init__(self):
        self._models = {
            "gemini-3-pro-preview": FakeModelAdapter("gemini-3-pro-preview"),
            "gemini-1.5-flash": FakeModelAdapter("gemini-1.5-flash"),
            "gemini-1.5-pro": FakeModelAdapter("gemini-1.5-pro"),
        }
        self._default_model = FakeModelAdapter("gemini-3-pro-preview")

    def get(self, model_name: str) -> FakeModelAdapter:
        """Get a fake model adapter."""
        return self._models.get(model_name, FakeModelAdapter(model_name))

    def generate_content(self, prompts, generation_config=None) -> FakeLLMResponse:
        """Generate content using the default model (for backward compatibility)."""
        return self._default_model.generate_content(prompts, generation_config)

    def count_tokens(self, model: str, contents: list[str]) -> "FakeTokenCount":
        """Return fake token count."""
        # Estimate tokens based on content length
        total_chars = sum(len(content) for content in contents)
        estimated_tokens = max(100, total_chars // 4)  # Rough estimate
        return FakeTokenCount(estimated_tokens)


class FakeTokenCount:
    """Fake token count response."""

    def __init__(self, count: int = 1000):
        self.total_tokens = count
        self.input_tokens = count // 3
        self.output_tokens = count - self.input_tokens


class FakeGenerativeModel:
    """Fake GenerativeModel for backward compatibility."""

    def __init__(self, model_name: str = "gemini-3-pro-preview"):
        self.model_name = model_name
        self._adapter = FakeModelAdapter(model_name)

    def generate_content(self, prompt, generation_config=None):
        """Generate content using the adapter."""
        return self._adapter.generate_content(prompt, generation_config)

    def count_tokens(self, contents):
        """Count tokens in contents."""
        if isinstance(contents, str):
            contents = [contents]
        total_chars = sum(len(content) for content in contents)
        estimated_tokens = max(100, total_chars // 4)
        return FakeTokenCount(estimated_tokens)


# Convenience functions for test setup
def create_fake_llm_client(api_key: str = "fake-api-key") -> FakeLLMClient:
    """Create a fake LLM client for testing."""
    return FakeLLMClient(api_key)


def create_fake_model(model_name: str = "gemini-3-pro-preview") -> FakeGenerativeModel:
    """Create a fake GenerativeModel for testing."""
    return FakeGenerativeModel(model_name)
