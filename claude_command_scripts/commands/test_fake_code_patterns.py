#!/usr/bin/env python3
"""
test_fake_code_patterns.py - Tests for various fake code patterns
This file contains examples of fake/simulated code that should be detected
"""

import datetime
import logging
import os
import subprocess
import traceback
import unittest
from unittest.mock import Mock, patch


class FakeCodeExamples:
    """Examples of fake code patterns that should be detected"""

    def fake_ai_response_generator(self, user_input: str) -> str:
        """FAKE: Hardcoded responses masquerading as AI"""
        user_input_lower = user_input.lower()

        if "error" in user_input_lower or "bug" in user_input_lower:
            return "Thank you for identifying this issue! We'll look into it."
        if "suggestion" in user_input_lower:
            return "Excellent suggestion! We appreciate your feedback."
        if "help" in user_input_lower:
            return "I'm here to help! What do you need assistance with?"
        return "I understand. Let me process that for you."

    def fake_sentiment_analyzer(self, text: str) -> dict:
        """FAKE: Keyword-based sentiment pretending to be ML"""
        positive_words = ["good", "great", "excellent", "love", "amazing"]
        negative_words = ["bad", "terrible", "hate", "awful", "horrible"]

        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            return {"sentiment": "positive", "confidence": 0.95}
        if negative_count > positive_count:
            return {"sentiment": "negative", "confidence": 0.92}
        return {"sentiment": "neutral", "confidence": 0.88}

    def fake_data_processor(self, data: list) -> list:
        """FAKE: Returns mock data instead of processing"""
        # Simulates processing but just returns hardcoded results
        return [
            {"id": 1, "status": "processed", "result": "success"},
            {"id": 2, "status": "processed", "result": "success"},
            {"id": 3, "status": "processed", "result": "success"},
        ]

    def fake_api_client(self, endpoint: str, params: dict) -> dict:
        """FAKE: Mock API responses without real network calls"""
        mock_responses = {
            "/users": {"users": [{"id": 1, "name": "Test User"}]},
            "/products": {
                "products": [{"id": 1, "name": "Test Product", "price": 99.99}]
            },
            "/orders": {"orders": [{"id": 1, "status": "completed", "total": 199.99}]},
        }

        return mock_responses.get(endpoint, {"error": "Not found"})

    def fake_complexity_analyzer(self, code: str) -> str:
        """FAKE: Trivial logic claiming to analyze complexity"""
        line_count = len(code.split("\n"))

        if line_count < 10:
            return "Low complexity"
        if line_count < 50:
            return "Medium complexity"
        return "High complexity"


