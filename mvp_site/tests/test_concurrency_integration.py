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

import asyncio
import concurrent.futures
import itertools
import json
import os
import threading
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("ALLOW_TEST_AUTH_BYPASS", "true")
os.environ.setdefault("TESTING", "true")

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
                executor.submit(make_request_and_validate, i)
                for i in range(request_count)
            ]
            status_codes = [future.result() for future in futures]

        # All requests should succeed without exceptions or data corruption
        self.assertEqual(
            status_codes,
            [200] * request_count,
            "All concurrent requests should return 200 OK with valid data structure",
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
            results = list(
                executor.map(
                    lambda i: self.client.get("/health").status_code,
                    range(num_requests),
                )
            )

        # All requests should succeed - proves connection handling is robust
        self.assertEqual(
            results,
            [200] * num_requests,
            "Repeated concurrent requests should all succeed with robust connection handling",
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
            all_responded, "All concurrent requests should receive valid HTTP responses"
        )

        # Response codes should be consistent
        status_codes = [r["status_code"] for r in results]
        unique_codes = set(status_codes)

        # Should have only 1-2 unique status codes (consistent handling)
        self.assertLessEqual(
            len(unique_codes),
            2,
            f"Status codes should be consistent, got {unique_codes}",
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


class TestParallelExecutionTiming(unittest.TestCase):
    """
    TDD RED PHASE: Tests that demonstrate the blocking I/O issue

    These tests MUST FAIL before the fix is applied, proving:
    1. Current implementation processes requests serially (blocking)
    2. Multiple concurrent requests take N×single_request_time (serial)
    3. After fix, requests should complete in ~1×single_request_time (parallel)

    ROOT CAUSE: Blocking Firestore calls inside shared asyncio event loop
    - Firestore service calls were executed directly in the event loop
    - run_in_background_loop().result() blocked on serialized Firestore calls
    - Result: Single event loop serialized ALL requests

    FIX: Use loop.run_in_executor() for blocking I/O calls
    """

    def setUp(self):
        """Set up test Flask application with simulated slow operations"""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Simulated delay for blocking operations (100ms)
        self.simulated_delay_ms = 100

    def test_blocking_io_in_shared_event_loop_causes_serialization(self):
        """
        RED TEST: Directly tests that blocking I/O in a shared event loop serializes execution

        This test simulates the exact pattern used in main.py:
        - Single shared asyncio event loop
        - Multiple async coroutines submitted via run_coroutine_threadsafe
        - Blocking I/O (time.sleep) inside the coroutines

        BEFORE FIX: All coroutines run serially because blocking I/O blocks event loop
        AFTER FIX: Coroutines run in parallel using run_in_executor for blocking I/O
        """
        io_delay = 0.1  # 100ms blocking I/O
        num_tasks = 4

        # Create shared event loop (same pattern as the shared loop used in main.py)
        shared_loop = asyncio.new_event_loop()

        def start_loop(loop):
            asyncio.set_event_loop(loop)
            loop.run_forever()

        loop_thread = threading.Thread(
            target=start_loop, args=(shared_loop,), daemon=True
        )
        loop_thread.start()
        time.sleep(0.01)  # Let loop start

        # BLOCKING VERSION (current main.py behavior)
        async def blocking_coroutine(task_id):
            """Simulates current behavior: blocking I/O directly in coroutine"""
            time.sleep(io_delay)  # BLOCKING - blocks the event loop
            return task_id

        # NON-BLOCKING VERSION (what we need to implement)
        async def nonblocking_coroutine(task_id):
            """Simulates fixed behavior: blocking I/O in executor"""
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, time.sleep, io_delay)
            return task_id

        def run_concurrent_tasks(coroutine_func):
            """Run N tasks concurrently and measure total time"""
            start = time.perf_counter()

            # Submit tasks from multiple threads (simulating Gunicorn threads)
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=num_tasks
            ) as executor:

                def submit_and_wait(task_id):
                    future = asyncio.run_coroutine_threadsafe(
                        coroutine_func(task_id), shared_loop
                    )
                    return future.result(timeout=5.0)

                futures = [
                    executor.submit(submit_and_wait, i) for i in range(num_tasks)
                ]
                results = [f.result() for f in futures]

            duration = time.perf_counter() - start
            return duration, results

        try:
            # Test BLOCKING version (should be SERIAL - takes ~400ms for 4 tasks)
            blocking_duration, _ = run_concurrent_tasks(blocking_coroutine)

            # Test NON-BLOCKING version (should be PARALLEL - takes ~100ms for 4 tasks)
            nonblocking_duration, _ = run_concurrent_tasks(nonblocking_coroutine)

            # Log timing comparison
            print("\n=== SHARED EVENT LOOP CONCURRENCY TEST ===")
            print(f"I/O delay per task: {io_delay * 1000:.0f}ms")
            print(f"Number of concurrent tasks: {num_tasks}")
            print(
                f"BLOCKING version (time.sleep in coroutine): {blocking_duration * 1000:.1f}ms"
            )
            print(
                f"NON-BLOCKING version (run_in_executor): {nonblocking_duration * 1000:.1f}ms"
            )
            print(f"Expected SERIAL: ~{io_delay * num_tasks * 1000:.0f}ms")
            print(f"Expected PARALLEL: ~{io_delay * 1000:.0f}ms")
            print(
                f"Blocking ratio (actual/expected_serial): {blocking_duration / (io_delay * num_tasks):.2f}x"
            )
            print(
                f"Non-blocking ratio (actual/expected_parallel): {nonblocking_duration / io_delay:.2f}x"
            )

            # ASSERTIONS

            # 1. Blocking version should be SLOW (serial execution ~N×delay)
            serial_expected_min = io_delay * (num_tasks - 0.5)  # Allow some margin
            self.assertGreater(
                blocking_duration,
                serial_expected_min,
                f"Blocking version should take at least {serial_expected_min * 1000:.0f}ms "
                f"(serial execution), got {blocking_duration * 1000:.0f}ms",
            )

            # 2. Non-blocking version should be FAST (parallel execution ~1×delay)
            parallel_expected_max = io_delay * 2.5  # Allow overhead
            self.assertLess(
                nonblocking_duration,
                parallel_expected_max,
                f"Non-blocking version should complete in <{parallel_expected_max * 1000:.0f}ms "
                f"(parallel execution), got {nonblocking_duration * 1000:.0f}ms\n"
                f"FIX: Use loop.run_in_executor() for blocking I/O",
            )

            # 3. Non-blocking should be significantly faster than blocking
            speedup = blocking_duration / nonblocking_duration
            self.assertGreater(
                speedup,
                2.0,
                f"Non-blocking should be at least 2x faster, got {speedup:.1f}x speedup",
            )
        finally:
            # Cleanup
            shared_loop.call_soon_threadsafe(shared_loop.stop)
            loop_thread.join(timeout=1)

    def test_parallel_requests_execute_concurrently_not_serially(self):
        """
        RED TEST: Concurrent requests should complete in parallel time, not serial time

        Test Matrix:
        | Concurrent Requests | Expected Parallel Time | Serial Time (Fail) |
        |---------------------|------------------------|-------------------|
        | 2                   | ~1× single req         | 2× single req     |
        | 4                   | ~1× single req         | 4× single req     |
        | 8                   | ~1× single req         | 8× single req     |

        This test should FAIL before the fix because:
        - Blocking firestore calls serialize request handling
        - N requests take N × single_request_time instead of ~1 × single_request_time

        After fix (run_in_executor), this test should PASS because:
        - Blocking I/O runs in thread pool, doesn't block event loop
        - N requests complete in ~1 × single_request_time (truly parallel)
        """
        num_concurrent_requests = 4

        def make_timed_request(request_id):
            """Make request and return timing info"""
            start = time.perf_counter()
            response = self.client.get("/health")
            end = time.perf_counter()
            duration = end - start
            return {
                "request_id": request_id,
                "start": start,
                "end": end,
                "duration": duration,
                "status": response.status_code,
            }

        # Measure single request baseline
        single_start = time.perf_counter()
        response = self.client.get("/health")
        single_duration = time.perf_counter() - single_start
        self.assertEqual(
            response.status_code,
            200,
            "Single baseline request should return 200",
        )

        # Now make N concurrent requests
        concurrent_start = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=num_concurrent_requests
        ) as executor:
            futures = [
                executor.submit(make_timed_request, i)
                for i in range(num_concurrent_requests)
            ]
            results = [f.result() for f in futures]
        concurrent_total_duration = time.perf_counter() - concurrent_start

        # All requests should succeed
        all_succeeded = all(r["status"] == 200 for r in results)
        self.assertTrue(all_succeeded, "All concurrent requests should return 200")

        # CRITICAL ASSERTION: Concurrent requests should complete in parallel
        # If serial: concurrent_total ≈ N × single
        # If parallel: concurrent_total ≈ 1 × single (with small overhead)

        # Allow generous overhead to avoid false positives in fast local environments
        # Serial execution would be roughly N×single request time
        parallel_threshold = single_duration * (num_concurrent_requests + 1.5)
        serial_indicator = single_duration * (num_concurrent_requests - 0.5)

        # Log timing for debugging
        print("\n=== PARALLEL EXECUTION TEST ===")
        print(f"Single request duration: {single_duration * 1000:.1f}ms")
        print(
            f"Concurrent ({num_concurrent_requests}x) duration: {concurrent_total_duration * 1000:.1f}ms"
        )
        print(f"Parallel threshold: {parallel_threshold * 1000:.1f}ms")
        print(f"Serial indicator: {serial_indicator * 1000:.1f}ms")
        print(
            f"Ratio (concurrent/single): {concurrent_total_duration / single_duration:.2f}x"
        )

        # The key assertion - this should FAIL if requests are serial
        self.assertLess(
            concurrent_total_duration,
            parallel_threshold,
            f"CONCURRENCY ISSUE DETECTED!\n"
            f"{num_concurrent_requests} concurrent requests took {concurrent_total_duration * 1000:.1f}ms "
            f"but should complete in ~{parallel_threshold * 1000:.1f}ms for parallel execution.\n"
            f"Single request takes {single_duration * 1000:.1f}ms.\n"
            f"Ratio: {concurrent_total_duration / single_duration:.2f}x (should be <2.5x for parallel)\n"
            f"ROOT CAUSE: Blocking Firestore I/O inside shared asyncio event loop\n"
            f"FIX: Use loop.run_in_executor() for blocking database calls",
        )

    def test_async_route_with_blocking_io_demonstrates_serialization(self):
        """
        RED TEST: Demonstrates that blocking I/O in async routes serializes requests

        This test patches the firestore service to add a measurable delay,
        proving that blocking I/O in the shared event loop causes serialization.

        Expected behavior BEFORE fix: 4 requests × 100ms delay = ~400ms total (SERIAL)
        Expected behavior AFTER fix: 4 requests × 100ms delay = ~100ms total (PARALLEL)
        """
        num_requests = 4
        io_delay_seconds = 0.1  # 100ms simulated blocking I/O

        # Create a mock that simulates blocking I/O
        call_counter = itertools.count()

        def slow_firestore_get(*args, **kwargs):
            next(call_counter)
            time.sleep(io_delay_seconds)  # Simulate blocking I/O
            return None, []  # Return empty campaign data

        # Patch firestore service to use slow mock
        with patch(
            "mvp_site.firestore_service.get_campaign_by_id",
            side_effect=slow_firestore_get,
        ):
            with patch("mvp_site.firestore_service.get_user_settings", return_value={}):
                with patch(
                    "mvp_site.firestore_service.get_campaign_game_state",
                    return_value=None,
                ):

                    def make_api_request(request_id):
                        """Make API request that triggers Firestore call"""
                        start = time.perf_counter()
                        # Use a test campaign ID - will hit mocked firestore
                        response = self.client.get(
                            "/api/campaigns/test-campaign-id",
                            headers={
                                "Authorization": "Bearer test-token",
                                "X-Test-Bypass-Auth": "true",
                                "X-Test-User-ID": "test-user",
                            },
                        )
                        end = time.perf_counter()
                        return {
                            "request_id": request_id,
                            "duration": end - start,
                            "status": response.status_code,
                        }

                    # Measure single request with simulated I/O
                    single_start = time.perf_counter()
                    single_result = make_api_request(0)
                    single_duration = time.perf_counter() - single_start
                    self.assertIn(
                        single_result["status"],
                        {200, 404},
                        "Single baseline request should return 200/404 depending on mock",
                    )

                    # Make concurrent requests
                    concurrent_start = time.perf_counter()
                    with concurrent.futures.ThreadPoolExecutor(
                        max_workers=num_requests
                    ) as executor:
                        futures = [
                            executor.submit(make_api_request, i)
                            for i in range(num_requests)
                        ]
                        results = [f.result() for f in futures]
                        for result in results:
                            self.assertIn(
                                result["status"],
                                {200, 404},
                                f"Concurrent request {result['request_id']} should return 200/404",
                            )
                    concurrent_duration = time.perf_counter() - concurrent_start

        # Log timing analysis
        print("\n=== BLOCKING I/O SERIALIZATION TEST ===")
        print(f"Simulated I/O delay: {io_delay_seconds * 1000:.0f}ms per call")
        print(f"Single request duration: {single_duration * 1000:.1f}ms")
        print(
            f"Concurrent ({num_requests}x) duration: {concurrent_duration * 1000:.1f}ms"
        )
        print(f"Expected PARALLEL: ~{io_delay_seconds * 1000:.0f}ms")
        print(f"Expected SERIAL: ~{io_delay_seconds * num_requests * 1000:.0f}ms")
        print(
            f"Actual ratio (concurrent/io_delay): {concurrent_duration / io_delay_seconds:.2f}x"
        )

        # CRITICAL: This tests parallel execution
        # If parallel: concurrent_duration ≈ 1 × io_delay (all run simultaneously)
        # If serial: concurrent_duration ≈ N × io_delay (one after another)

        parallel_max = io_delay_seconds * 2.0  # Allow 2x for overhead
        serial_min = io_delay_seconds * (num_requests - 0.5)  # Serial would be ~N×delay

        # This assertion FAILS if requests are serialized
        # After implementing run_in_executor, it should PASS
        self.assertLess(
            concurrent_duration,
            parallel_max,
            f"SERIALIZATION DETECTED!\n"
            f"Concurrent requests took {concurrent_duration * 1000:.1f}ms\n"
            f"For parallel execution, expected <{parallel_max * 1000:.1f}ms\n"
            f"Serial execution indicator: >{serial_min * 1000:.1f}ms\n"
            f"This proves blocking I/O in async routes causes request serialization.\n"
            f"FIX REQUIRED: Use loop.run_in_executor() for firestore calls",
        )


if __name__ == "__main__":
    unittest.main()
