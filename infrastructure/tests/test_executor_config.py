"""
TDD Tests for Centralized Executor Configuration

Tests that:
1. Executor is configured with 100 workers
2. configure_asyncio_executor() sets the default executor
3. asyncio.to_thread() uses our executor after configuration
4. Singleton pattern works correctly
"""

import asyncio
import os
import threading
import time
import unittest

# Import the module under test
from infrastructure import executor_config


class TestExecutorConfiguration(unittest.TestCase):
    """Test executor configuration values."""

    def setUp(self):
        """Reset executor state before each test."""
        executor_config.shutdown_executor(wait=False)
        executor_config._executor = None

    def tearDown(self):
        """Cleanup executor after each test."""
        executor_config.shutdown_executor(wait=False)

    def test_default_max_workers_is_100(self):
        """RED→GREEN: Default executor should have 100 workers."""
        self.assertEqual(
            executor_config.EXECUTOR_MAX_WORKERS, 100,
            "Default EXECUTOR_MAX_WORKERS should be 100"
        )

    def test_executor_created_with_100_workers(self):
        """RED→GREEN: Executor should be created with 100 max_workers."""
        executor = executor_config.get_blocking_io_executor()

        self.assertIsNotNone(executor)
        stats = executor_config.get_executor_stats()
        self.assertEqual(
            stats["max_workers"], 100,
            f"Executor should have 100 workers, got {stats['max_workers']}"
        )

    def test_executor_thread_prefix(self):
        """RED→GREEN: Executor threads should have 'blocking_io' prefix."""
        self.assertEqual(
            executor_config.EXECUTOR_THREAD_PREFIX, "blocking_io"
        )

    def test_max_workers_from_environment(self):
        """RED→GREEN: EXECUTOR_MAX_WORKERS env var should override default."""
        # Note: EXECUTOR_MAX_WORKERS is evaluated at import time, so changing
        # the environment here wouldn't update the module constant without
        # reloading the module. This test verifies the parsed value that the
        # module is currently using.
        test_value = os.getenv("EXECUTOR_MAX_WORKERS", "100")
        expected = int(test_value)
        self.assertEqual(
            executor_config.EXECUTOR_MAX_WORKERS, expected,
            "EXECUTOR_MAX_WORKERS should be parsed from env or default to 100"
        )


class TestExecutorSingleton(unittest.TestCase):
    """Test singleton pattern for executor."""

    def setUp(self):
        """Reset executor state before each test."""
        executor_config.shutdown_executor(wait=False)
        executor_config._executor = None

    def tearDown(self):
        """Cleanup executor after each test."""
        executor_config.shutdown_executor(wait=False)

    def test_get_executor_returns_singleton(self):
        """RED→GREEN: Multiple calls should return same executor instance."""
        executor1 = executor_config.get_blocking_io_executor()
        executor2 = executor_config.get_blocking_io_executor()

        self.assertIs(
            executor1, executor2,
            "get_blocking_io_executor() should return singleton"
        )

    def test_thread_safe_initialization(self):
        """RED→GREEN: Concurrent initialization should create only one executor."""
        executors = []
        errors = []

        def get_executor():
            try:
                executors.append(executor_config.get_blocking_io_executor())
            except Exception as e:
                errors.append(e)

        # Start 10 threads simultaneously
        threads = [threading.Thread(target=get_executor) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Errors during initialization: {errors}")
        self.assertEqual(len(executors), 10)
        # All should be the same instance
        self.assertTrue(
            all(e is executors[0] for e in executors),
            "All threads should get the same executor instance"
        )


class TestAsyncioIntegration(unittest.TestCase):
    """Test asyncio.to_thread() integration."""

    def setUp(self):
        """Reset executor state before each test."""
        executor_config.shutdown_executor(wait=False)
        executor_config._executor = None

    def tearDown(self):
        """Cleanup executor after each test."""
        executor_config.shutdown_executor(wait=False)

    def test_configure_asyncio_executor_sets_default(self):
        """RED→GREEN: configure_asyncio_executor() should set loop's default executor."""
        loop = asyncio.new_event_loop()

        try:
            executor_config.configure_asyncio_executor(loop)

            # The loop should now use our executor
            # We verify by checking thread names when running tasks
            async def get_thread_name():
                return await asyncio.to_thread(
                    lambda: threading.current_thread().name
                )

            asyncio.set_event_loop(loop)
            thread_name = loop.run_until_complete(get_thread_name())

            self.assertIn(
                "blocking_io", thread_name.lower(),
                f"Thread name should contain 'blocking_io', got '{thread_name}'"
            )
        finally:
            loop.close()

    def test_100_concurrent_tasks_succeed(self):
        """RED→GREEN: Should handle 100 concurrent blocking tasks."""
        loop = asyncio.new_event_loop()
        executor_config.configure_asyncio_executor(loop)

        active_count = 0
        max_concurrent = 0
        count_lock = threading.Lock()

        def blocking_task():
            nonlocal active_count, max_concurrent
            with count_lock:
                active_count += 1
                if active_count > max_concurrent:
                    max_concurrent = active_count

            time.sleep(0.05)  # Simulate I/O

            with count_lock:
                active_count -= 1

            return threading.current_thread().name

        async def run_100_tasks():
            tasks = [asyncio.to_thread(blocking_task) for _ in range(100)]
            results = await asyncio.gather(*tasks)
            return results

        try:
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(run_100_tasks())

            self.assertEqual(len(results), 100, "Should complete 100 tasks")
            self.assertGreaterEqual(
                max_concurrent, 80,
                f"Should achieve at least 80 concurrent tasks, got {max_concurrent}. "
                f"This suggests executor doesn't have enough workers."
            )
        finally:
            loop.close()


class TestExecutorStats(unittest.TestCase):
    """Test executor monitoring."""

    def setUp(self):
        """Reset executor state before each test."""
        executor_config.shutdown_executor(wait=False)
        executor_config._executor = None

    def tearDown(self):
        """Cleanup executor after each test."""
        executor_config.shutdown_executor(wait=False)

    def test_get_executor_stats(self):
        """RED→GREEN: Should return correct stats before and after initialization."""
        # Before initialization - executor should not be initialized
        stats_before = executor_config.get_executor_stats()
        self.assertEqual(stats_before["max_workers"], 100)
        self.assertEqual(stats_before["thread_prefix"], "blocking_io")
        self.assertFalse(stats_before["executor_initialized"])

        # After initialization
        executor_config.get_blocking_io_executor()
        stats_after = executor_config.get_executor_stats()
        self.assertTrue(stats_after["executor_initialized"])


if __name__ == "__main__":
    unittest.main()
