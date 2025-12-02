"""
TDD tests for Gunicorn configuration (gunicorn.conf.py)

Tests verify that the Gunicorn configuration file:
1. Loads without errors
2. Has correct worker formula calculation
3. Uses gthread worker class
4. Has appropriate timeout settings
5. Responds to environment variables
"""
import importlib.util
import multiprocessing
import os
import unittest


class TestGunicornConfiguration(unittest.TestCase):
    """Test suite for gunicorn.conf.py configuration file"""

    def setUp(self):
        """Load gunicorn.conf.py as a module for testing"""
        # Path to gunicorn.conf.py
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "gunicorn.conf.py"
        )

        # Load the config file as a module
        spec = importlib.util.spec_from_file_location("gunicorn_config", config_path)
        self.config = importlib.util.module_from_spec(spec)

        # Store original environment
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Restore original environment after each test"""
        # Remove any keys added during test
        for key in list(os.environ.keys()):
            if key not in self.original_env:
                del os.environ[key]
        # Restore original values
        for key, value in self.original_env.items():
            os.environ[key] = value

    def _reload_config(self):
        """Reload configuration with current environment variables"""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "gunicorn.conf.py"
        )
        spec = importlib.util.spec_from_file_location("gunicorn_config", config_path)
        self.config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.config)

    def test_config_file_loads_without_errors(self):
        """RED→GREEN: Configuration file should load without syntax errors"""
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "gunicorn.conf.py"
            )
            spec = importlib.util.spec_from_file_location(
                "gunicorn_config", config_path
            )
            config = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config)
            loaded = True
        except Exception as e:
            loaded = False
            self.fail(f"Configuration file failed to load: {e}")

        self.assertTrue(loaded, "Configuration file should load without errors")

    def test_worker_formula_calculation(self):
        """RED→GREEN: Workers should follow (2*CPU)+1 formula by default"""
        self._reload_config()

        expected_workers = (2 * multiprocessing.cpu_count()) + 1
        actual_workers = self.config.workers

        self.assertEqual(
            actual_workers,
            expected_workers,
            f"Workers should be (2*CPU)+1 = {expected_workers}, got {actual_workers}"
        )

    def test_worker_class_is_gthread(self):
        """RED→GREEN: Worker class should be 'gthread' for threaded workers"""
        self._reload_config()

        self.assertEqual(
            self.config.worker_class,
            "gthread",
            "Worker class should be 'gthread' for concurrent request handling"
        )

    def test_threads_per_worker_default(self):
        """RED→GREEN: Should have 4 threads per worker by default"""
        self._reload_config()

        self.assertEqual(
            self.config.threads,
            4,
            "Default threads per worker should be 4"
        )

    def test_timeout_is_sufficient_for_ai_operations(self):
        """RED→GREEN: Timeout should be 600s (10 minutes) for long AI operations"""
        self._reload_config()

        self.assertEqual(
            self.config.timeout,
            600,
            "Timeout should be 600 seconds for Gemini API calls"
        )

    def test_timeout_respects_central_environment_variable(self):
        """Timeout should follow WORLDARCH_TIMEOUT_SECONDS when provided"""
        os.environ["WORLDARCH_TIMEOUT_SECONDS"] = "720"

        self._reload_config()

        self.assertEqual(
            self.config.timeout,
            720,
            "Timeout should honor WORLDARCH_TIMEOUT_SECONDS for stack-wide sync",
        )

    def test_workers_respects_environment_variable(self):
        """RED→GREEN: GUNICORN_WORKERS env var should override default"""
        # Set environment variable
        os.environ["GUNICORN_WORKERS"] = "7"

        # Reload config to pick up environment variable
        self._reload_config()

        self.assertEqual(
            self.config.workers,
            7,
            "Workers should respect GUNICORN_WORKERS environment variable"
        )

    def test_threads_respects_environment_variable(self):
        """RED→GREEN: GUNICORN_THREADS env var should override default"""
        # Set environment variable
        os.environ["GUNICORN_THREADS"] = "8"

        # Reload config to pick up environment variable
        self._reload_config()

        self.assertEqual(
            self.config.threads,
            8,
            "Threads should respect GUNICORN_THREADS environment variable"
        )

    def test_bind_address_is_cloud_run_compatible(self):
        """RED→GREEN: Should bind to 0.0.0.0:8080 for Cloud Run"""
        self._reload_config()

        self.assertEqual(
            self.config.bind,
            "0.0.0.0:8080",
            "Should bind to 0.0.0.0:8080 for container compatibility"
        )

    def test_logging_outputs_to_stdout_stderr(self):
        """RED→GREEN: Logs should go to stdout/stderr for Cloud Run"""
        self._reload_config()

        self.assertEqual(
            self.config.accesslog,
            "-",
            "Access log should output to stdout ('-')"
        )
        self.assertEqual(
            self.config.errorlog,
            "-",
            "Error log should output to stderr ('-')"
        )

    def test_worker_restart_policy_prevents_memory_leaks(self):
        """RED→GREEN: Workers should restart after max_requests to prevent leaks"""
        self._reload_config()

        self.assertIsNotNone(
            self.config.max_requests,
            "max_requests should be set for worker restart policy"
        )
        self.assertGreater(
            self.config.max_requests,
            0,
            "max_requests should be positive"
        )
        self.assertEqual(
            self.config.max_requests,
            1000,
            "Workers should restart after 1000 requests"
        )

    def test_jitter_prevents_simultaneous_worker_restarts(self):
        """RED→GREEN: max_requests_jitter should prevent all workers restarting at once"""
        self._reload_config()

        self.assertIsNotNone(
            self.config.max_requests_jitter,
            "max_requests_jitter should be set"
        )
        self.assertGreater(
            self.config.max_requests_jitter,
            0,
            "Jitter should be positive to add randomness"
        )

    def test_daemon_mode_is_disabled_for_containers(self):
        """RED→GREEN: Daemon mode should be False for containerized deployment"""
        self._reload_config()

        self.assertFalse(
            self.config.daemon,
            "Daemon mode should be False for Docker/Cloud Run"
        )

    def test_process_name_is_identifiable(self):
        """RED→GREEN: Process name should be identifiable for monitoring"""
        self._reload_config()

        self.assertIsNotNone(
            self.config.proc_name,
            "Process name should be set for monitoring"
        )
        self.assertIn(
            "worldarchitect",
            self.config.proc_name.lower(),
            "Process name should identify the application"
        )

    def test_graceful_timeout_allows_request_completion(self):
        """RED→GREEN: Graceful timeout should allow in-flight requests to complete"""
        self._reload_config()

        self.assertIsNotNone(
            self.config.graceful_timeout,
            "Graceful timeout should be set"
        )
        self.assertGreater(
            self.config.graceful_timeout,
            0,
            "Graceful timeout should be positive"
        )

    def test_worker_connections_for_async_workers(self):
        """RED→GREEN: worker_connections should be set for potential async use"""
        self._reload_config()

        self.assertIsNotNone(
            self.config.worker_connections,
            "worker_connections should be set"
        )
        self.assertGreater(
            self.config.worker_connections,
            0,
            "worker_connections should be positive"
        )

    def test_hooks_are_callable(self):
        """RED→GREEN: Lifecycle hooks should be callable functions"""
        self._reload_config()

        # Check if hooks exist and are callable
        hooks_to_test = [
            "on_starting",
            "on_reload",
            "worker_int",
            "worker_abort",
        ]

        for hook_name in hooks_to_test:
            if hasattr(self.config, hook_name):
                hook = getattr(self.config, hook_name)
                self.assertTrue(
                    callable(hook),
                    f"{hook_name} hook should be callable"
                )

    def test_calculated_concurrency_is_correct(self):
        """RED→GREEN: Total concurrency should be workers × threads"""
        # Set known values
        os.environ["GUNICORN_WORKERS"] = "5"
        os.environ["GUNICORN_THREADS"] = "4"

        self._reload_config()

        expected_concurrency = 5 * 4  # 20 concurrent requests
        actual_concurrency = self.config.workers * self.config.threads

        self.assertEqual(
            actual_concurrency,
            expected_concurrency,
            f"Total concurrency should be workers×threads = {expected_concurrency}"
        )


if __name__ == "__main__":
    unittest.main()
