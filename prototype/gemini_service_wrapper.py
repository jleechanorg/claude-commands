"""
Gemini service wrapper for validation prototype.
Provides a simplified interface to Gemini API with error handling.
"""

import os
import time
from typing import Any

# Try to import Gemini
try:
    import google.generativeai as genai

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai not installed. Using mock service.")


class GeminiServiceWrapper:
    """Wrapper for Gemini API with validation-specific features."""

    def __init__(self, api_key: str = None, model_name: str = "gemini-pro"):
        self.api_key = api_key
        self.model_name = model_name
        self.model = None
        self._request_count = 0
        self._total_tokens = 0

        if GEMINI_AVAILABLE and api_key:
            self._initialize_model()

    def _initialize_model(self):
        """Initialize Gemini model."""
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            print(f"Gemini model '{self.model_name}' initialized successfully")
        except Exception as e:
            print(f"Failed to initialize Gemini model: {e}")
            self.model = None

    def generate_content(self, prompt: str, **kwargs) -> Any:
        """Generate content using Gemini API."""
        if not self.model:
            raise RuntimeError("Gemini model not initialized")

        self._request_count += 1

        # Add safety settings if not provided
        if "safety_settings" not in kwargs:
            kwargs["safety_settings"] = [
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE",
                }
            ]

        # Generate content
        response = self.model.generate_content(prompt, **kwargs)

        # Track token usage if available
        if hasattr(response, "usage_metadata"):
            self._total_tokens += response.usage_metadata.total_tokens

        return response

    def get_metrics(self) -> dict[str, Any]:
        """Get usage metrics."""
        return {
            "request_count": self._request_count,
            "total_tokens": self._total_tokens,
            "model_name": self.model_name,
            "available": self.model is not None,
        }

    @classmethod
    def from_file(cls, api_key_path: str, **kwargs):
        """Create service from API key file."""
        if os.path.exists(api_key_path):
            with open(api_key_path) as f:
                api_key = f.read().strip()
            return cls(api_key=api_key, **kwargs)
        print(f"API key file not found: {api_key_path}")
        return cls(api_key=None, **kwargs)


class MockGeminiService:
    """Mock Gemini service for testing without API."""

    def __init__(self):
        self._request_count = 0

    def generate_content(self, prompt: str, **kwargs):
        """Generate mock response."""
        self._request_count += 1

        # Simulate API delay
        time.sleep(0.1)

        # Create mock response
        class MockResponse:
            def __init__(self, text):
                self.text = text

        # Generate contextual mock response based on prompt
        if "Gideon" in prompt and "Rowan" in prompt:
            if "knight" in prompt.lower() and "healer" in prompt.lower():
                response_text = """{
                    "entities_found": ["Gideon", "Rowan"],
                    "entities_missing": [],
                    "entity_states": {},
                    "confidence": 0.95,
                    "analysis": "Both characters are clearly referenced - 'knight' refers to Gideon and 'healer' to Rowan"
                }"""
            elif "alone" in prompt.lower() or "missing" in prompt.lower():
                response_text = """{
                    "entities_found": ["Gideon"],
                    "entities_missing": ["Rowan"],
                    "confidence": 0.85,
                    "analysis": "Only Gideon is present in the narrative"
                }"""
            else:
                response_text = """{
                    "entities_found": [],
                    "entities_missing": ["Gideon", "Rowan"],
                    "confidence": 0.7,
                    "analysis": "No clear references to the expected characters"
                }"""
        else:
            response_text = """{
                "entities_found": [],
                "entities_missing": [],
                "confidence": 0.5,
                "analysis": "Unable to determine entity presence"
            }"""

        return MockResponse(response_text)

    def get_metrics(self):
        """Get mock metrics."""
        return {
            "request_count": self._request_count,
            "total_tokens": 0,
            "model_name": "mock",
            "available": True,
        }


def get_gemini_service(api_key_path: str | None = None) -> Any:
    """Get Gemini service (real or mock based on availability)."""
    if api_key_path and os.path.exists(api_key_path) and GEMINI_AVAILABLE:
        return GeminiServiceWrapper.from_file(api_key_path)
    return MockGeminiService()
