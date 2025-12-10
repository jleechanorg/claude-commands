from datetime import datetime, timedelta

from orchestration.message_broker import MessageBroker


def test_heartbeat_updates_timestamp_and_returns_true():
    broker = MessageBroker()
    broker.register_agent("agent-1", "worker", ["x"])

    first_heartbeat = datetime.fromisoformat(broker.agent_registry["agent-1"].last_heartbeat)
    # Ensure measurable delta
    later = first_heartbeat + timedelta(seconds=1)
    broker.agent_registry["agent-1"].last_heartbeat = later.isoformat()

    result = broker.heartbeat("agent-1")

    assert result is True
    updated = datetime.fromisoformat(broker.agent_registry["agent-1"].last_heartbeat)
    assert updated != later


def test_heartbeat_returns_false_for_unknown_agents():
    broker = MessageBroker()
    broker.register_agent("known", "worker", [])

    assert broker.heartbeat("missing") is False
    assert set(broker.agent_registry) == {"known"}


def test_cleanup_removes_stale_agents():
    broker = MessageBroker()
    broker.register_agent("stale", "worker", [])
    broker.register_agent("fresh", "worker", [])

    stale_time = datetime.now() - timedelta(minutes=10)
    broker.agent_registry["stale"].last_heartbeat = stale_time.isoformat()

    broker.cleanup_stale_agents(timeout_seconds=60)

    assert "stale" not in broker.agent_registry
    assert "fresh" in broker.agent_registry


def test_heartbeat_persists_health_snapshot():
    broker = MessageBroker()
    broker.register_agent("agent-h", "worker", ["monitor"])

    health = {"status": "healthy", "uptime": 1.2, "capabilities": ["monitor"]}

    assert broker.heartbeat("agent-h", health) is True
    registration = broker.agent_registry["agent-h"]

    assert registration.health == health
    assert registration.status == "healthy"
