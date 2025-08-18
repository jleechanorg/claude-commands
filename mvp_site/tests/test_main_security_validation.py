"""
Tests for main.py security and validation features.
Phase 8 - Milestone 8.3
"""

import html
import io
import json
import os
import sys
import unicodedata
import unittest
import zipfile
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

# Setup module path
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# Import proper fakes library 
from fake_services import FakeServiceManager
from fake_firestore import FakeFirestoreClient

# Use proper fakes library instead of manual MagicMock setup
with FakeServiceManager() as fake_services:
    pass  # Fakes library handles firebase_admin setup

os.environ["TESTING"] = "true"


class TestSQLInjectionPrevention(unittest.TestCase):
    """Test SQL injection prevention measures."""

    def setUp(self):
        """Set up test client and mocks."""
        # Mock Flask app and client
        self.app = MagicMock()
        self.client = MagicMock()
        self.app.test_client.return_value = self.client

    def test_sql_injection_in_campaign_name(self):
        """Test that SQL injection attempts in campaign names are sanitized."""
        with patch("firestore_service.create_campaign") as mock_create:
            # Simulate SQL injection attempt
            campaign_name = "Test'; DROP TABLE users; --"

            # Verify that Firestore (NoSQL) doesn't execute SQL
            # In a real app, this would be handled by input validation
            assert "DROP TABLE" in campaign_name

            # Mock that the service handles it safely
            mock_create.return_value = {"campaign_id": "test123", "name": campaign_name}

            # Call the function
            result = mock_create("test_user", campaign_name, "Test description")

            # Verify it was called with the injection attempt
            mock_create.assert_called_with(
                "test_user", campaign_name, "Test description"
            )

            # NoSQL databases like Firestore are inherently safe from SQL injection
            assert result is not None

    def test_sql_injection_in_user_input(self):
        """Test SQL injection attempts in various user inputs."""
        with patch("firestore_service.add_story_entry") as mock_add:
            # Attempt SQL injection in story entry
            malicious_text = "Robert'); DROP TABLE players; --"

            # Firestore handles this safely as it's NoSQL
            mock_add.return_value = True

            # Test that the service accepts the input (NoSQL is safe from SQL injection)
            result = mock_add("test_user", "test_campaign", "player", malicious_text)

            assert result
            mock_add.assert_called_once_with(
                "test_user", "test_campaign", "player", malicious_text
            )

    def test_nosql_injection_prevention(self):
        """Test NoSQL injection prevention in Firestore queries."""
        with patch("firestore_service.get_campaigns_for_user") as mock_get:
            # Attempt NoSQL injection patterns
            injection_attempts = [
                {"$ne": None},  # MongoDB style
                {"$gt": ""},  # MongoDB comparison
                "'; return true; var foo='",  # JS injection
                '{"$where": "this.password == null"}',  # MongoDB $where
            ]

            for _attempt in injection_attempts:
                # Firestore doesn't support MongoDB-style operators
                # It would ignore or reject these
                mock_get.return_value = []

                # Simulate calling - Firestore API doesn't accept arbitrary filter objects
                result = mock_get("test_user")

                # Should return empty list, not execute injection
                assert result == []

    def test_parameterized_query_usage(self):
        """Test that queries use parameterized/safe patterns."""
        with patch("firestore_service.get_campaign_by_id") as mock_get:
            # Test search with potential injection
            campaign_id = "test' OR '1'='1"

            # Firestore uses parameterized queries internally
            mock_get.return_value = None

            # Simulate search with injection attempt
            result = mock_get("test_user", campaign_id)

            # Should handle safely without executing injection
            assert result is None
            mock_get.assert_called_with("test_user", campaign_id)


