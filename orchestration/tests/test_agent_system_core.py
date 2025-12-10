"""Regression coverage for AgentBase heartbeat handling."""

import time

from orchestration.agent_system import AgentBase
from orchestration.message_broker import MessageBroker


class RecordingBroker(MessageBroker):
    """Broker that captures heartbeat payloads for assertions."""

    def __init__(self):
        super().__init__()
        self.heartbeats: list[tuple[str, dict | None]] = []

    def heartbeat(self, agent_id: str, health_data: dict | None = None) -> bool:
        self.heartbeats.append((agent_id, health_data))
        return super().heartbeat(agent_id, health_data)


class PassiveAgent(AgentBase):
    """Agent variant that avoids background threads for deterministic tests."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("enable_a2a", False)
        super().__init__(*args, **kwargs)
        self.start_time = time.time()

    def _process_messages(self):  # pragma: no cover - disabled for tests
        self.running = False


def test_collects_structured_health_data():
    broker = RecordingBroker()
    broker.register_agent("agent-1", "worker", ["coding"])

    agent = PassiveAgent(
        "agent-1",
        "worker",
        broker,
        capabilities=["coding"],
        heartbeat_interval=0.01,
        error_retry_interval=0.01,
    )

    payload = agent._collect_health_data()

    assert payload["agent_id"] == "agent-1"
    assert payload["status"] == "healthy"
    assert payload["capabilities"] == ["coding"]


def test_heartbeat_tick_pushes_health_payload():
    broker = RecordingBroker()
    broker.register_agent("agent-2", "worker", ["analysis"])

    agent = PassiveAgent(
        "agent-2",
        "worker",
        broker,
        capabilities=["analysis"],
        heartbeat_interval=0.01,
        error_retry_interval=0.01,
    )

    assert agent._heartbeat_tick() is True
    assert broker.heartbeats, "heartbeat should be recorded"

    recorded_id, payload = broker.heartbeats[0]
    assert recorded_id == "agent-2"
    assert payload["agent_id"] == "agent-2"
    assert payload["status"] == "healthy"
