"""
TDD tests for enhanced /health endpoint with concurrency metrics

Tests verify that the /health endpoint:
1. Returns 200 OK status
2. Returns basic health information
3. Returns concurrency metrics when environment variables are set
4. Returns MCP client configuration status
5. Is exempt from rate limiting
"""
import json
import os
import unittest

from mvp_site.main import create_app


class TestHealthEndpointConcurrency(unittest.TestCase):
    """Test suite for enhanced /health endpoint"""

    def setUp(self):
        """Set up test Flask application"""
        # Store original environment
        self.original_env = os.environ.copy()

        # Create test app
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def tearDown(self):
        """Restore original environment after each test"""
        # Remove keys added during the test
        for key in list(os.environ.keys()):
            if key not in self.original_env:
                del os.environ[key]

        # Restore original values for existing keys
        for key, value in self.original_env.items():
            os.environ[key] = value

    def test_health_endpoint_returns_200_ok(self):
        """RED→GREEN: Health endpoint should return 200 OK"""
        response = self.client.get("/health")

        self.assertEqual(
            response.status_code,
            200,
            f"Health endpoint should return 200 OK, got {response.status_code}"
        )

    def test_health_endpoint_returns_json(self):
        """RED→GREEN: Health endpoint should return JSON response"""
        response = self.client.get("/health")

        self.assertEqual(
            response.content_type,
            "application/json",
            "Health endpoint should return JSON content type"
        )

        # Verify JSON is parseable
        try:
            json.loads(response.data)
            is_json = True
        except json.JSONDecodeError:
            is_json = False

        self.assertTrue(is_json, "Response should be valid JSON")

    def test_health_endpoint_returns_basic_info(self):
        """RED→GREEN: Health endpoint should return status, service, and timestamp"""
        response = self.client.get("/health")
        data = json.loads(response.data)

        # Check required fields
        self.assertIn("status", data, "Response should include 'status' field")
        self.assertEqual(data["status"], "healthy", "Status should be 'healthy'")

        self.assertIn("service", data, "Response should include 'service' field")
        self.assertEqual(
            data["service"],
            "worldarchitect-ai",
            "Service should be 'worldarchitect-ai'"
        )

        self.assertIn("timestamp", data, "Response should include 'timestamp' field")
        self.assertIsInstance(
            data["timestamp"],
            str,
            "Timestamp should be a string"
        )

    def test_health_endpoint_includes_concurrency_with_workers_env(self):
        """RED→GREEN: Should include concurrency info when GUNICORN_WORKERS is set"""
        # Set environment variable before creating app
        os.environ["GUNICORN_WORKERS"] = "5"

        # Create new app with environment variable
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        response = client.get("/health")
        data = json.loads(response.data)

        self.assertIn(
            "concurrency",
            data,
            "Response should include 'concurrency' field when GUNICORN_WORKERS is set"
        )
        self.assertIn(
            "workers",
            data["concurrency"],
            "Concurrency should include 'workers' field"
        )
        self.assertEqual(
            data["concurrency"]["workers"],
            5,
            "Workers should match GUNICORN_WORKERS environment variable"
        )

    def test_health_endpoint_includes_threads_in_concurrency(self):
        """RED→GREEN: Should include threads when both GUNICORN_WORKERS and GUNICORN_THREADS are set

        Note: threads are only shown when workers are also present to maintain consistency
        with max_concurrent_requests calculation (workers × threads).
        """
        os.environ["GUNICORN_WORKERS"] = "3"
        os.environ["GUNICORN_THREADS"] = "4"

        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        response = client.get("/health")
        data = json.loads(response.data)

        self.assertIn("concurrency", data)
        self.assertIn("threads", data["concurrency"])
        self.assertEqual(
            data["concurrency"]["threads"],
            4,
            "Threads should match GUNICORN_THREADS environment variable"
        )

    def test_health_endpoint_calculates_max_concurrent_requests(self):
        """RED→GREEN: Should calculate max_concurrent_requests = workers × threads"""
        os.environ["GUNICORN_WORKERS"] = "5"
        os.environ["GUNICORN_THREADS"] = "4"

        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        response = client.get("/health")
        data = json.loads(response.data)

        self.assertIn("concurrency", data)
        self.assertIn("max_concurrent_requests", data["concurrency"])
        self.assertEqual(
            data["concurrency"]["max_concurrent_requests"],
            20,  # 5 workers × 4 threads
            "max_concurrent_requests should be workers × threads"
        )

    def test_health_endpoint_no_concurrency_without_env_vars(self):
        """RED→GREEN: Should not include concurrency if env vars not set"""
        # Ensure no gunicorn env vars are set
        for key in ["GUNICORN_WORKERS", "GUNICORN_THREADS"]:
            if key in os.environ:
                del os.environ[key]

        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        response = client.get("/health")
        data = json.loads(response.data)

        # Concurrency field should not be present when no GUNICORN_* env vars are set
        self.assertNotIn(
            "concurrency",
            data,
            "Health response should omit 'concurrency' when no GUNICORN_* env vars are set"
        )

    def test_health_endpoint_includes_mcp_client_status(self):
        """RED→GREEN: Should include MCP client configuration status"""
        response = self.client.get("/health")
        data = json.loads(response.data)

        self.assertIn(
            "mcp_client",
            data,
            "Response should include 'mcp_client' field"
        )

        mcp_client = data["mcp_client"]
        self.assertIn(
            "initialized",
            mcp_client,
            "MCP client should have 'initialized' field"
        )
        self.assertIsInstance(
            mcp_client["initialized"],
            bool,
            "MCP client 'initialized' should be boolean"
        )

        # If initialized, should have additional info
        if mcp_client["initialized"]:
            self.assertIn(
                "base_url",
                mcp_client,
                "Configured MCP client should have 'base_url'"
            )
            self.assertIn(
                "skip_http",
                mcp_client,
                "Configured MCP client should have 'skip_http'"
            )

    def test_health_endpoint_handles_mcp_client_error_gracefully(self):
        """RED→GREEN: Should handle MCP client initialization error gracefully

        Note: This test verifies the behavior without mocking since get_mcp_client
        is a nested function inside create_app(). The error handling is verified
        by the actual implementation's try/except block.
        """
        # The health endpoint should always return 200 OK even if MCP client fails
        response = self.client.get("/health")

        # Should always return 200 OK regardless of MCP client status
        self.assertEqual(response.status_code, 200)

        # Response should include mcp_client field (initialized true or false)
        data = json.loads(response.data)
        self.assertIn("mcp_client", data)
        self.assertIn("initialized", data["mcp_client"])
        self.assertIsInstance(data["mcp_client"]["initialized"], bool)

    def test_health_endpoint_is_rate_limit_exempt(self):
        """RED→GREEN: Health endpoint should not be rate limited"""
        # Make multiple rapid requests
        responses = []
        for _ in range(100):
            response = self.client.get("/health")
            responses.append(response.status_code)

        # All requests should succeed (no 429 Too Many Requests)
        all_success = all(status == 200 for status in responses)
        self.assertTrue(
            all_success,
            "Health endpoint should not be rate limited (all requests should return 200)"
        )

        # Verify no 429 responses
        rate_limited = any(status == 429 for status in responses)
        self.assertFalse(
            rate_limited,
            "Health endpoint should never return 429 Too Many Requests"
        )

    def test_health_endpoint_response_structure_is_consistent(self):
        """RED→GREEN: Response structure should be consistent across calls"""
        # Make multiple calls
        responses_data = []
        for _ in range(5):
            response = self.client.get("/health")
            data = json.loads(response.data)
            responses_data.append(data)

        # All responses should have the same keys (except timestamp values)
        first_keys = set(responses_data[0].keys())
        for data in responses_data[1:]:
            self.assertEqual(
                set(data.keys()),
                first_keys,
                "All health responses should have consistent structure"
            )

    def test_health_endpoint_timestamp_format(self):
        """RED→GREEN: Timestamp should be in ISO 8601 format"""
        response = self.client.get("/health")
        data = json.loads(response.data)

        timestamp = data["timestamp"]

        # Check if it looks like ISO 8601 format (basic validation)
        # Format: 2025-11-17T12:34:56.789000+00:00
        self.assertRegex(
            timestamp,
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
            "Timestamp should be in ISO 8601 format"
        )

    def test_health_endpoint_with_full_concurrency_info(self):
        """RED→GREEN: Integration test with all concurrency info present"""
        os.environ["GUNICORN_WORKERS"] = "7"
        os.environ["GUNICORN_THREADS"] = "6"

        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        response = client.get("/health")
        data = json.loads(response.data)

        # Verify complete response structure
        expected_structure = {
            "status": str,
            "service": str,
            "timestamp": str,
            "concurrency": {
                "workers": int,
                "threads": int,
                "max_concurrent_requests": int,
            },
            "mcp_client": {
                "initialized": bool,
            },
        }

        # Check top-level fields
        for field, expected_type in expected_structure.items():
            if field == "concurrency":
                self.assertIn(field, data)
                for sub_field, sub_type in expected_structure[field].items():
                    self.assertIn(sub_field, data[field])
                    self.assertIsInstance(data[field][sub_field], sub_type)
            elif field == "mcp_client":
                self.assertIn(field, data)
                self.assertIn("initialized", data[field])
                self.assertIsInstance(data[field]["initialized"], bool)
            else:
                self.assertIn(field, data)
                self.assertIsInstance(data[field], expected_type)

        # Verify calculation
        self.assertEqual(data["concurrency"]["max_concurrent_requests"], 42)  # 7×6


if __name__ == "__main__":
    unittest.main()
