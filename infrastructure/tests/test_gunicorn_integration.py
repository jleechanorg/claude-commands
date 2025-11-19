"""
Integration tests for Gunicorn configuration with worker_config library

Tests the full configuration stack including:
- gunicorn.conf.py loading and execution
- Environment variable propagation
- Worker and thread configuration in different scenarios
- Configuration hooks and lifecycle management
"""
import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import multiprocessing
import importlib.util

# Add project root to path for infrastructure package import
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


class TestGunicornIntegration(unittest.TestCase):
    """Integration test suite for full gunicorn configuration"""

    def load_gunicorn_config(self):
        """
        Helper to load gunicorn.conf.py as a module

        Returns:
            Module object with gunicorn configuration
        """
        # Path to mvp_site/gunicorn.conf.py from infrastructure/tests/
        config_path = os.path.join(
            project_root,
            "mvp_site",
            "gunicorn.conf.py"
        )
        spec = importlib.util.spec_from_file_location("gunicorn_config", config_path)
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        return config_module

    def test_gunicorn_config_loads_successfully(self):
        """Integration: gunicorn.conf.py should load without errors"""
        try:
            config = self.load_gunicorn_config()
            # Verify key configuration attributes exist
            self.assertTrue(hasattr(config, 'workers'))
            self.assertTrue(hasattr(config, 'threads'))
            self.assertTrue(hasattr(config, 'worker_class'))
            self.assertTrue(hasattr(config, 'bind'))
            self.assertTrue(hasattr(config, 'timeout'))
        except Exception as e:
            self.fail(f"gunicorn.conf.py failed to load: {e}")

    def test_production_environment_configuration(self):
        """Integration: Production environment should use (2*CPU)+1 workers"""
        with patch.dict('os.environ', {}, clear=True):
            config = self.load_gunicorn_config()
            expected_workers = (2 * multiprocessing.cpu_count()) + 1
            self.assertEqual(config.workers, expected_workers)
            self.assertEqual(config.threads, 4)  # Default threads
            self.assertEqual(config.worker_class, "gthread")

    def test_preview_environment_configuration(self):
        """Integration: Preview environment should use 1 worker"""
        with patch.dict('os.environ', {'ENVIRONMENT': 'preview'}, clear=True):
            config = self.load_gunicorn_config()
            self.assertEqual(config.workers, 1)
            self.assertEqual(config.threads, 4)

    def test_gunicorn_workers_override(self):
        """Integration: GUNICORN_WORKERS should override default calculation"""
        with patch.dict('os.environ', {'GUNICORN_WORKERS': '8'}, clear=True):
            config = self.load_gunicorn_config()
            self.assertEqual(config.workers, 8)

    def test_gunicorn_threads_override(self):
        """Integration: GUNICORN_THREADS should override default threads"""
        with patch.dict('os.environ', {'GUNICORN_THREADS': '12'}, clear=True):
            config = self.load_gunicorn_config()
            self.assertEqual(config.threads, 12)

    def test_combined_environment_overrides(self):
        """Integration: Both GUNICORN_WORKERS and GUNICORN_THREADS should work together"""
        with patch.dict('os.environ', {
            'GUNICORN_WORKERS': '6',
            'GUNICORN_THREADS': '8',
            'ENVIRONMENT': 'preview'  # Should be overridden by GUNICORN_WORKERS
        }, clear=True):
            config = self.load_gunicorn_config()
            self.assertEqual(config.workers, 6)  # GUNICORN_WORKERS overrides preview
            self.assertEqual(config.threads, 8)

    def test_port_binding_configuration(self):
        """Integration: PORT environment variable should configure bind address"""
        with patch.dict('os.environ', {'PORT': '9090'}, clear=True):
            config = self.load_gunicorn_config()
            self.assertEqual(config.bind, "0.0.0.0:9090")

    def test_port_default_binding(self):
        """Integration: Default to port 8080 when PORT not set"""
        with patch.dict('os.environ', {}, clear=True):
            config = self.load_gunicorn_config()
            self.assertEqual(config.bind, "0.0.0.0:8080")

    def test_worker_lifecycle_configuration(self):
        """Integration: Worker lifecycle settings should be configured"""
        config = self.load_gunicorn_config()
        self.assertEqual(config.max_requests, 1000)
        self.assertEqual(config.max_requests_jitter, 50)
        self.assertEqual(config.timeout, 300)
        self.assertEqual(config.graceful_timeout, 30)

    def test_logging_configuration(self):
        """Integration: Logging should be configured for Cloud Run"""
        config = self.load_gunicorn_config()
        self.assertEqual(config.accesslog, "-")  # stdout
        self.assertEqual(config.errorlog, "-")   # stderr
        self.assertEqual(config.loglevel, "info")

    def test_on_starting_hook_exists(self):
        """Integration: on_starting hook should be callable"""
        config = self.load_gunicorn_config()
        self.assertTrue(hasattr(config, 'on_starting'))
        self.assertTrue(callable(config.on_starting))

    def test_on_starting_hook_logs_configuration(self):
        """Integration: on_starting hook should log configuration details"""
        config = self.load_gunicorn_config()

        # Create mock server with log
        mock_server = MagicMock()
        mock_logger = MagicMock()
        mock_server.log = mock_logger

        # Call the hook
        config.on_starting(mock_server)

        # Verify logging occurred
        self.assertTrue(mock_logger.info.called)
        call_args = [call[0][0] for call in mock_logger.info.call_args_list]

        # Should log workers, threads, and total concurrent requests
        self.assertTrue(any("Workers:" in arg for arg in call_args))
        self.assertTrue(any("Threads per worker:" in arg for arg in call_args))
        self.assertTrue(any("Total concurrent requests:" in arg for arg in call_args))

    def test_total_concurrent_capacity(self):
        """Integration: Total concurrent capacity should be workers × threads"""
        with patch.dict('os.environ', {
            'GUNICORN_WORKERS': '4',
            'GUNICORN_THREADS': '6'
        }, clear=True):
            config = self.load_gunicorn_config()
            expected_capacity = 4 * 6  # 24 concurrent requests
            actual_capacity = config.workers * config.threads
            self.assertEqual(actual_capacity, expected_capacity)


if __name__ == '__main__':
    unittest.main()
