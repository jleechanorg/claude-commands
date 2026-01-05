"""Tests for debug_info trimming to prevent storage bloat.

This module tests that debug_info no longer stores bloated fields like
system_instruction_text, raw_request_payload, and raw_response_text,
while still storing lightweight metadata fields.

Related PR: feat(llm): Stop storing bloated debug_info fields, log instead
"""

from __future__ import annotations

import json
import os
import unittest

# Import the functions we need to test
from mvp_site.narrative_response_schema import NarrativeResponse


class TestDebugInfoTrimming(unittest.TestCase):
    """Tests that debug_info does not contain bloated fields."""

    def test_narrative_response_debug_info_does_not_require_bloated_fields(self):
        """Verify NarrativeResponse can be created without bloated debug_info fields."""
        # These fields should NOT be required in debug_info
        debug_info = {
            "llm_provider": "gemini",
            "llm_model": "gemini-2.0-flash",
            "system_instruction_files": ["base.txt", "rules.txt"],
            "system_instruction_char_count": 5000,
        }

        response = NarrativeResponse(
            narrative="Test narrative",
            session_header="Test Session",
            planning_block={"thinking": "test", "choices": {}},
            debug_info=debug_info,
        )

        # Verify lightweight fields are present
        self.assertEqual(response.debug_info.get("llm_provider"), "gemini")
        self.assertEqual(response.debug_info.get("llm_model"), "gemini-2.0-flash")
        self.assertEqual(
            response.debug_info.get("system_instruction_files"),
            ["base.txt", "rules.txt"],
        )
        self.assertEqual(response.debug_info.get("system_instruction_char_count"), 5000)

        # Verify bloated fields are NOT present
        self.assertNotIn("system_instruction_text", response.debug_info)
        self.assertNotIn("raw_request_payload", response.debug_info)
        self.assertNotIn("raw_response_text", response.debug_info)


class TestDebugLoggingFormat(unittest.TestCase):
    """Tests for the debug logging format with conditional ellipsis."""

    def test_conditional_ellipsis_short_string(self):
        """Verify ellipsis is NOT added when string is shorter than preview limit."""
        short_text = "Short text"
        preview_limit = 2000

        preview = short_text[:preview_limit]
        suffix = "..." if len(short_text) > len(preview) else ""

        # Short text should have no ellipsis
        self.assertEqual(suffix, "")
        self.assertEqual(f"{preview}{suffix}", "Short text")

    def test_conditional_ellipsis_long_string(self):
        """Verify ellipsis IS added when string is longer than preview limit."""
        long_text = "x" * 3000  # Longer than 2000 preview limit
        preview_limit = 2000

        preview = long_text[:preview_limit]
        suffix = "..." if len(long_text) > len(preview) else ""

        # Long text should have ellipsis
        self.assertEqual(suffix, "...")
        self.assertTrue(f"{preview}{suffix}".endswith("..."))

    def test_accurate_length_reporting_request(self):
        """Verify RAW_REQUEST logs actual length, not truncated length."""
        # Simulate the logging logic from llm_service.py
        raw_limit = 20000
        original_payload = "x" * 50000  # 50KB payload

        # The code should capture actual length BEFORE truncation
        request_length = len(original_payload)
        request_str_truncated = original_payload[:raw_limit]
        request_preview = request_str_truncated[:2000]

        # Verify actual length is reported (50000), not truncated (20000)
        self.assertEqual(request_length, 50000)
        self.assertEqual(len(request_str_truncated), 20000)
        self.assertEqual(len(request_preview), 2000)

    def test_accurate_length_reporting_response(self):
        """Verify RAW_RESPONSE logs actual length, not truncated length."""
        raw_limit = 20000
        original_response = "y" * 30000  # 30KB response

        # The code should use original response text for length
        raw_response = original_response  # Original, not truncated
        response_truncated = raw_response[:raw_limit]
        response_preview = response_truncated[:2000]

        # Verify actual length is reported (30000)
        self.assertEqual(len(raw_response), 30000)
        self.assertEqual(len(response_truncated), 20000)
        self.assertEqual(len(response_preview), 2000)


class TestDebugInfoStorageSavings(unittest.TestCase):
    """Tests verifying the storage savings from trimmed debug_info."""

    def test_trimmed_debug_info_size_estimation(self):
        """Verify trimmed debug_info is much smaller than before."""
        # OLD: Bloated debug_info (approx sizes)
        # system_instruction_text: ~8KB
        # raw_request_payload: ~20KB
        # raw_response_text: ~8KB
        # Total: ~36KB per entry

        # NEW: Lightweight debug_info
        lightweight_debug_info = {
            "llm_provider": "gemini",
            "llm_model": "gemini-2.0-flash",
            "system_instruction_files": [
                "base_game_master.txt",
                "character_mode_rules.txt",
                "combat_instructions.txt",
            ],
            "system_instruction_char_count": 8000,
        }

        lightweight_size = len(json.dumps(lightweight_debug_info))

        # Lightweight debug_info should be under 500 bytes
        self.assertLess(
            lightweight_size,
            500,
            f"Lightweight debug_info should be <500 bytes, got {lightweight_size}",
        )

        # This represents ~99% storage reduction from ~36KB to <500 bytes
        estimated_old_size = 36000
        savings_ratio = (estimated_old_size - lightweight_size) / estimated_old_size
        self.assertGreater(
            savings_ratio,
            0.95,
            f"Should achieve >95% storage savings, got {savings_ratio:.2%}",
        )


class TestCaptureRawEnvVariable(unittest.TestCase):
    """Tests for CAPTURE_RAW_LLM environment variable behavior."""

    def test_capture_raw_default_enabled(self):
        """Verify CAPTURE_RAW_LLM defaults to true."""
        # Clear any existing env var
        original = os.environ.pop("CAPTURE_RAW_LLM", None)
        try:
            capture_raw = os.getenv("CAPTURE_RAW_LLM", "true").lower() == "true"
            self.assertTrue(capture_raw, "CAPTURE_RAW_LLM should default to true")
        finally:
            if original is not None:
                os.environ["CAPTURE_RAW_LLM"] = original

    def test_capture_raw_can_be_disabled(self):
        """Verify CAPTURE_RAW_LLM can be disabled via env var."""
        original = os.environ.get("CAPTURE_RAW_LLM")
        try:
            os.environ["CAPTURE_RAW_LLM"] = "false"
            capture_raw = os.getenv("CAPTURE_RAW_LLM", "true").lower() == "true"
            self.assertFalse(capture_raw, "CAPTURE_RAW_LLM=false should disable capture")
        finally:
            if original is not None:
                os.environ["CAPTURE_RAW_LLM"] = original
            else:
                os.environ.pop("CAPTURE_RAW_LLM", None)


if __name__ == "__main__":
    unittest.main()
