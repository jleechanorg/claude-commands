#!/usr/bin/env python3
"""
Tests for timeout command
"""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add commands directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from timeout import TIMEOUT_MODES, TimeoutOptimizer


class TestTimeoutCommand(unittest.TestCase):
    """Test timeout command functionality"""

    def setUp(self):
        """Set up test environment"""
        # Create temporary directory for config
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "timeout_config.json"

    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_mode_constants(self):
        """Test that all required modes are defined"""
        required_modes = ["standard", "strict", "emergency"]
        for mode in required_modes:
            self.assertIn(mode, TIMEOUT_MODES)

        # Check required fields in each mode
        required_fields = [
            "name",
            "icon",
            "thinking_limit",
            "response_format",
            "context_lines",
            "tool_batching",
            "multiedit_threshold",
            "max_file_lines",
            "explanation_level",
        ]

        for mode, config in TIMEOUT_MODES.items():
            for field in required_fields:
                self.assertIn(field, config, f"Mode {mode} missing field {field}")

    def test_set_mode_standard(self):
        """Test setting standard mode"""
        optimizer = TimeoutOptimizer()
        optimizer.config_file = self.config_file

        result = optimizer.set_mode("standard")

        self.assertIn("STANDARD", result)
        self.assertIn("🚀", result)
        self.assertIn("Think-limit 5", result)

    def test_set_mode_strict(self):
        """Test setting strict mode"""
        optimizer = TimeoutOptimizer()
        optimizer.config_file = self.config_file

        result = optimizer.set_mode("strict")

        self.assertIn("STRICT", result)
        self.assertIn("⚡", result)
        self.assertIn("Think-limit 3", result)

    def test_set_mode_emergency(self):
        """Test setting emergency mode"""
        optimizer = TimeoutOptimizer()
        optimizer.config_file = self.config_file

        result = optimizer.set_mode("emergency")

        self.assertIn("EMERGENCY", result)
        self.assertIn("🚨", result)
        self.assertIn("Think-limit 2", result)
        self.assertIn("Crisis-mode", result)

    def test_set_mode_off(self):
        """Test disabling timeout mode"""
        optimizer = TimeoutOptimizer()
        optimizer.config_file = self.config_file

        result = optimizer.set_mode("off")

        self.assertEqual(result, "Timeout optimizations disabled")

    def test_invalid_mode(self):
        """Test invalid mode handling"""
        optimizer = TimeoutOptimizer()
        optimizer.config_file = self.config_file

        result = optimizer.set_mode("invalid")

        self.assertIn("Invalid mode", result)
        self.assertIn("standard, strict, emergency, off", result)

    def test_behavior_prompt_generation(self):
        """Test behavior prompt generation for each mode"""
        optimizer = TimeoutOptimizer()

        # Test each mode generates appropriate prompts
        for mode in TIMEOUT_MODES.keys():
            optimizer.current_mode = mode
            prompt = optimizer.generate_behavior_prompt()

            self.assertIn("TIMEOUT OPTIMIZATION MODE", prompt)
            self.assertIn("MANDATORY BEHAVIOR MODIFICATIONS", prompt)
            self.assertIn("TIMEOUT PREVENTION IS CRITICAL", prompt)

            # Check mode-specific content
            config = TIMEOUT_MODES[mode]
            self.assertIn(f"Thinking limit: {config['thinking_limit']}", prompt)
            self.assertIn(f"Read max {config['max_file_lines']}", prompt)

    def test_mode_progression(self):
        """Test that modes have appropriate progression of restrictions"""
        standard = TIMEOUT_MODES["standard"]
        strict = TIMEOUT_MODES["strict"]
        emergency = TIMEOUT_MODES["emergency"]

        # Thinking limits should decrease
        self.assertGreater(standard["thinking_limit"], strict["thinking_limit"])
        self.assertGreater(strict["thinking_limit"], emergency["thinking_limit"])

        # File line limits should decrease
        self.assertGreater(standard["max_file_lines"], strict["max_file_lines"])
        self.assertGreater(strict["max_file_lines"], emergency["max_file_lines"])

        # Context lines should decrease
        self.assertGreaterEqual(standard["context_lines"], strict["context_lines"])
        self.assertGreaterEqual(strict["context_lines"], emergency["context_lines"])


if __name__ == "__main__":
    unittest.main()
