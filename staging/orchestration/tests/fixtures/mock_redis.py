"""Mock fixtures for Redis operations in orchestration tests."""

import fnmatch
import json
from contextlib import contextmanager
from datetime import datetime
from unittest.mock import patch


class MockRedisClient:
    """Mock Redis client for testing."""

    def __init__(self):
        self.data = {}  # Simulate Redis key-value store
        self.hashes = {}  # Simulate Redis hashes
        self.call_history = []
        self.connection_fails = False

    def set_connection_failure(self, should_fail=True):
        """Configure mock to simulate connection failures."""
        self.connection_fails = should_fail

    def _check_connection(self):
        """Check if connection should fail."""
        if self.connection_fails:
            raise ConnectionError("Redis connection failed")

    def hset(self, name, key=None, value=None, mapping=None):
        """Mock Redis HSET command."""
        self._check_connection()
        self.call_history.append(("hset", name, key, value, mapping))

        if name not in self.hashes:
            self.hashes[name] = {}

        if mapping:
            self.hashes[name].update(mapping)
        elif key and value:
            self.hashes[name][key] = value

        return 1

    def hget(self, name, key):
        """Mock Redis HGET command."""
        self._check_connection()
        self.call_history.append(("hget", name, key))

        return self.hashes.get(name, {}).get(key)

    def hgetall(self, name):
        """Mock Redis HGETALL command."""
        self._check_connection()
        self.call_history.append(("hgetall", name))

        return self.hashes.get(name, {})

    def publish(self, channel, message):
        """Mock Redis PUBLISH command."""
        self._check_connection()
        self.call_history.append(("publish", channel, message))
        return 1

    def get(self, key):
        """Mock Redis GET command."""
        self._check_connection()
        self.call_history.append(("get", key))
        return self.data.get(key)

    def set(self, key, value):
        """Mock Redis SET command."""
        self._check_connection()
        self.call_history.append(("set", key, value))
        self.data[key] = value
        return True

    def keys(self, pattern="*"):
        """Mock Redis KEYS command."""
        self._check_connection()
        self.call_history.append(("keys", pattern))

        if pattern == "*":
            return list(self.data.keys()) + list(self.hashes.keys())

        # Simple pattern matching

        all_keys = list(self.data.keys()) + list(self.hashes.keys())
        return [key for key in all_keys if fnmatch.fnmatch(key, pattern)]

    def pubsub(self):
        """Mock Redis pubsub."""
        return MockRedisPubSub()

    def get_agent_data(self, agent_id):
        """Helper to get agent data from mock."""
        return self.hashes.get(f"agent:{agent_id}", {})

    def assert_agent_registered(self, agent_id, agent_type=None, capabilities=None):
        """Assert that an agent was registered."""
        agent_key = f"agent:{agent_id}"
        assert agent_key in self.hashes, f"Agent {agent_id} not registered"

        agent_data = self.hashes[agent_key]

        if agent_type:
            assert agent_data.get("type") == agent_type, (
                f"Agent type mismatch: expected {agent_type}, got {agent_data.get('type')}"
            )

        if capabilities:
            stored_capabilities = json.loads(agent_data.get("capabilities", "[]"))
            assert stored_capabilities == capabilities, (
                f"Capabilities mismatch: expected {capabilities}, got {stored_capabilities}"
            )


class MockRedisPubSub:
    """Mock Redis PubSub for testing."""

    def __init__(self):
        self.subscriptions = []
        self.messages = []

    def subscribe(self, *channels):
        """Mock subscribe."""
        self.subscriptions.extend(channels)

    def get_message(self, timeout=None):
        """Mock get_message."""
        if self.messages:
            return self.messages.pop(0)
        return None

    def close(self):
        """Mock close."""


class MockMessageBroker:
    """Mock MessageBroker for testing."""

    def __init__(self, should_fail=False):
        self.should_fail = should_fail
        self.registered_agents = {}
        self.sent_tasks = []

        if should_fail:
            raise ConnectionError("Redis connection failed")

        self.redis_client = MockRedisClient()

    def register_agent(self, agent_id, agent_type, capabilities):
        """Mock agent registration."""
        self.registered_agents[agent_id] = {
            "type": agent_type,
            "capabilities": capabilities,
            "registered_at": datetime.now().isoformat(),
        }

        # Also register with mock Redis
        self.redis_client.hset(
            f"agent:{agent_id}",
            mapping={
                "id": agent_id,
                "type": agent_type,
                "capabilities": json.dumps(capabilities),
                "status": "active",
                "last_heartbeat": datetime.now().isoformat(),
            },
        )

    def send_task(self, from_agent, to_agent, task_data):
        """Mock task sending."""
        self.sent_tasks.append(
            {
                "from": from_agent,
                "to": to_agent,
                "data": task_data,
                "sent_at": datetime.now().isoformat(),
            }
        )

    def get_registered_agents(self):
        """Get all registered agents."""
        return self.registered_agents

    def assert_agent_registered(self, agent_id):
        """Assert that an agent was registered."""
        assert agent_id in self.registered_agents, f"Agent {agent_id} not registered"


@contextmanager
def mock_redis_fixture(should_fail=False):
    """Fixture that provides a mock Redis environment."""
    mock_redis = MockRedisClient()

    if should_fail:
        mock_redis.set_connection_failure(True)

    def mock_redis_constructor(*args, **kwargs):
        if should_fail:
            raise ConnectionError("Redis connection failed")
        return mock_redis

    with patch("redis.Redis", side_effect=mock_redis_constructor):
        yield mock_redis


@contextmanager
def mock_message_broker_fixture(should_fail=False):
    """Fixture that provides a mock MessageBroker."""
    try:
        mock_broker = MockMessageBroker(should_fail=should_fail)
        yield mock_broker
    except ConnectionError:
        yield None
