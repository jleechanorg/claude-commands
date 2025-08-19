#!/usr/bin/env python3
"""
Proper TDD tests for Claude bot server response quality.
Tests that would have caught the branch-header-only bug.
"""

import os
import subprocess
import time
import unittest

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


@unittest.skipUnless(REQUESTS_AVAILABLE, "requests library not available")
class TestClaudeBotServer(unittest.TestCase):
    """Test Claude bot server responses and quality."""

    @classmethod
    def setUpClass(cls):
        """Start the Claude bot server for testing."""
        cls.server_process = None
        cls.base_url = "http://127.0.0.1:5001"
        cls.claude_endpoint = f"{cls.base_url}/claude"
        cls.health_endpoint = f"{cls.base_url}/health"

        # Start server
        cls._start_server()
        cls._wait_for_server()

    @classmethod
    def tearDownClass(cls):
        """Stop the Claude bot server."""
        if cls.server_process:
            cls.server_process.terminate()
            cls.server_process.wait()

    @classmethod
    def _start_server(cls):
        """Start the Claude bot server process."""
        server_script = os.path.join(
            os.path.dirname(__file__), "../server/claude-bot-server.py"
        )
        cls.server_process = subprocess.Popen(
            ["python3", server_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

    @classmethod
    def _wait_for_server(cls, max_retries=30):
        """Wait for server to be ready."""
        for _ in range(max_retries):
            try:
                response = requests.get(cls.health_endpoint, timeout=1)
                if response.status_code == 200:
                    return
            except requests.exceptions.RequestException:
                pass
            time.sleep(0.5)
        raise Exception("Server failed to start within timeout")

    def _send_prompt(self, prompt):
        """Send prompt to Claude bot server."""
        response = requests.post(
            self.claude_endpoint, data={"prompt": prompt}, timeout=30
        )
        assert response.status_code == 200
        return response.text.strip()

    def test_health_endpoint(self):
        """Test that health endpoint works."""
        response = requests.get(self.health_endpoint)
        assert response.status_code == 200
        assert "running" in response.text.lower()

    def test_hello_response_quality(self):
        """Test that hello prompts return proper responses or proper error handling."""
        test_cases = ["hello!", "hello", "hi", "hey"]

        for prompt in test_cases:
            with self.subTest(prompt=prompt):
                response = self._send_prompt(prompt)

                # Should not be empty
                assert len(response) > 0, f"Empty response for '{prompt}'"

                # Should not be ONLY metadata (branch headers)
                assert not (response.startswith("[Local:") and response.endswith("]")), f"Response is only metadata for '{prompt}': {response}"

                # In testing environment, expect proper error handling
                if os.getenv("TESTING") == "true":
                    # Should be a proper error message (not just hanging)
                    error_indicators = ["Error", "timed out", "not found", "failed"]
                    assert any(indicator in response for indicator in error_indicators), f"Expected error handling in test environment for '{prompt}': {response}"
                    # Should be reasonably informative
                    assert len(response) >= 20, f"Error message too short for '{prompt}': {response}"
                else:
                    # In production, expect greeting content
                    greeting_words = ["hello", "hi", "claude", "assist", "help"]
                    assert any(word in response.lower() for word in greeting_words), f"Response lacks greeting content for '{prompt}': {response}"
                    # Should be reasonably long
                    assert len(response) >= 20, f"Response too short for '{prompt}': {response}"

    def test_math_response_quality(self):
        """Test that math prompts return proper responses or error handling."""
        test_cases = [
            ("2+2", ["4", "four"]),
            ("what is 2+2?", ["4", "four"]),
            ("2 + 2", ["4", "four"]),
        ]

        for prompt, expected_content in test_cases:
            with self.subTest(prompt=prompt):
                response = self._send_prompt(prompt)

                # Should not be ONLY metadata
                assert not (response.startswith("[Local:") and response.endswith("]")), f"Response is only metadata for '{prompt}': {response}"

                # Environment-aware testing
                if os.getenv("TESTING") == "true":
                    # In testing, expect proper error handling
                    error_indicators = ["Error", "timed out", "not found", "failed"]
                    assert any(indicator in response for indicator in error_indicators), f"Expected error handling in test environment for '{prompt}': {response}"
                else:
                    # In production, expect mathematical content
                    assert any(content in response.lower() for content in expected_content), f"Response lacks math content for '{prompt}': {response}"

    def test_help_response_quality(self):
        """Test that help prompts return helpful information or proper error handling."""
        test_cases = ["help", "help me", "I need help"]

        for prompt in test_cases:
            with self.subTest(prompt=prompt):
                response = self._send_prompt(prompt)

                # Environment-aware testing
                if os.getenv("TESTING") == "true":
                    # In testing, expect proper error handling
                    error_indicators = ["Error", "timed out", "not found", "failed"]
                    assert any(indicator in response for indicator in error_indicators), f"Expected error handling in test environment for '{prompt}': {response}"
                    # Should be substantial error message
                    assert len(response) >= 20, f"Error message too short for '{prompt}': {response}"
                else:
                    # In production, expect help content
                    help_words = ["help", "assist", "question", "debug"]
                    assert any(word in response.lower() for word in help_words), f"Response lacks help content for '{prompt}': {response}"
                    # Should be substantial
                    assert len(response) >= 30, f"Help response too short for '{prompt}': {response}"

    def test_debug_response_quality(self):
        """Test that debug prompts return debugging assistance or proper error handling."""
        test_cases = ["debug", "help me debug", "debug this code"]

        for prompt in test_cases:
            with self.subTest(prompt=prompt):
                response = self._send_prompt(prompt)

                # Environment-aware testing
                if os.getenv("TESTING") == "true":
                    # In testing, expect proper error handling
                    error_indicators = ["Error", "timed out", "not found", "failed"]
                    assert any(indicator in response for indicator in error_indicators), f"Expected error handling in test environment for '{prompt}': {response}"
                else:
                    # In production, expect debug content
                    debug_words = ["debug", "code", "issue", "problem", "share"]
                    assert any(word in response.lower() for word in debug_words), f"Response lacks debug content for '{prompt}': {response}"

    def test_general_response_quality(self):
        """Test general prompt handling."""
        test_cases = ["explain something", "what can you do?", "random question"]

        for prompt in test_cases:
            with self.subTest(prompt=prompt):
                response = self._send_prompt(prompt)

                # Should not be empty
                assert len(response) > 0

                # Should not be ONLY metadata
                assert not (response.startswith("[Local:") and response.endswith("]")), f"Response is only metadata for '{prompt}': {response}"

                # Should be reasonably substantial
                assert len(response) >= 50, f"Response too short for '{prompt}': {response}"

                # Should mention the prompt or Claude
                assert prompt.lower() in response.lower() or "claude" in response.lower(), f"Response doesn't acknowledge prompt or identity: {response}"

    def test_empty_prompt_handling(self):
        """Test that empty prompts are rejected properly."""
        test_cases = ["", "   ", "null"]

        for prompt in test_cases:
            with self.subTest(prompt=prompt):
                response = requests.post(
                    self.claude_endpoint, data={"prompt": prompt}, timeout=10
                )

                # Should return 400 for empty prompts
                assert response.status_code == 400
                assert "Error" in response.text
                assert "empty" in response.text.lower()

    def test_response_not_just_branch_header(self):
        """Test that responses are never ONLY branch headers."""
        test_prompts = [
            "hello!",
            "help",
            "debug",
            "2+2",
            "test",
            "explain",
            "what",
            "how",
            "why",
        ]

        for prompt in test_prompts:
            with self.subTest(prompt=prompt):
                response = self._send_prompt(prompt)

                # Critical: Should NEVER be only a branch header
                branch_header_pattern = r"^\[Local:.*\]$"
                import re

                assert not re.match(branch_header_pattern, response.strip()), f"Response is ONLY branch header for '{prompt}': {response}"

                # Should provide SOME response (even if error in testing)
                assert len(response.strip()) > 0, f"Completely empty response for '{prompt}'"

    def test_response_consistency(self):
        """Test that same prompts return consistent responses."""
        prompt = "hello!"

        responses = []
        for _ in range(3):
            response = self._send_prompt(prompt)
            responses.append(response)
            time.sleep(0.1)

        # All responses should be similar (contain greeting)
        for response in responses:
            assert "claude" in response.lower()
            assert len(response) > 20


if __name__ == "__main__":
    unittest.main(verbosity=2)
