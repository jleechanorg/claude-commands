#!/usr/bin/env python3
"""
Gemini API client wrapper for real LLM testing
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Any

# Set up API key BEFORE importing SDK (following test_integration.py pattern)
if not os.environ.get("GEMINI_API_KEY"):
    # Check home directory first
    home_key_path = os.path.expanduser("~/.gemini_api_key.txt")
    if os.path.exists(home_key_path):
        with open(home_key_path) as key_file:
            os.environ["GEMINI_API_KEY"] = key_file.read().strip()
    else:
        # Check project root
        project_key_path = os.path.join(
            os.path.dirname(__file__), "../../../gemini_api_key.txt"
        )
        if os.path.exists(project_key_path):
            with open(project_key_path) as key_file:
                os.environ["GEMINI_API_KEY"] = key_file.read().strip()

try:
    from google import genai
    from google.genai import types
except ImportError:
    # Fallback for environments without the package
    genai = None
    print("WARNING: google-genai not installed. Using mock mode.")

from config import (
    COST_PER_1K_INPUT_TOKENS,
    COST_PER_1K_OUTPUT_TOKENS,
    MAX_BUDGET_USD,
    MAX_RETRIES,
    MAX_TOKENS,
    SAFETY_SETTINGS,
    TEMPERATURE,
    TEST_MODEL,
    WARNING_THRESHOLD_USD,
    get_api_key,
)

logger = logging.getLogger(__name__)


class CostTracker:
    """Track API costs and enforce budget limits"""

    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost_usd = 0.0
        self.call_count = 0
        self.start_time = datetime.now()

    def add_usage(self, input_tokens: int, output_tokens: int):
        """Add token usage from an API call"""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.call_count += 1

        # Calculate cost
        input_cost = (input_tokens / 1000) * COST_PER_1K_INPUT_TOKENS
        output_cost = (output_tokens / 1000) * COST_PER_1K_OUTPUT_TOKENS
        call_cost = input_cost + output_cost
        self.total_cost_usd += call_cost

        # Log usage
        logger.info(
            f"API Call #{self.call_count}: {input_tokens} in, {output_tokens} out, ${call_cost:.4f}"
        )

        # Check thresholds
        if self.total_cost_usd >= MAX_BUDGET_USD:
            raise Exception(
                f"BUDGET EXCEEDED: ${self.total_cost_usd:.2f} >= ${MAX_BUDGET_USD}"
            )
        if self.total_cost_usd >= WARNING_THRESHOLD_USD:
            logger.warning(
                f"BUDGET WARNING: ${self.total_cost_usd:.2f} of ${MAX_BUDGET_USD} used"
            )

    def get_summary(self) -> dict[str, Any]:
        """Get cost tracking summary"""
        duration = (datetime.now() - self.start_time).total_seconds()
        return {
            "total_calls": self.call_count,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "average_cost_per_call": round(
                self.total_cost_usd / max(1, self.call_count), 4
            ),
            "duration_seconds": round(duration, 1),
            "budget_used_percent": round(
                (self.total_cost_usd / MAX_BUDGET_USD) * 100, 1
            ),
        }


class GeminiClient:
    """Wrapper for Gemini API with retry logic and cost tracking"""

    def __init__(self, use_mock: bool = False):
        self.use_mock = use_mock or (genai is None)
        self.cost_tracker = CostTracker()
        self.model = None
        self.client = None

        if not self.use_mock:
            try:
                # Get API key - it should already be in environment from module init
                api_key = os.environ.get("GEMINI_API_KEY")
                if not api_key:
                    api_key = get_api_key()

                # Create client using pattern from test_integration.py
                self.client = genai.Client(api_key=api_key)
                self.model_name = TEST_MODEL
                logger.info(f"Initialized Gemini client with model: {TEST_MODEL}")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")
                self.use_mock = True

    def generate_narrative(
        self, prompt: str, system_instruction: str | None = None
    ) -> dict[str, Any]:
        """Generate narrative with the Gemini API"""
        if self.use_mock:
            return self._generate_mock_response(prompt)

        start_time = time.time()

        # Build full prompt
        full_prompt = prompt
        if system_instruction:
            full_prompt = f"{system_instruction}\n\n{prompt}"

        # Retry logic
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                # Generate content using the client
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        temperature=TEMPERATURE,
                        max_output_tokens=MAX_TOKENS,
                        safety_settings=SAFETY_SETTINGS,
                    ),
                )

                # Extract text from response
                response_text = (
                    response.text if hasattr(response, "text") else str(response)
                )

                # Extract token counts (approximate if not provided)
                input_tokens = len(full_prompt.split()) * 1.3  # Rough estimate
                output_tokens = len(response_text.split()) * 1.3

                # Track costs
                self.cost_tracker.add_usage(int(input_tokens), int(output_tokens))

                # Return structured response
                return {
                    "success": True,
                    "text": response_text,
                    "input_tokens": int(input_tokens),
                    "output_tokens": int(output_tokens),
                    "model": self.model_name,
                    "duration": time.time() - start_time,
                    "cost_usd": self.cost_tracker.total_cost_usd,
                }

            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2**attempt)  # Exponential backoff

        # All retries failed
        return {
            "success": False,
            "error": str(last_error),
            "text": "",
            "duration": time.time() - start_time,
        }

    def _generate_mock_response(self, prompt: str) -> dict[str, Any]:
        """Generate a mock response for testing without API"""
        # Simple mock that mentions some entities
        if "multi_character" in prompt:
            text = "Sariel, Lyra, and Marcus gathered in the tavern. The innkeeper served them ale."
        elif "combat" in prompt:
            text = "Sariel struck the orc with her sword. Marcus cast healing on Lyra."
        else:
            text = "The party continued their journey through the forest."

        return {
            "success": True,
            "text": text,
            "input_tokens": len(prompt.split()),
            "output_tokens": len(text.split()),
            "model": "mock",
            "duration": 0.1,
            "cost_usd": 0.0,
        }

    def parse_structured_response(
        self, response_text: str, format_type: str = "json"
    ) -> dict | None:
        """Parse structured response from LLM output"""
        if format_type == "json":
            # Try to find JSON block
            try:
                # Look for ```json blocks first
                if "```json" in response_text:
                    start = response_text.find("```json") + 7
                    end = response_text.find("```", start)
                    json_str = response_text[start:end].strip()
                else:
                    # Try to parse the whole response
                    json_str = response_text.strip()

                return json.loads(json_str)
            except:
                logger.warning("Failed to parse JSON response")
                return None

        elif format_type == "xml":
            # Simple XML parsing for entity lists
            entities = []
            if "<entities>" in response_text:
                start = response_text.find("<entities>") + 10
                end = response_text.find("</entities>")
                entity_block = response_text[start:end]

                # Extract entity tags
                import re

                pattern = r"<entity[^>]*>([^<]+)</entity>"
                matches = re.findall(pattern, entity_block)
                entities.extend(matches)

            return {"entities": entities} if entities else None

        return None

    def get_cost_summary(self) -> dict[str, Any]:
        """Get current cost tracking summary"""
        return self.cost_tracker.get_summary()


# Module-level client instance
_client = None


def get_client(use_mock: bool = False) -> GeminiClient:
    """Get or create the Gemini client instance"""
    global _client
    if _client is None:
        _client = GeminiClient(use_mock=use_mock)
    return _client
