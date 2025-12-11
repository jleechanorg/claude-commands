"""Core orchestration data structures and helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


def iso_now() -> str:
    """Return the current timestamp in ISO format."""
    return datetime.now().isoformat()


@dataclass
class AgentRegistration:
    """Lightweight record of an agent's identity and status."""

    agent_id: str
    agent_type: str
    capabilities: list[str]
    status: str = "active"
    last_heartbeat: str = field(default_factory=iso_now)
    health: dict[str, Any] | None = None

    def touch(self, health: dict[str, Any] | None = None) -> None:
        """Refresh the heartbeat timestamp and optional health snapshot."""
        self.last_heartbeat = iso_now()
        if health is not None:
            self.health = health
            self.status = health.get("status", self.status)

    def as_dict(self) -> dict[str, Any]:
        """Convert to a serializable dictionary for debugging or display."""
        return {
            "id": self.agent_id,
            "type": self.agent_type,
            "capabilities": list(self.capabilities),
            "status": self.status,
            "last_heartbeat": self.last_heartbeat,
            "health": self.health,
        }
