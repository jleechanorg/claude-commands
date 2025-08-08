#!/usr/bin/env python3
"""
File-based message broker stub for agent orchestration.
Maintains interface compatibility but operates without Redis.
All coordination now handled via file-based A2A protocol.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class MessageType(Enum):
    TASK_ASSIGNMENT = "task_assignment"
    TASK_RESULT = "task_result"
    AGENT_HEARTBEAT = "agent_heartbeat"
    AGENT_REGISTER = "agent_register"
    AGENT_SHUTDOWN = "agent_shutdown"


@dataclass
class TaskMessage:
    """Task message structure."""

    id: str
    type: MessageType
    from_agent: str
    to_agent: str
    timestamp: str
    payload: dict[str, Any]
    retry_count: int = 0


class MessageBroker:
    """File-based message broker stub - maintains interface without Redis."""

    def __init__(self, _redis_host="localhost", _redis_port=6379, _redis_password=None):
        # Redis parameters ignored - file-based coordination only
        self.agent_registry = {}
        self.running = False
        print("📁 File-based MessageBroker initialized (Redis functionality removed)")

    def start(self):
        """Start the message broker."""
        self.running = True
        print("📁 File-based message broker started")

    def stop(self):
        """Stop the message broker."""
        self.running = False
        print("📁 File-based message broker stopped")

    def register_agent(self, agent_id: str, agent_type: str, capabilities: list[str]):
        """Register an agent in the system (file-based tracking only)."""
        agent_info = {
            "id": agent_id,
            "type": agent_type,
            "capabilities": capabilities,
            "status": "active",
            "last_heartbeat": datetime.now().isoformat(),
        }

        self.agent_registry[agent_id] = agent_info
        print(f"📁 Agent {agent_id} registered with type {agent_type} (file-based)")

    def send_task(self, from_agent: str, to_agent: str, task_data: dict[str, Any]):
        """Send a task to another agent (no-op in file-based mode)."""
        print(f"📁 Task coordination via A2A files: {from_agent} -> {to_agent}")

    def get_task(self, agent_id: str) -> TaskMessage | None:
        """Get a task for an agent (no-op in file-based mode)."""
        return None

    def send_result(self, from_agent: str, to_agent: str, result_data: dict[str, Any]):
        """Send task result back to requesting agent (no-op in file-based mode)."""
        print(f"📁 Result coordination via A2A files: {from_agent} -> {to_agent}")

    def heartbeat(self, agent_id: str):
        """Send heartbeat for an agent (file-based tracking only)."""
        if agent_id in self.agent_registry:
            self.agent_registry[agent_id]["last_heartbeat"] = datetime.now().isoformat()

    def get_active_agents(self) -> list[str]:
        """Get list of active agents (from file-based registry only)."""
        return list(self.agent_registry.keys())

    def cleanup_stale_agents(self, timeout_seconds: int = 300):
        """Remove agents that haven't sent heartbeat recently (file-based only)."""
        current_time = datetime.now()
        stale_agents = []

        for agent_id, agent_info in self.agent_registry.items():
            last_heartbeat = agent_info.get("last_heartbeat")
            if last_heartbeat:
                heartbeat_time = datetime.fromisoformat(last_heartbeat)
                if (current_time - heartbeat_time).seconds > timeout_seconds:
                    stale_agents.append(agent_id)

        for agent_id in stale_agents:
            del self.agent_registry[agent_id]
            print(f"📁 Cleaned up stale agent: {agent_id}")
