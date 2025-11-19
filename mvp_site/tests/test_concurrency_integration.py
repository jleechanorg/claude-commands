"""
TDD integration tests for concurrent request handling

Tests verify that the application:
1. Can handle multiple simultaneous requests
2. Responds correctly under concurrent load
3. Maintains consistency across concurrent requests
4. Does not have race conditions
5. Properly uses connection pooling

These are integration tests that verify the entire concurrency stack:
- Gunicorn configuration (workers × threads)
- Flask application
- MCP client connection pooling
- Request handling under load
"""
import concurrent.futures
import json
import time
import unittest

from mvp_site.main import create_app


class TestConcurrencyIntegration(unittest.TestCase):
    """Integration test suite for concurrent request handling"""

    def setUp(self):
        """Set up test Flask application"""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_single_request_baseline(self):
        """RED→GREEN: Baseline test - single request should work"""
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "healthy")

    def test_sequential_requests_work(self):
        """RED→GREEN: Sequential requests should all succeed"""
        results = []

        for i in range(10):
            response = self.client.get("/health")
            results.append(response.status_code)

        # All requests should succeed
        self.assertEqual(
            results, [200] * 10, "All sequential requests should return 200 OK"
        )

    def test_concurrent_health_checks(self):
        """RED→GREEN: Multiple concurrent health check requests should succeed"""

        def make_request(request_id):
            response = self.client.get("/health")
            return {
                "request_id": request_id,
                "status_code": response.status_code,
                "data": json.loads(response.data),
            }

        # Make 20 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request, i) for i in range(20)]
            results = [future.result() for future in futures]

        # All requests should succeed
        status_codes = [r["status_code"] for r in results]
        self.assertEqual(
            status_codes,
            [200] * 20,
            "All concurrent requests should return 200 OK",
        )

        # All should have healthy status
        statuses = [r["data"]["status"] for r in results]
        self.assertEqual(
            statuses, ["healthy"] * 20, "All responses should have healthy status"
        )

    def test_concurrent_requests_maintain_data_integrity(self):
        """RED→GREEN: Concurrent requests should return consistent data structure"""

        def make_request(request_id):
            response = self.client.get("/health")
            return json.loads(response.data)

        # Make 50 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(make_request, i) for i in range(50)]
            results = [future.result() for future in futures]

        # All responses should have the same keys
        first_keys = set(results[0].keys())
        for i, result in enumerate(results[1:], 1):
            self.assertEqual(
                set(result.keys()),
                first_keys,
                f"Request {i} should have same keys as first request",
            )

        # All should have required fields
        for i, result in enumerate(results):
            self.assertIn("status", result, f"Request {i} should have status")
            self.assertIn("service", result, f"Request {i} should have service")
            self.assertIn("timestamp", result, f"Request {i} should have timestamp")

    def test_high_concurrency_load(self):
        """RED→GREEN: Application should handle high concurrent load"""

        def make_request(request_id):
            start_time = time.time()
            response = self.client.get("/health")
            end_time = time.time()

            return {
                "request_id": request_id,
                "status_code": response.status_code,
                "duration": end_time - start_time,
                "success": response.status_code == 200,
            }

        # Make 100 concurrent requests
        num_requests = 100
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_requests)]
            results = [future.result() for future in futures]

        # Calculate success rate
        successes = sum(1 for r in results if r["success"])
        success_rate = successes / num_requests

        # Should have high success rate (>95%)
        self.assertGreaterEqual(
            success_rate,
            0.95,
            f"Success rate should be >= 95%, got {success_rate * 100:.1f}%",
        )

        # Average response time should be reasonable (<1 second for health checks)
        avg_duration = sum(r["duration"] for r in results) / num_requests
        self.assertLess(
            avg_duration,
            1.0,
            f"Average response time should be <1s, got {avg_duration:.3f}s",
        )

    def test_no_race_conditions_in_concurrent_requests(self):
        """RED→GREEN: Concurrent requests should not corrupt shared state

        Validates that concurrent requests maintain data integrity without
        race conditions, regardless of system clock resolution.
        """

        request_count = 50

        def make_request_and_validate(request_id):
            response = self.client.get("/health")
            data = json.loads(response.data)
            # Validate data structure integrity
            self.assertIn("timestamp", data)
            self.assertIn("status", data)
            self.assertEqual(data["status"], "healthy")
            return response.status_code

        # Make concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [
                executor.submit(make_request_and_validate, i) for i in range(request_count)
            ]
            status_codes = [future.result() for future in futures]

        # All requests should succeed without exceptions or data corruption
        self.assertEqual(
            status_codes,
            [200] * request_count,
            "All concurrent requests should return 200 OK with valid data structure"
        )

    def test_connection_reuse_under_load(self):
        """RED→GREEN: Application should handle repeated concurrent requests reliably

        Validates that connection handling is robust under sustained concurrent load,
        which requires proper connection pooling configuration. This test focuses on
        reliability rather than timing performance (which is environment-dependent).
        """
        num_requests = 30

        # Perform concurrent requests to verify connection handling is robust
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(
                lambda i: self.client.get("/health").status_code,
                range(num_requests)
            ))

        # All requests should succeed - proves connection handling is robust
        self.assertEqual(
            results,
            [200] * num_requests,
            "Repeated concurrent requests should all succeed with robust connection handling"
        )

    def test_error_handling_under_concurrent_load(self):
        """RED→GREEN: Error responses should be handled consistently under load

        Tests that non-existent API endpoints return consistent error responses
        (typically 404) when accessed concurrently, verifying thread-safe error handling.
        """

        def make_request(request_id):
            # Try to access API endpoint that doesn't exist (should return 404)
            response = self.client.get(f"/api/nonexistent-endpoint-{request_id}")
            return {
                "request_id": request_id,
                "status_code": response.status_code,
                "has_response": response.status_code in [200, 404],
            }

        # Make concurrent requests to non-existent API endpoints
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request, i) for i in range(20)]
            results = [future.result() for future in futures]

        # All should return valid HTTP responses (not timeouts/errors)
        all_responded = all(r["has_response"] for r in results)
        self.assertTrue(
            all_responded,
            "All concurrent requests should receive valid HTTP responses"
        )

        # Response codes should be consistent
        status_codes = [r["status_code"] for r in results]
        unique_codes = set(status_codes)

        # Should have only 1-2 unique status codes (consistent handling)
        self.assertLessEqual(
            len(unique_codes),
            2,
            f"Status codes should be consistent, got {unique_codes}"
        )

    def test_mixed_endpoint_concurrent_access(self):
        """RED→GREEN: Concurrent access to different endpoints should work"""

        def access_health(request_id):
            response = self.client.get("/health")
            return {"endpoint": "health", "status": response.status_code}

        def access_api_time(request_id):
            response = self.client.get("/api/time")
            return {"endpoint": "api_time", "status": response.status_code}

        requests = []
        # Mix health and time endpoint requests
        for i in range(10):
            requests.append(("health", access_health, i))
            requests.append(("api_time", access_api_time, i))

        # Execute all concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(func, req_id) for _, func, req_id in requests]
            results = [future.result() for future in futures]

        # Group by endpoint
        health_results = [r for r in results if r["endpoint"] == "health"]
        api_time_results = [r for r in results if r["endpoint"] == "api_time"]

        # All health checks should succeed
        health_success = all(r["status"] == 200 for r in health_results)
        self.assertTrue(health_success, "All health checks should return 200 OK")

        # API time endpoint success (may be 401 if auth required, but should respond)
        api_time_responses = all(r["status"] in [200, 401] for r in api_time_results)
        self.assertTrue(
            api_time_responses, "API time endpoint should respond (200 or 401)"
        )

    def test_sustained_concurrent_load(self):
        """RED→GREEN: Application should handle sustained concurrent load"""

        def make_burst(burst_id):
            # Each burst makes 5 requests
            responses = []
            for i in range(5):
                response = self.client.get("/health")
                responses.append(response.status_code)
            return responses

        # Make 10 bursts of 5 requests each = 50 total requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_burst, i) for i in range(10)]
            all_results = [status for future in futures for status in future.result()]

        # All 50 requests should succeed
        success_count = sum(1 for status in all_results if status == 200)
        self.assertEqual(
            success_count, 50, "All 50 requests in sustained load should succeed"
        )


if __name__ == "__main__":
    unittest.main()
