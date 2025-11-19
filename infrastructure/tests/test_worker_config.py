"""
TDD tests for worker configuration library

Following RED-GREEN-REFACTOR methodology:
1. RED: Write failing tests
2. GREEN: Implement minimal code to pass
3. REFACTOR: Improve code quality
"""
import sys
import os
import unittest
from unittest.mock import patch
import multiprocessing

# Add parent directory to path for infrastructure package import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import from infrastructure package
from infrastructure import worker_config


class TestWorkerConfig(unittest.TestCase):
    """Test suite for worker configuration library"""

    def test_parse_workers_valid_value(self):
        """RED: Should parse valid GUNICORN_WORKERS value"""
        result = worker_config.parse_workers("5", default_workers=3)
        self.assertEqual(result, 5)

    def test_parse_workers_invalid_value(self):
        """RED: Should return default for invalid GUNICORN_WORKERS value"""
        result = worker_config.parse_workers("abc", default_workers=3)
        self.assertEqual(result, 3)

    def test_parse_workers_none_value(self):
        """RED: Should return default when env var is None"""
        result = worker_config.parse_workers(None, default_workers=3)
        self.assertEqual(result, 3)

    def test_parse_threads_valid_value(self):
        """RED: Should parse valid GUNICORN_THREADS value"""
        result = worker_config.parse_threads("8")
        self.assertEqual(result, 8)

    def test_parse_threads_invalid_value(self):
        """RED: Should return default 4 for invalid value"""
        result = worker_config.parse_threads("xyz")
        self.assertEqual(result, 4)

    def test_parse_threads_none_value(self):
        """RED: Should return default 4 when None"""
        result = worker_config.parse_threads(None)
        self.assertEqual(result, 4)

    def test_calculate_default_workers(self):
        """RED: Should calculate (2*CPU)+1 workers"""
        expected = (2 * multiprocessing.cpu_count()) + 1
        result = worker_config.calculate_default_workers()
        self.assertEqual(result, expected)

    def test_get_workers_for_preview_environment(self):
        """RED: Should return 1 worker for preview environment"""
        with patch.dict('os.environ', {'ENVIRONMENT': 'preview'}, clear=True):
            result = worker_config.get_workers()
            self.assertEqual(result, 1)

    def test_get_workers_for_production_environment(self):
        """RED: Should return (2*CPU)+1 for non-preview environment"""
        with patch.dict('os.environ', {}, clear=True):
            result = worker_config.get_workers()
            expected = (2 * multiprocessing.cpu_count()) + 1
            self.assertEqual(result, expected)

    def test_get_workers_with_env_var_override(self):
        """RED: Should respect GUNICORN_WORKERS override"""
        with patch.dict('os.environ', {'GUNICORN_WORKERS': '7'}, clear=True):
            result = worker_config.get_workers()
            self.assertEqual(result, 7)

    def test_get_threads_default(self):
        """RED: Should return 4 threads by default"""
        with patch.dict('os.environ', {}, clear=True):
            result = worker_config.get_threads()
            self.assertEqual(result, 4)

    def test_get_threads_with_env_var(self):
        """RED: Should respect GUNICORN_THREADS override"""
        with patch.dict('os.environ', {'GUNICORN_THREADS': '12'}, clear=True):
            result = worker_config.get_threads()
            self.assertEqual(result, 12)


if __name__ == '__main__':
    unittest.main()