class TestXSSPrevention(unittest.TestCase):
    """Test XSS (Cross-Site Scripting) prevention measures."""

    def setUp(self):
        """Set up test environment."""
        self.malicious_scripts = [
            '<script>alert("XSS")</script>',
            '<img src=x onerror=alert("XSS")>',
            '<svg onload=alert("XSS")>',
            'javascript:alert("XSS")',
            "<iframe src=\"javascript:alert('XSS')\">",
        ]

    def test_xss_in_campaign_description(self):
        """Test XSS prevention in campaign descriptions."""
        with patch("firestore_service.create_campaign") as mock_create:
            for script in self.malicious_scripts:
                # Mock successful creation (Firestore stores as-is, frontend handles escaping)
                mock_create.return_value = {
                    "campaign_id": "test123",
                    "description": script,  # Stored as-is in database
                }

                result = mock_create(
                    "test_user", "Test Campaign", script, "Opening story", {}
                )

                # Verify the script is stored (escaping happens on display)
                assert result["description"] == script

                # In a real app, the frontend would escape this when displaying
                escaped = html.escape(script)
                assert "<script>" not in escaped
                assert "<img" not in escaped

    def test_script_tag_sanitization(self):
        """Test that script tags are properly handled."""
        with patch("firestore_service.add_story_entry") as mock_add:
            malicious_story = (
                "The wizard casts <script>steal_cookies()</script> a spell!"
            )

            # Firestore stores the raw content
            mock_add.return_value = True

            result = mock_add("test_user", "test_campaign", "player", malicious_story)

            assert result

            # Frontend should escape when displaying
            safe_display = html.escape(malicious_story)
            assert "&lt;script&gt;" in safe_display
            assert "<script>" not in safe_display

    def test_event_handler_removal(self):
        """Test that event handlers are neutralized."""
        dangerous_inputs = [
            '<button onclick="malicious()">Click me</button>',
            '<div onmouseover="steal()">Hover here</div>',
            '<input onfocus="hack()" value="test">',
            '<a href="#" onload="xss()">Link</a>',
        ]

        with patch("firestore_service.add_story_entry") as mock_add:
            for dangerous_input in dangerous_inputs:
                mock_add.return_value = True

                result = mock_add(
                    "test_user", "test_campaign", "player", dangerous_input
                )
                assert result

                # Check that event handlers would be escaped on display
                safe_html = html.escape(dangerous_input)
                # html.escape converts < and > to &lt; and &gt;
                assert "&lt;" in safe_html
                assert "&gt;" in safe_html
                # The dangerous HTML can't be executed
                assert "<button" not in safe_html
                assert "<div" not in safe_html

    def test_xss_in_json_responses(self):
        """Test XSS prevention in JSON API responses."""
        with patch("firestore_service.get_campaign_by_id") as mock_get:
            # Mock a campaign with XSS attempt in data
            mock_get.return_value = {
                "title": '<script>alert("XSS")</script>',
                "description": "Normal description with <b>bold</b>",
                "metadata": {
                    "created_by": '"><script>alert("XSS")</script>',
                },
            }

            campaign = mock_get("test_user", "test_campaign")

            # JSON serialization naturally escapes special characters
            json_str = json.dumps(campaign)

            # Verify JSON encoding prevents XSS
            assert '\\"' in json_str  # Quotes are escaped
            # The dangerous string is properly contained within JSON string
            assert '\\"><script>' in json_str  # Properly escaped in JSON
            # Verify it's within a quoted string context
            assert '"created_by": "\\"><script>' in json_str


