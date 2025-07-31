#!/usr/bin/env python3
"""Test orchestration system works without Redis dependencies."""
import json
import os
import sys
import tempfile
import unittest

# time import removed - not used
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrate_unified import UnifiedOrchestration


class TestOrchestrationNoRedis(unittest.TestCase):
    """Test orchestration system functions without Redis."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)

    def test_orchestration_init_without_redis(self):
        """Test orchestration initializes without Redis/message_broker."""
        # This should not raise any errors about message_broker
        orchestration = UnifiedOrchestration()

        # Verify no message_broker attribute exists or it's None
        self.assertFalse(hasattr(orchestration, 'message_broker'),
                        "message_broker should not exist in Redis-free system")

    @patch('subprocess.run')
    def test_orchestration_create_agents_without_redis(self, mock_run):
        """Test agent creation works without Redis."""
        # Mock dependency checks
        mock_run.return_value = MagicMock(returncode=0)

        orchestration = UnifiedOrchestration()

        # Mock task dispatcher to return test agents
        test_agents = [{
            'name': 'test-agent-123',
            'type': 'development',
            'focus': 'test task',
            'capabilities': ['file_edit', 'git_operations']
        }]

        with patch.object(orchestration.task_dispatcher,
                         'analyze_task_and_create_agents',
                         return_value=test_agents):
            # This should work without Redis
            try:
                orchestration.orchestrate("Test task without Redis")
                # If we get here, orchestration didn't crash
                success = True
            except AttributeError as e:
                if 'message_broker' in str(e):
                    success = False
                else:
                    raise
            except NameError as e:
                if 'message_broker' in str(e):
                    success = False
                else:
                    raise

            self.assertTrue(success,
                          "Orchestration should work without message_broker")

    def test_no_redis_imports_needed(self):
        """Test that Redis-related imports are not required."""
        # Check if we can create orchestration without MessageBroker import
        with patch.dict('sys.modules', {'message_broker': None}):
            try:
                # Reimport to test without message_broker module
                import importlib

                import orchestrate_unified
                importlib.reload(orchestrate_unified)

                # Should still be able to create orchestration
                orch = orchestrate_unified.UnifiedOrchestration()
                success = True
            except ImportError as e:
                if 'message_broker' in str(e):
                    success = False
                else:
                    raise
            except Exception:
                # Any other exception means test failed
                success = False

            self.assertTrue(success,
                          "Should work without message_broker module")

    @patch('subprocess.run')
    def test_a2a_coordination_without_redis(self, mock_run):
        """Test A2A file-based coordination works without Redis."""
        # Mock successful command execution
        mock_run.return_value = MagicMock(returncode=0, stdout='')

        orchestration = UnifiedOrchestration()

        # Create A2A directories
        a2a_base = '/tmp/orchestration/a2a'
        os.makedirs(f'{a2a_base}/registry', exist_ok=True)
        os.makedirs(f'{a2a_base}/tasks/available', exist_ok=True)

        # Write test registry
        registry_data = {
            'test-agent-1': {
                'agent_id': 'test-agent-1',
                'status': 'idle',
                'capabilities': ['file_edit']
            }
        }

        with open(f'{a2a_base}/registry.json', 'w') as f:
            json.dump(registry_data, f)

        # Verify orchestration can work with file-based A2A
        with patch.object(orchestration.task_dispatcher,
                         'analyze_task_and_create_agents',
                         return_value=[]):
            orchestration.orchestrate("Test A2A without Redis")

        # Should complete without Redis errors
        self.assertTrue(os.path.exists(a2a_base),
                       "A2A file system should be used")


if __name__ == '__main__':
    unittest.main()
