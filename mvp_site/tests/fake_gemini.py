"""
Fake Gemini AI service for testing.
Returns realistic responses instead of Mock objects to avoid JSON serialization issues.
"""

import json
import re


class FakeGeminiResponse:
    """Fake Gemini response that behaves like the real thing."""

    def __init__(self, text: str, usage_metadata: dict | None = None):
        self.text = text
        self.usage_metadata = usage_metadata or {
            "input_tokens": 100,
            "output_tokens": 200,
            "total_tokens": 300,
        }
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

    def __init__(self, model_name: str = "gemini-2.5-flash"):
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
            },
        }

    def generate_content(
        self, prompt: str, generation_config=None
    ) -> FakeGeminiResponse:
        """Generate a fake response based on prompt content."""

        # Extract context from prompt for more realistic responses
        context = self._extract_context(prompt)

        # Choose appropriate template
        if "create a campaign" in prompt.lower() or "new campaign" in prompt.lower():
            template = self._response_templates["campaign_creation"]
        else:
            template = self._response_templates["story_continuation"]

        # Fill template with context
        response_data = self._fill_template(template, context)

        # Convert to JSON string as Gemini would return
        response_text = json.dumps(response_data, indent=2)

        return FakeGeminiResponse(response_text)

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


class FakeGeminiClient:
    """Fake Gemini client that behaves like google.genai.Client."""

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
            "gemini-2.5-flash": FakeModelAdapter("gemini-2.5-flash"),
            "gemini-1.5-flash": FakeModelAdapter("gemini-1.5-flash"),
            "gemini-1.5-pro": FakeModelAdapter("gemini-1.5-pro"),
        }

    def get(self, model_name: str) -> FakeModelAdapter:
        """Get a fake model adapter."""
        return self._models.get(model_name, FakeModelAdapter(model_name))

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

    def __init__(self, model_name: str = "gemini-2.5-flash"):
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
def create_fake_gemini_client(api_key: str = "fake-api-key") -> FakeGeminiClient:
    """Create a fake Gemini client for testing."""
    return FakeGeminiClient(api_key)


def create_fake_model(model_name: str = "gemini-2.5-flash") -> FakeGenerativeModel:
    """Create a fake GenerativeModel for testing."""
    return FakeGenerativeModel(model_name)