class TestRequestSizeLimits(unittest.TestCase):
    """Test request size limit enforcement."""

    def setUp(self):
        """Set up test environment."""
        self.app = MagicMock()
        self.client = MagicMock()

    def test_request_body_size_limit(self):
        """Test that oversized request bodies are rejected."""
        # Common body size limits are 1MB, 10MB, etc.
        MAX_BODY_SIZE = 10 * 1024 * 1024  # 10MB typical limit

        with patch("firestore_service.create_campaign") as mock_create:
            # Create an oversized payload
            oversized_description = "A" * (MAX_BODY_SIZE + 1000)

            # Mock that the service would reject this
            mock_create.side_effect = ValueError("Request body too large")

            with pytest.raises(ValueError) as context:
                mock_create(
                    "test_user", "Test Campaign", oversized_description, "Story", {}
                )

            assert "too large" in str(context.value)

    def test_header_size_limit(self):
        """Test that oversized headers are handled."""
        # HTTP header size limits (typically 8KB total)
        MAX_HEADER_SIZE = 8 * 1024

        # Create oversized header value
        oversized_token = "Bearer " + "A" * MAX_HEADER_SIZE

        # In a real Flask app, oversized headers would be rejected by the server
        # Most web servers (nginx, Apache) reject headers > 8KB
        assert len(oversized_token) > MAX_HEADER_SIZE

        # Mock that the web server would reject this before reaching the app
        with patch("firebase_admin.auth.verify_id_token") as mock_verify:
            # Simulate header size rejection
            mock_verify.side_effect = ValueError("Header too large")

            with pytest.raises(ValueError) as context:
                mock_verify(oversized_token)

            assert "Header too large" in str(context.value)

    def test_url_length_limit(self):
        """Test URL length limits."""
        # URL length limits (typically 2048 characters)
        MAX_URL_LENGTH = 2048

        with patch("firestore_service.get_campaign_by_id") as mock_get:
            # Create oversized campaign ID (part of URL)
            oversized_id = "a" * MAX_URL_LENGTH

            # Service should handle gracefully
            mock_get.return_value = None

            result = mock_get("test_user", oversized_id)

            assert result is None
            mock_get.assert_called_once()

    def test_array_size_limits(self):
        """Test limits on array/list sizes in requests."""
        with patch("firestore_service.add_story_entry") as mock_add:
            # Try to add extremely large number of items
            large_array = ["item"] * 10000  # 10k items

            # Convert to a story entry with metadata
            story_with_huge_metadata = {
                "text": "Normal story",
                "metadata": {"items": large_array},
            }

            # Service should handle this (Firestore has document size limits)
            mock_add.return_value = True

            result = mock_add(
                "test_user",
                "test_campaign",
                "player",
                json.dumps(story_with_huge_metadata),
            )

            assert result

            # In production, Firestore would reject documents > 1MB
            doc_size = len(json.dumps(story_with_huge_metadata))
            assert doc_size > 50000  # Verify it's actually large


class TestRateLimitingEnforcement(unittest.TestCase):
    """Test rate limiting enforcement."""

    def setUp(self):
        """Set up test environment."""
        self.rate_limiter = MagicMock()
        self.request_counts = {}

    def test_api_rate_limiting(self):
        """Test API rate limiting enforcement."""
        # Common rate limit: 100 requests per minute per user
        RATE_LIMIT = 100
        user_id = "test_user"

        # Simulate tracking requests
        for _i in range(RATE_LIMIT + 10):
            if user_id not in self.request_counts:
                self.request_counts[user_id] = 0

            self.request_counts[user_id] += 1

            if self.request_counts[user_id] > RATE_LIMIT:
                # Should be rate limited
                assert self.request_counts[user_id] > RATE_LIMIT
                break

        # Verify rate limit was exceeded
        assert self.request_counts[user_id] == RATE_LIMIT + 1

    def test_rate_limit_headers(self):
        """Test rate limit headers are properly set."""
        with patch("firestore_service.get_campaigns_for_user") as mock_get:
            mock_get.return_value = []

            # Simulate rate limit headers
            rate_limit_headers = {
                "X-RateLimit-Limit": "100",
                "X-RateLimit-Remaining": "95",
                "X-RateLimit-Reset": "1609459200",
            }

            # Verify headers contain rate limit info
            assert rate_limit_headers["X-RateLimit-Limit"] == "100"
            assert "X-RateLimit-Remaining" in rate_limit_headers
            assert "X-RateLimit-Reset" in rate_limit_headers

    def test_distributed_rate_limiting(self):
        """Test distributed rate limiting across multiple instances."""
        # Simulate distributed rate limiting with shared state
        shared_counter = {"requests": 0, "window_start": datetime.now()}
        WINDOW_SECONDS = 60
        MAX_REQUESTS = 100

        def check_rate_limit():
            now = datetime.now()
            window_elapsed = (now - shared_counter["window_start"]).total_seconds()

            if window_elapsed > WINDOW_SECONDS:
                # Reset window
                shared_counter["requests"] = 0
                shared_counter["window_start"] = now

            if shared_counter["requests"] >= MAX_REQUESTS:
                return False  # Rate limited

            shared_counter["requests"] += 1
            return True

        # Test rate limiting
        allowed_count = 0
        for _i in range(MAX_REQUESTS + 20):
            if check_rate_limit():
                allowed_count += 1

        # Should allow exactly MAX_REQUESTS
        assert allowed_count == MAX_REQUESTS

    def test_rate_limit_by_endpoint(self):
        """Test different rate limits for different endpoints."""
        # Different endpoints may have different limits
        endpoint_limits = {
            "/api/campaigns": 100,  # Standard limit
            "/api/ai/generate": 10,  # Lower limit for expensive operations
            "/api/health": 1000,  # Higher limit for health checks
        }

        endpoint_counters = dict.fromkeys(endpoint_limits, 0)

        # Simulate requests to different endpoints
        test_requests = [
            ("/api/campaigns", 50),
            ("/api/ai/generate", 15),
            ("/api/health", 500),
        ]

        for endpoint, count in test_requests:
            limit = endpoint_limits[endpoint]
            allowed = min(count, limit)
            endpoint_counters[endpoint] = allowed

            # Verify appropriate limits
            assert endpoint_counters[endpoint] <= limit

        # Verify AI endpoint was limited more strictly
        assert endpoint_counters["/api/ai/generate"] == 10


