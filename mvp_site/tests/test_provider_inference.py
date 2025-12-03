"""Test automatic provider inference from model selection.

This test validates that when users update their model via settings (without
explicitly setting the provider), the system correctly infers the provider
from the model name.

Addresses the issue where frontend only sends gemini_model without llm_provider,
causing the server to use the wrong provider.
"""

import os
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mvp_site.constants import (
    DEFAULT_LLM_PROVIDER,
    LLM_PROVIDER_CEREBRAS,
    LLM_PROVIDER_GEMINI,
    LLM_PROVIDER_OPENROUTER,
    infer_provider_from_model,
)


class TestProviderInference(unittest.TestCase):
    """Test automatic provider inference from model names."""

    def test_infer_gemini_provider_from_default_model(self):
        """Infer gemini provider from default Gemini model."""
        model = "gemini-2.0-flash"
        provider = infer_provider_from_model(model)
        self.assertEqual(provider, LLM_PROVIDER_GEMINI)

    def test_infer_gemini_provider_from_premium_model(self):
        """Infer gemini provider from premium Gemini model."""
        model = "gemini-3-pro-preview"
        provider = infer_provider_from_model(model)
        self.assertEqual(provider, LLM_PROVIDER_GEMINI)

    def test_infer_openrouter_provider_from_llama_model(self):
        """Infer openrouter provider from Llama model."""
        model = "meta-llama/llama-3.1-70b-instruct"
        provider = infer_provider_from_model(model)
        self.assertEqual(provider, LLM_PROVIDER_OPENROUTER)

    def test_infer_openrouter_provider_from_grok_model(self):
        """Infer openrouter provider from Grok model."""
        model = "x-ai/grok-4.1-fast:free"
        provider = infer_provider_from_model(model)
        self.assertEqual(provider, LLM_PROVIDER_OPENROUTER)

    def test_infer_cerebras_provider_from_qwen_model(self):
        """Infer cerebras provider from Qwen model."""
        model = "qwen-3-235b-a22b-instruct-2507"
        provider = infer_provider_from_model(model)
        self.assertEqual(provider, LLM_PROVIDER_CEREBRAS)

    def test_infer_cerebras_provider_from_llama_model(self):
        """Infer cerebras provider from Cerebras Llama model."""
        model = "llama-3.3-70b"
        provider = infer_provider_from_model(model)
        self.assertEqual(provider, LLM_PROVIDER_CEREBRAS)

    def test_infer_default_provider_for_unknown_model(self):
        """Default to DEFAULT_LLM_PROVIDER for unknown model."""
        model = "unknown-model-xyz"
        provider = infer_provider_from_model(model)
        self.assertEqual(provider, DEFAULT_LLM_PROVIDER)

    def test_infer_gemini_from_legacy_mapping(self):
        """Infer gemini provider from legacy model names in mapping."""
        # Legacy models that redirect to gemini-2.0-flash
        legacy_models = ["gemini-2.5-flash", "gemini-2.5-pro", "pro-2.5", "flash-2.5"]
        for model in legacy_models:
            with self.subTest(model=model):
                provider = infer_provider_from_model(model)
                self.assertEqual(
                    provider,
                    LLM_PROVIDER_GEMINI,
                    f"Legacy model {model} should infer gemini provider",
                )


if __name__ == "__main__":
    unittest.main()