class RealCodeExamples:
    """Examples of real code that should NOT be flagged as fake"""

    def real_input_validator(self, user_input: str) -> tuple[bool, str]:
        """REAL: Actual validation logic with specific rules"""
        if not user_input:
            return False, "Input cannot be empty"

        if len(user_input) < 3:
            return False, "Input must be at least 3 characters"

        if len(user_input) > 100:
            return False, "Input cannot exceed 100 characters"

        # Check for SQL injection patterns
        dangerous_patterns = ["DROP TABLE", "DELETE FROM", "; --", "UNION SELECT"]
        for pattern in dangerous_patterns:
            if pattern in user_input.upper():
                return False, "Invalid input: contains dangerous pattern"

        return True, "Valid input"

    def real_data_transformer(self, data: dict) -> dict:
        """REAL: Actual data transformation with business logic"""
        transformed = {}

        # Apply actual transformations
        for key, value in data.items():
            if isinstance(value, str):
                transformed[key] = value.strip().lower()
            elif isinstance(value, int | float):
                transformed[key] = round(value * 1.1, 2)  # Apply 10% increase
            elif isinstance(value, list):
                transformed[key] = [
                    self.real_data_transformer(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                transformed[key] = value

        # Add metadata
        transformed["_processed_at"] = datetime.datetime.now().isoformat()
        transformed["_version"] = "1.0"

        return transformed

    def real_error_handler(self, exception: Exception) -> dict:
        """REAL: Proper error handling with logging and context"""
        error_context = {
            "error_type": type(exception).__name__,
            "error_message": str(exception),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.datetime.now().isoformat(),
        }

        # Log the error
        logging.error(f"Error occurred: {error_context['error_type']}", exc_info=True)

        # Return sanitized error for client
        if isinstance(exception, ValueError):
            return {"error": "Invalid input provided", "code": "VALIDATION_ERROR"}
        if isinstance(exception, KeyError):
            return {"error": "Required data missing", "code": "MISSING_DATA"}
        return {"error": "An unexpected error occurred", "code": "INTERNAL_ERROR"}


class TestFakeCodeDetection(unittest.TestCase):
    """Unit tests to verify fake code patterns are detectable"""

    def test_fake_patterns_exist(self):
        """Verify that our fake examples contain detectable patterns"""
        fake = FakeCodeExamples()

        # Test hardcoded response generator
        response1 = fake.fake_ai_response_generator("I found an error in the code")
        response2 = fake.fake_ai_response_generator("I have a suggestion")
        assert response1 == "Thank you for identifying this issue! We'll look into it."
        assert response2 == "Excellent suggestion! We appreciate your feedback."

        # Test keyword-based sentiment
        sentiment1 = fake.fake_sentiment_analyzer("This is great!")
        sentiment2 = fake.fake_sentiment_analyzer("This is terrible!")
        assert sentiment1["sentiment"] == "positive"
        assert sentiment2["sentiment"] == "negative"

        # Test mock data processor
        result = fake.fake_data_processor([1, 2, 3, 4, 5])
        assert len(result) == 3  # Always returns 3 items
        assert all(item["status"] == "processed" for item in result)

    def test_real_patterns_work(self):
        """Verify that real code examples function properly"""
        real = RealCodeExamples()

        # Test real validation
        valid, msg = real.real_input_validator("valid input")
        assert valid

        invalid, msg = real.real_input_validator("DROP TABLE users")
        assert not invalid
        assert "dangerous pattern" in msg

        # Test real transformation
        data = {"name": "  TEST  ", "value": 100, "items": [{"x": 1}]}
        result = real.real_data_transformer(data)
        assert result["name"] == "test"
        assert result["value"] == 110.0
        assert "_processed_at" in result

    def test_pattern_characteristics(self):
        """Test specific characteristics that identify fake code"""
        fake = FakeCodeExamples()

        # Characteristic 1: Limited input variations produce predictable outputs
        inputs = ["error here", "ERROR!", "An error occurred", "erRoR"]
        outputs = [fake.fake_ai_response_generator(inp) for inp in inputs]
        # All should produce the same output despite different inputs
        assert len(set(outputs)) == 1

        # Characteristic 2: High confidence scores without actual analysis
        sentiments = [
            fake.fake_sentiment_analyzer("neutral text"),
            fake.fake_sentiment_analyzer("mixed feelings"),
        ]
        # Fake code often has unrealistically high confidence
        for s in sentiments:
            assert s["confidence"] > 0.85


class TestMockPatterns(unittest.TestCase):
    """Test patterns that use mocking (which might be legitimate in tests)"""

    @patch("requests.get")
    def test_legitimate_mock_usage(self, mock_get):
        """LEGITIMATE: Using mocks in test code is acceptable"""
        mock_get.return_value.json.return_value = {"status": "ok"}

        # This is legitimate mock usage in a test
        response = mock_get("http://api.example.com/status")
        assert response.json()["status"] == "ok"

    def test_mock_vs_fake_code(self):
        """Distinguish between legitimate mocks and fake implementations"""
        # Legitimate: Mock for testing
        mock_service = Mock()
        mock_service.process.return_value = "processed"

        # Fake: Hardcoded implementation in production code
        def fake_service_process(data):
            # This would be fake if used in production
            return "processed"

        assert mock_service.process("data") == "processed"
        assert fake_service_process("data") == "processed"


class TestDataFabricationHook(unittest.TestCase):
    """Test the fake detection hook's data fabrication patterns (August 2025 enhancement)"""

    def setUp(self):
        """Set up hook path for testing"""
        # Find project root by looking for CLAUDE.md
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = current_dir
        while project_root != "/" and not os.path.exists(os.path.join(project_root, "CLAUDE.md")):
            project_root = os.path.dirname(project_root)
        
        self.project_root = project_root
        self.hook_path = os.path.join(project_root, ".claude/hooks/detect_speculation_and_fake_code.sh")
        self.assertTrue(os.path.exists(self.hook_path), f"Hook not found at {self.hook_path}")
        
        # Clean up any existing warning files
        self.warning_file = os.path.join(project_root, "docs/CRITICAL_FAKE_CODE_WARNING.md")
        if os.path.exists(self.warning_file):
            os.remove(self.warning_file)

    def tearDown(self):
        """Clean up after each test"""
        if os.path.exists(self.warning_file):
            os.remove(self.warning_file)

    def _run_hook(self, test_text: str) -> tuple[int, str, str]:
        """Run the hook with test text and return (exit_code, stdout, stderr)"""
        try:
            # Combine stderr and stdout to get full output
            result = subprocess.run(
                [self.hook_path],
                input=test_text,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Combine stderr into stdout
                timeout=10
            )
            # Return combined output as stderr for easier testing
            return result.returncode, "", result.stdout
        except subprocess.TimeoutExpired:
            self.fail("Hook execution timed out")
        except Exception as e:
            self.fail(f"Failed to run hook: {e}")

    def test_data_fabrication_detection_tilde_patterns(self):
        """Test detection of tilde (~) estimation patterns"""
        # Should detect: ~N lines patterns
        test_cases = [
            "The React component has ~45 lines of code",
            "This function is ~30 lines long",
            "Approximately ~100 lines in the file",
        ]
        
        for test_text in test_cases:
            with self.subTest(text=test_text):
                exit_code, stdout, stderr = self._run_hook(test_text)
                self.assertEqual(exit_code, 2, f"Should detect pattern in: {test_text}")
                self.assertIn("FAKE CODE DETECTED", stderr)
                self.assertIn("Estimated line count", stderr)

    def test_data_fabrication_detection_approximation_patterns(self):
        """Test detection of approximation language patterns"""
        test_cases = [
            "The system has approximately 60 lines",
            "This contains roughly 200 lines of code", 
            "Around 150 lines were generated",
            "The file has estimated 75 lines total",
        ]
        
        for test_text in test_cases:
            with self.subTest(text=test_text):
                exit_code, stdout, stderr = self._run_hook(test_text)
                self.assertEqual(exit_code, 2, f"Should detect pattern in: {test_text}")
                self.assertIn("FAKE CODE DETECTED", stderr)
                # Should match one of: Numeric approximation, Rough numeric estimate, Line count estimation
                detected_patterns = ["Numeric approximation", "Rough numeric estimate", "Line count estimation"]
                self.assertTrue(any(pattern in stderr for pattern in detected_patterns))

    def test_data_fabrication_detection_table_patterns(self):
        """Test detection of table estimation markers"""
        test_cases = [
            "| React Component | 326ms | ~45 | 320 tokens |",
            "| API Handler | 250ms | ~30 | 180 tokens |",
            "| Data Processor | ~50 lines | 400 tokens |",
        ]
        
        for test_text in test_cases:
            with self.subTest(text=test_text):
                exit_code, stdout, stderr = self._run_hook(test_text)
                self.assertEqual(exit_code, 2, f"Should detect table pattern in: {test_text}")
                self.assertIn("FAKE CODE DETECTED", stderr)
                self.assertIn("Table estimation marker", stderr)

    def test_original_benchmark_error_pattern(self):
        """Test that the exact pattern from the original benchmark error is caught"""
        # This is the exact pattern that caused the 8x fabrication error
        benchmark_row = "| React Product Card | 326 | 8000-12000 | 25-37x faster | 42 | ~45 | 292 | ~320 |"
        
        exit_code, stdout, stderr = self._run_hook(benchmark_row)
        self.assertEqual(exit_code, 2, "Should catch original benchmark error pattern")
        self.assertIn("FAKE CODE DETECTED", stderr)
        self.assertIn("Table estimation marker", stderr)

    def test_no_false_positives_real_measurements(self):
        """Test that real measurement language doesn't trigger false positives"""
        legitimate_cases = [
            "Based on wc -l output: file.txt contains 366 lines",
            "Measured with wc -l: 1,234 lines total",
            "Git diff shows 15 lines changed",
            "Line count from actual measurement: 456 lines",
            "The file is 200 lines (measured)",
            "Verified line count: 89 lines",
        ]
        
        for test_text in legitimate_cases:
            with self.subTest(text=test_text):
                exit_code, stdout, stderr = self._run_hook(test_text)
                self.assertEqual(exit_code, 0, f"Should NOT detect pattern in legitimate: {test_text}")
                self.assertIn("No fake code detected", stderr)

    def test_multiple_patterns_in_single_text(self):
        """Test detection when multiple fabrication patterns exist in one text"""
        multi_pattern_text = "The React component has ~45 lines of code and approximately 60 lines in the API."
        
        exit_code, stdout, stderr = self._run_hook(multi_pattern_text)
        self.assertEqual(exit_code, 2, "Should detect multiple patterns")
        self.assertIn("FAKE CODE DETECTED", stderr)
        # Should detect both patterns
        self.assertIn("Estimated line count", stderr)
        self.assertIn("Numeric approximation", stderr)

    def test_hook_error_handling(self):
        """Test hook handles edge cases gracefully"""
        edge_cases = [
            "",  # Empty input
            "Normal text with no patterns",  # No patterns
            "The file has 100 lines exactly",  # Exact numbers (no estimation markers)
        ]
        
        for test_text in edge_cases:
            with self.subTest(text=test_text):
                exit_code, stdout, stderr = self._run_hook(test_text)
                self.assertEqual(exit_code, 0, f"Should pass through: '{test_text}'")
                if test_text:  # Non-empty should show "no fake code detected"
                    self.assertIn("No fake code detected", stderr)

    def test_pattern_case_insensitivity(self):
        """Test that patterns work regardless of case"""
        case_variants = [
            "The file has APPROXIMATELY 50 lines",
            "This contains Roughly 100 Lines",
            "Around 25 LINES were added",
        ]
        
        for test_text in case_variants:
            with self.subTest(text=test_text):
                exit_code, stdout, stderr = self._run_hook(test_text)
                self.assertEqual(exit_code, 2, f"Should detect case-insensitive pattern: {test_text}")
                self.assertIn("FAKE CODE DETECTED", stderr)


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)

    print("\n" + "=" * 60)
    print("ANALYSIS NOTES FOR CODE AUTHENTICITY DETECTION:")
    print("=" * 60)
    print("""
    This file contains examples of FAKE CODE patterns that should be detected:

    1. fake_ai_response_generator: Hardcoded responses based on keywords
    2. fake_sentiment_analyzer: Simple keyword counting pretending to be ML
    3. fake_data_processor: Returns mock data instead of processing
    4. fake_api_client: Hardcoded responses without network calls
    5. fake_complexity_analyzer: Trivial line counting as "analysis"

    PLUS NEW DATA FABRICATION PATTERNS (August 2025 enhancement):
    6. Estimation markers: ~45 lines, approximately 60, roughly 200
    7. Table estimation: | Component | ~45 | (markdown table estimates)
    8. Approximation language: around X lines, estimated Y lines

    Key indicators of fake code:
    - Keyword matching with hardcoded responses
    - Unrealistic confidence scores
    - Mock data in production code
    - Overly simplistic logic claiming sophistication
    - Generic responses that don't reflect actual processing
    - DATA FABRICATION: Estimation markers instead of measurements

    The REAL code examples show proper implementation with:
    - Actual validation logic
    - Real data transformation
    - Proper error handling
    - Genuine processing based on input
    - REAL DATA: Measured values with measurement commands (wc -l, etc.)

    Hook tests validate:
    - Detection of all 6 new data fabrication patterns
    - Zero false positives on real measurement language
    - Prevention of original benchmark error (8x fabrication)
    - Case-insensitive pattern matching
    - Multiple pattern detection in single text
    """)