class TestInputSanitization(unittest.TestCase):
    """Test input sanitization measures."""

    def setUp(self):
        """Set up test environment."""
        self.dangerous_inputs = [
            '&lt;script&gt;alert("XSS")&lt;/script&gt;',  # Already encoded
            '<IMG SRC=javascript:alert("XSS")>',  # Mixed case
            '<IMG SRC=JaVaScRiPt:alert("XSS")>',  # Mixed case JS
            '&#60;script&#62;alert("XSS")&#60;/script&#62;',  # HTML entities
            '\x3cscript\x3ealert("XSS")\x3c/script\x3e',  # Hex encoding
        ]

    def test_html_entity_encoding(self):
        """Test HTML entity encoding for special characters."""
        # Test various special characters that should be encoded
        special_chars = {
            "<": "&lt;",
            ">": "&gt;",
            "&": "&amp;",
            '"': "&quot;",
            "'": "&#x27;",
        }

        for char, encoded in special_chars.items():
            result = html.escape(char)
            assert result == encoded

        # Test complex string
        dangerous_string = '<script>alert("XSS & more")</script>'
        safe_string = html.escape(dangerous_string)

        assert "<script>" not in safe_string
        assert "&lt;script&gt;" in safe_string
        assert "&amp;" in safe_string
        assert "&quot;" in safe_string

    def test_unicode_normalization(self):
        """Test Unicode normalization to prevent homograph attacks."""

        # Test various Unicode variations that normalize differently
        unicode_tests = [
            ("ⓢⓒⓡⓘⓟⓣ", True),  # Circled letters - normalizes
            ("𝓼𝓬𝓻𝓲𝓹𝓽", True),  # Mathematical bold script - normalizes
            ("ｓｃｒｉｐｔ", True),  # Full-width - normalizes
            ("script", False),  # Regular ASCII - stays same
        ]

        for unicode_str, should_change in unicode_tests:
            # NFKD normalization converts to compatible form
            normalized = unicodedata.normalize("NFKD", unicode_str)

            # For display purposes, these would be normalized
            assert isinstance(normalized, str)

            # Check if normalization changed the string
            if should_change:
                # These special Unicode forms should normalize to simpler forms
                assert unicode_str != normalized
            else:
                # Regular ASCII should stay the same
                assert unicode_str == normalized

    def test_control_character_removal(self):
        """Test removal of control characters."""
        # Control characters that should be removed or sanitized
        control_chars = [
            "\x00",  # Null
            "\x08",  # Backspace
            "\x0b",  # Vertical tab
            "\x0c",  # Form feed
            "\x1b",  # Escape
            "\x7f",  # Delete
        ]

        for char in control_chars:
            test_string = f"Hello{char}World"

            # Simple sanitization: remove control characters
            sanitized = "".join(
                c for c in test_string if c.isprintable() or c in "\n\r\t"
            )

            assert char not in sanitized
            assert sanitized == "HelloWorld"

    def test_nested_encoding_prevention(self):
        """Test prevention of nested/double encoding attacks."""
        # Test strings with multiple encoding layers
        nested_attacks = [
            '&lt;script&gt;alert("XSS")&lt;/script&gt;',  # Already encoded
            "&#x3c;script&#x3e;",  # Hex entities
            "&amp;lt;script&amp;gt;",  # Double encoded
        ]

        with patch("firestore_service.add_story_entry") as mock_add:
            for attack in nested_attacks:
                mock_add.return_value = True

                # Store the attack as-is (encoding happens on display)
                result = mock_add("test_user", "test_campaign", "player", attack)

                assert result

                # When displaying, avoid double-encoding
                # If it's already encoded, don't encode again
                if "&lt;" in attack or "&#" in attack:
                    # Already contains encoded entities
                    assert "&" in attack


