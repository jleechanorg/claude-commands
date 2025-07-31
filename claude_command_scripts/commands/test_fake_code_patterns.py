#!/usr/bin/env python3
"""
test_fake_code_patterns.py - Tests for various fake code patterns
This file contains examples of fake/simulated code that should be detected
"""

import datetime
import logging
import traceback
import unittest
from unittest.mock import Mock, patch


class FakeCodeExamples:
    """Examples of fake code patterns that should be detected"""

    def fake_ai_response_generator(self, user_input: str) -> str:
        """FAKE: Hardcoded responses masquerading as AI"""
        user_input_lower = user_input.lower()

        if 'error' in user_input_lower or 'bug' in user_input_lower:
            return "Thank you for identifying this issue! We'll look into it."
        if 'suggestion' in user_input_lower:
            return "Excellent suggestion! We appreciate your feedback."
        if 'help' in user_input_lower:
            return "I'm here to help! What do you need assistance with?"
        return "I understand. Let me process that for you."

    def fake_sentiment_analyzer(self, text: str) -> dict:
        """FAKE: Keyword-based sentiment pretending to be ML"""
        positive_words = ['good', 'great', 'excellent', 'love', 'amazing']
        negative_words = ['bad', 'terrible', 'hate', 'awful', 'horrible']

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
            {"id": 3, "status": "processed", "result": "success"}
        ]

    def fake_api_client(self, endpoint: str, params: dict) -> dict:
        """FAKE: Mock API responses without real network calls"""
        mock_responses = {
            "/users": {"users": [{"id": 1, "name": "Test User"}]},
            "/products": {"products": [{"id": 1, "name": "Test Product", "price": 99.99}]},
            "/orders": {"orders": [{"id": 1, "status": "completed", "total": 199.99}]}
        }

        return mock_responses.get(endpoint, {"error": "Not found"})

    def fake_complexity_analyzer(self, code: str) -> str:
        """FAKE: Trivial logic claiming to analyze complexity"""
        line_count = len(code.split('\n'))

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
        dangerous_patterns = ['DROP TABLE', 'DELETE FROM', '; --', 'UNION SELECT']
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
            elif isinstance(value, (int, float)):
                transformed[key] = round(value * 1.1, 2)  # Apply 10% increase
            elif isinstance(value, list):
                transformed[key] = [self.real_data_transformer(item)
                                  if isinstance(item, dict) else item
                                  for item in value]
            else:
                transformed[key] = value

        # Add metadata
        transformed['_processed_at'] = datetime.datetime.now().isoformat()
        transformed['_version'] = '1.0'

        return transformed

    def real_error_handler(self, exception: Exception) -> dict:
        """REAL: Proper error handling with logging and context"""
        error_context = {
            'error_type': type(exception).__name__,
            'error_message': str(exception),
            'traceback': traceback.format_exc(),
            'timestamp': datetime.datetime.now().isoformat()
        }

        # Log the error
        logging.error(f"Error occurred: {error_context['error_type']}",
                     exc_info=True)

        # Return sanitized error for client
        if isinstance(exception, ValueError):
            return {'error': 'Invalid input provided', 'code': 'VALIDATION_ERROR'}
        if isinstance(exception, KeyError):
            return {'error': 'Required data missing', 'code': 'MISSING_DATA'}
        return {'error': 'An unexpected error occurred', 'code': 'INTERNAL_ERROR'}


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
        assert sentiment1['sentiment'] == 'positive'
        assert sentiment2['sentiment'] == 'negative'

        # Test mock data processor
        result = fake.fake_data_processor([1, 2, 3, 4, 5])
        assert len(result) == 3  # Always returns 3 items
        assert all(item['status'] == 'processed' for item in result)

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
        assert result['name'] == 'test'
        assert result['value'] == 110.0
        assert '_processed_at' in result

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
            fake.fake_sentiment_analyzer("mixed feelings")
        ]
        # Fake code often has unrealistically high confidence
        for s in sentiments:
            assert s['confidence'] > 0.85


class TestMockPatterns(unittest.TestCase):
    """Test patterns that use mocking (which might be legitimate in tests)"""

    @patch('requests.get')
    def test_legitimate_mock_usage(self, mock_get):
        """LEGITIMATE: Using mocks in test code is acceptable"""
        mock_get.return_value.json.return_value = {"status": "ok"}

        # This is legitimate mock usage in a test
        response = mock_get('http://api.example.com/status')
        assert response.json()['status'] == 'ok'

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


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)

    print("\n" + "="*60)
    print("ANALYSIS NOTES FOR CODE AUTHENTICITY DETECTION:")
    print("="*60)
    print("""
    This file contains examples of FAKE CODE patterns that should be detected:

    1. fake_ai_response_generator: Hardcoded responses based on keywords
    2. fake_sentiment_analyzer: Simple keyword counting pretending to be ML
    3. fake_data_processor: Returns mock data instead of processing
    4. fake_api_client: Hardcoded responses without network calls
    5. fake_complexity_analyzer: Trivial line counting as "analysis"

    Key indicators of fake code:
    - Keyword matching with hardcoded responses
    - Unrealistic confidence scores
    - Mock data in production code
    - Overly simplistic logic claiming sophistication
    - Generic responses that don't reflect actual processing

    The REAL code examples show proper implementation with:
    - Actual validation logic
    - Real data transformation
    - Proper error handling
    - Genuine processing based on input
    """)
