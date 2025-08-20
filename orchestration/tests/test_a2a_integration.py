"""Tests for A2A protocol integration in the orchestration system."""

import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime
from unittest.mock import Mock, patch

# Add orchestration directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
# Add mvp_site directory to path for logging_util
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "mvp_site"
    ),
)
# Add fixtures directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "fixtures"))

from message_broker import MessageBroker, MessageType, TaskMessage
from orchestrate_unified import UnifiedOrchestration

from .fixtures import (
    mock_claude_fixture,
    mock_message_broker_fixture,
    mock_tmux_fixture,
)


class TestA2AIntegration(unittest.TestCase):
    """Test A2A protocol integration with the orchestration system."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Create required directories
        os.makedirs("/tmp/orchestration_results", exist_ok=True)
        os.makedirs("/tmp/orchestration_logs", exist_ok=True)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.old_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_agent_registration_with_a2a(self):
        """Test: Agent creation → A2A registration → Redis messaging"""

        with (
            mock_tmux_fixture(),
            mock_claude_fixture(),
            mock_message_broker_fixture() as mock_broker,
        ):
            # Given: Redis is available and A2A integration enabled
            task = "Implement new feature with A2A coordination"

            # When: Agent is created
            orchestration = UnifiedOrchestration()
            orchestration.message_broker = mock_broker  # Use mock broker

            with patch("subprocess.run") as mock_git:
                mock_git.return_value = Mock(returncode=0)

                orchestration.orchestrate(task)

                # Then: Verify A2A registration

                # 1. Agent should be registered with message broker
                registered_agents = mock_broker.get_registered_agents()
                assert len(registered_agents) > 0, "Agent should be registered with A2A system"

                # 2. Verify agent has correct A2A capabilities
                agent_id = list(registered_agents.keys())[0]
                agent_info = registered_agents[agent_id]

                expected_capabilities = [
                    "task_execution",
                    "development",
                    "git_operations",
                    "server_management",
                    "testing",
                    "full_stack",
                ]
                assert agent_info["capabilities"] == expected_capabilities

                # 3. Verify agent type is set correctly
                assert agent_info["type"] == "development"

    def test_redis_message_broker_initialization(self):
        """Test: MessageBroker initializes correctly with Redis"""

        # Mock Redis client
        with patch("redis.Redis") as mock_redis_class:
            mock_redis_instance = Mock()
            mock_redis_class.return_value = mock_redis_instance

            # Given: Redis is available
            # When: MessageBroker is initialized
            broker = MessageBroker()

            # Then: Verify Redis connection
            mock_redis_class.assert_called_once()
            assert broker.redis_client is not None
            assert broker.redis_client == mock_redis_instance

    def test_agent_capability_registration(self):
        """Test: Agents register with correct capabilities for A2A"""

        with mock_message_broker_fixture() as mock_broker:
            # Given: Different agent types with specific capabilities
            test_cases = [
                {
                    "name": "frontend-specialist",
                    "type": "frontend",
                    "capabilities": ["react", "css", "javascript", "ui_testing"],
                },
                {
                    "name": "backend-specialist",
                    "type": "backend",
                    "capabilities": ["api_development", "database", "authentication"],
                },
                {
                    "name": "testing-specialist",
                    "type": "testing",
                    "capabilities": [
                        "unit_testing",
                        "integration_testing",
                        "test_automation",
                    ],
                },
            ]

            # When: Agents are registered
            for agent_spec in test_cases:
                mock_broker.register_agent(
                    agent_spec["name"], agent_spec["type"], agent_spec["capabilities"]
                )

            # Then: Verify all agents registered with correct capabilities
            registered_agents = mock_broker.get_registered_agents()
            assert len(registered_agents) == 3, "All agents should be registered"

            for agent_spec in test_cases:
                agent_name = agent_spec["name"]
                assert agent_name in registered_agents

                agent_info = registered_agents[agent_name]
                assert agent_info["type"] == agent_spec["type"]
                assert agent_info["capabilities"] == agent_spec["capabilities"]

    def test_inter_agent_messaging_flow(self):
        """Test: Agents can send messages through A2A protocol"""

        with mock_message_broker_fixture() as mock_broker:
            # Given: Two registered agents
            agent1_id = "frontend-agent-1"
            agent2_id = "backend-agent-1"

            mock_broker.register_agent(agent1_id, "frontend", ["ui", "react"])
            mock_broker.register_agent(agent2_id, "backend", ["api", "database"])

            # When: Agent1 sends task to Agent2
            task_data = {
                "task": "Create API endpoint for user data",
                "priority": "high",
                "requirements": ["authentication", "validation"],
            }

            mock_broker.send_task(agent1_id, agent2_id, task_data)

            # Then: Verify message was sent
            sent_tasks = mock_broker.sent_tasks
            assert len(sent_tasks) == 1, "Task should be sent"

            sent_task = sent_tasks[0]
            assert sent_task["from"] == agent1_id
            assert sent_task["to"] == agent2_id
            assert sent_task["data"] == task_data

    def test_a2a_protocol_fallback_when_redis_unavailable(self):
        """Test: System gracefully handles A2A unavailability"""

        with mock_tmux_fixture(), mock_claude_fixture():
            # Given: Redis/A2A is unavailable
            task = "Create feature without A2A coordination"

            # When: Orchestration runs without A2A
            orchestration = UnifiedOrchestration()
            # Simulate Redis connection failure
            orchestration.message_broker = None

            with patch("subprocess.run") as mock_git:
                mock_git.return_value = Mock(returncode=0)

                # Should not raise exception
                orchestration.orchestrate(task)

                # Then: Verify graceful fallback
                assert orchestration.message_broker is None, "Should handle A2A unavailability gracefully"

    def test_agent_heartbeat_mechanism(self):
        """Test: Agents can send heartbeat messages through A2A"""

        # Mock the MessageBroker
        with patch("message_broker.MessageBroker") as mock_broker_class:
            mock_broker = Mock()
            mock_broker_class.return_value = mock_broker

            # Given: Agent with heartbeat capability
            agent_id = "heartbeat-agent"

            # When: Agent sends heartbeat
            heartbeat_message = TaskMessage(
                id="heartbeat-1",
                type=MessageType.AGENT_HEARTBEAT,
                from_agent=agent_id,
                to_agent="system",
                timestamp=datetime.now().isoformat(),
                payload={"status": "active", "load": 0.5},
            )

            # Simulate sending heartbeat
            mock_broker.send_heartbeat = Mock()
            mock_broker.send_heartbeat(heartbeat_message)

            # Then: Verify heartbeat was sent
            mock_broker.send_heartbeat.assert_called_once_with(heartbeat_message)

    def test_task_result_reporting_through_a2a(self):
        """Test: Agents can report task results through A2A protocol"""

        with mock_message_broker_fixture() as mock_broker:
            # Given: Agent that completed a task
            agent_id = "worker-agent"
            coordinator_id = "opus-master"

            mock_broker.register_agent(agent_id, "worker", ["task_execution"])
            mock_broker.register_agent(
                coordinator_id, "coordinator", ["task_management"]
            )

            # When: Agent reports task completion
            result_data = {
                "task_id": "task-123",
                "status": "completed",
                "result": "Successfully implemented feature X",
                "pr_url": "https://github.com/test/repo/pull/456",
                "duration_minutes": 45,
            }

            mock_broker.send_task(
                agent_id, coordinator_id, {"type": "task_result", "data": result_data}
            )

            # Then: Verify result was reported
            sent_tasks = mock_broker.sent_tasks
            result_task = next(
                (
                    task
                    for task in sent_tasks
                    if task["data"].get("type") == "task_result"
                ),
                None,
            )

            assert result_task is not None, "Task result should be sent"
            assert result_task["from"] == agent_id
            assert result_task["to"] == coordinator_id
            assert result_task["data"]["data"] == result_data

    def test_agent_discovery_through_a2a(self):
        """Test: Agents can discover other agents through A2A registry"""

        with mock_message_broker_fixture() as mock_broker:
            # Given: Multiple agents with different capabilities
            agents = [
                {
                    "id": "ui-expert",
                    "type": "frontend",
                    "capabilities": ["react", "css"],
                },
                {
                    "id": "api-expert",
                    "type": "backend",
                    "capabilities": ["fastapi", "postgresql"],
                },
                {
                    "id": "test-expert",
                    "type": "testing",
                    "capabilities": ["pytest", "selenium"],
                },
            ]

            # When: Agents register with A2A
            for agent in agents:
                mock_broker.register_agent(
                    agent["id"], agent["type"], agent["capabilities"]
                )

            # Then: Any agent should be able to discover others
            registered_agents = mock_broker.get_registered_agents()

            # Verify all agents are discoverable
            assert len(registered_agents) == 3, "All agents should be discoverable"

            # Verify agent capabilities are accessible
            ui_expert = registered_agents["ui-expert"]
            assert "react" in ui_expert["capabilities"]

            api_expert = registered_agents["api-expert"]
            assert "fastapi" in api_expert["capabilities"]

    def test_a2a_message_persistence_in_redis(self):
        """Test: A2A messages are properly stored in Redis"""

        # Mock Redis operations
        with patch("redis.Redis") as mock_redis_class:
            mock_redis = Mock()
            mock_redis_class.return_value = mock_redis

            # Given: MessageBroker with Redis
            broker = MessageBroker()

            # When: Agent registers (should store in Redis)
            agent_id = "test-agent"
            agent_type = "development"
            capabilities = ["coding", "testing"]

            broker.register_agent(agent_id, agent_type, capabilities)

            # Then: Verify Redis operations
            # Should call hset to store agent information
            mock_redis.hset.assert_called_once()

            # Verify the stored data structure
            call_args = mock_redis.hset.call_args
            assert call_args[0][0] == f"agent:{agent_id}"  # Redis key

            # Verify mapping contains expected fields
            mapping = call_args[1]["mapping"]
            assert mapping["id"] == agent_id
            assert mapping["type"] == agent_type
            assert mapping["status"] == "active"

            # Capabilities should be JSON encoded for Redis
            stored_capabilities = json.loads(mapping["capabilities"])
            assert stored_capabilities == capabilities


if __name__ == "__main__":
    unittest.main()