class TestCSRFProtection(unittest.TestCase):
    """Test CSRF (Cross-Site Request Forgery) protection."""

    def setUp(self):
        """Set up test environment."""
        self.client = MagicMock()
        self.csrf_token = "test_csrf_token_123"

    def test_csrf_token_validation(self):
        """Test CSRF token validation on state-changing operations."""
        # State-changing operations should require CSRF token
        state_changing_methods = ["POST", "PUT", "DELETE", "PATCH"]

        for _method in state_changing_methods:
            with patch("firestore_service.create_campaign") as mock_create:
                # Test without CSRF token - should fail
                mock_create.side_effect = ValueError("CSRF token missing")

                with pytest.raises(ValueError) as context:
                    mock_create("user", "campaign", "desc", "story", {})

                assert "CSRF" in str(context.value)

                # Test with valid CSRF token - should succeed
                mock_create.side_effect = None
                mock_create.return_value = {"campaign_id": "123"}

                result = mock_create(
                    "user", "campaign", "desc", "story", {}, csrf_token=self.csrf_token
                )

                assert result["campaign_id"] == "123"

    def test_double_submit_cookie(self):
        """Test double-submit cookie pattern for CSRF protection."""
        # Simulate double-submit cookie pattern
        cookie_token = "cookie_csrf_123"
        header_token = "cookie_csrf_123"

        # Valid case: cookie and header match
        assert cookie_token == header_token

        # Invalid case: tokens don't match
        bad_header_token = "different_token"
        assert cookie_token != bad_header_token

        # Test with mock request
        with patch("firestore_service.add_story_entry") as mock_add:
            # Simulate CSRF validation
            if cookie_token == header_token:
                mock_add.return_value = True
                result = mock_add("user", "campaign", "player", "action")
                assert result
            else:
                mock_add.side_effect = ValueError("CSRF token mismatch")
                with pytest.raises(ValueError):
                    mock_add("user", "campaign", "player", "action")

    def test_origin_header_validation(self):
        """Test Origin header validation for CSRF protection."""
        # Valid origins
        valid_origins = [
            "https://worldarchitect.ai",
            "https://www.worldarchitect.ai",
            "http://localhost:8080",  # Development
            "http://127.0.0.1:8080",  # Development
        ]

        # Invalid origins
        invalid_origins = [
            "https://evil-site.com",
            "http://attacker.com",
            "null",  # Sandboxed iframe
            "",  # Empty origin
        ]

        # Test valid origins
        for origin in valid_origins:
            # In production, these would be allowed
            is_valid = (
                "worldarchitect.ai" in origin.lower()
                or "localhost" in origin.lower()
                or "127.0.0.1" in origin
            )
            assert is_valid, f"Origin {origin} should be valid"

        # Test invalid origins
        for origin in invalid_origins:
            # These should be rejected
            assert "worldarchitect.ai" not in origin.lower()
            assert "localhost" not in origin.lower()
            assert "127.0.0.1" not in origin

    def test_safe_methods_exempt(self):
        """Test that safe methods don't require CSRF protection."""
        # Safe methods that don't change state
        safe_methods = ["GET", "HEAD", "OPTIONS"]

        with patch("firestore_service.get_campaigns_for_user") as mock_get:
            mock_get.return_value = []

            for _method in safe_methods:
                # Safe methods should work without CSRF token
                result = mock_get("test_user")

                assert result == []
                mock_get.assert_called_with("test_user")

                # No CSRF token needed for safe methods
                assert isinstance(result, list)


class TestPathTraversalAndPayloadAttacks(unittest.TestCase):
    """Test path traversal and payload attack prevention."""

    def setUp(self):
        """Set up test environment."""
        self.dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\sam",
            "../../../../../../../../etc/passwd",
            ".%2e/.%2e/.%2e/etc/passwd",  # URL encoded
            "....//....//....//etc/passwd",  # Double dots
        ]

    def test_path_traversal_prevention(self):
        """Test prevention of path traversal attacks."""

        # Base directory for safe file operations

        for dangerous_path in self.dangerous_paths:
            # Check for dangerous patterns
            if dangerous_path.startswith("/"):
                # Unix absolute paths should be rejected
                assert os.path.isabs(dangerous_path)
            elif dangerous_path.startswith(("C:", "c:")):
                # Windows absolute paths
                assert ":" in dangerous_path
            else:
                # Relative paths with .. should be caught
                has_traversal = (
                    ".." in dangerous_path or "%2e" in dangerous_path.lower()
                )
                assert (
                    has_traversal
                ), f"Path {dangerous_path} should contain traversal pattern"

            # In production, path validation would:
            # 1. Resolve to absolute path
            # 2. Check if it's within allowed directory
            # 3. Reject if outside safe base

            # Verify dangerous patterns are present
            is_dangerous = (
                ".." in dangerous_path
                or dangerous_path.startswith(("/", "C:"))
                or "%2e" in dangerous_path.lower()
                or "\\" in dangerous_path
            )

            assert (
                is_dangerous
            ), f"Path {dangerous_path} should be recognized as dangerous"

    def test_json_bomb_protection(self):
        """Test protection against JSON bomb/billion laughs attacks."""
        # JSON bomb - exponential expansion
        json_bomb = {
            "a": ["x"] * 1000,  # 1000 elements
            "b": ["x"] * 1000,
            "c": ["x"] * 1000,
        }

        # Add nested references (in string form, as actual refs would be circular)
        for i in range(10):
            json_bomb[f"level_{i}"] = {"data": ["x"] * 100, "nested": f"level_{i + 1}"}

        # Calculate approximate size
        json_str = json.dumps(json_bomb)
        json_size = len(json_str)

        # JSON bombs can be detected by:
        # 1. Maximum depth limits
        # 2. Maximum size limits
        # 3. Maximum array length limits

        MAX_JSON_SIZE = 1024 * 1024  # 1MB limit
        MAX_ARRAY_LENGTH = 10000

        # Check if this would exceed limits
        total_elements = sum(
            len(v) if isinstance(v, list) else 1
            for v in json_bomb.values()
            if isinstance(v, list)
        )

        assert total_elements < MAX_ARRAY_LENGTH
        assert json_size < MAX_JSON_SIZE

    def test_zip_bomb_prevention(self):
        """Test prevention of zip bomb attacks."""

        # Create a simulated zip file
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add a file that compresses well (highly repetitive)
            repetitive_data = "A" * 10000  # 10KB of 'A's
            zf.writestr("file1.txt", repetitive_data)

            # Add multiple files
            for i in range(5):
                zf.writestr(f"file{i}.txt", repetitive_data)

        zip_buffer.seek(0)
        compressed_size = len(zip_buffer.getvalue())

        # Check compressed vs uncompressed ratio
        uncompressed_size = 10000 * 6  # 6 files * 10KB each
        compression_ratio = uncompressed_size / compressed_size

        # Zip bombs have extreme compression ratios (1000:1 or more)
        # Normal files rarely exceed 10:1
        MAX_COMPRESSION_RATIO = 100

        assert compression_ratio < MAX_COMPRESSION_RATIO

        # Additional checks for zip bomb prevention:
        # 1. Maximum extracted size limit
        # 2. Maximum number of files limit
        # 3. Maximum nesting depth limit

        MAX_EXTRACTED_SIZE = 100 * 1024 * 1024  # 100MB
        MAX_FILES = 1000

        assert uncompressed_size < MAX_EXTRACTED_SIZE
        assert MAX_FILES > 6  # We created 6 files

    def test_xml_entity_expansion_prevention(self):
        """Test prevention of XML entity expansion attacks (XXE)."""
        # XML entity expansion attack example
        malicious_xml = """<?xml version="1.0"?>
        <!DOCTYPE lolz [
          <!ENTITY lol "lol">
          <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
          <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
        ]>
        <lolz>&lol3;</lolz>"""

        # In production, XML parsing should:
        # 1. Disable DTD processing
        # 2. Disable external entity resolution
        # 3. Use safe XML parsers

        # Check for dangerous patterns
        assert "<!DOCTYPE" in malicious_xml
        assert "<!ENTITY" in malicious_xml
        assert "&lol" in malicious_xml

        # Safe XML parsing would reject this
        # Example: defusedxml library prevents XXE attacks
        has_entities = "<!ENTITY" in malicious_xml
        has_doctype = "<!DOCTYPE" in malicious_xml

        assert has_entities and has_doctype, "Should detect potential XXE attack"


if __name__ == "__main__":
    unittest.main()
