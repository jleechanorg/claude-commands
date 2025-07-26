#!/usr/bin/env python3
"""
Simple Redis-based message broker for multi-terminal agent orchestration.
"""

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import redis


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
    """Redis-based message broker for agent communication."""

    def __init__(self, redis_host="localhost", redis_port=6379, redis_password=None):
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            decode_responses=True,
        )
        self.pubsub = self.redis_client.pubsub()
        self.agent_registry = {}
        self.running = False

    def start(self):
        """Start the message broker."""
        self.running = True
        print("Message broker started")

    def stop(self):
        """Stop the message broker."""
        self.running = False
        self.pubsub.close()
        print("Message broker stopped")

    def register_agent(self, agent_id: str, agent_type: str, capabilities: list[str]):
        """Register an agent in the system."""
        agent_info = {
            "id": agent_id,
            "type": agent_type,
            "capabilities": json.dumps(capabilities),  # JSON encode list for Redis
            "status": "active",
            "last_heartbeat": datetime.now().isoformat(),
        }

        self.redis_client.hset(f"agent:{agent_id}", mapping=agent_info)
        # Store original list in local registry
        self.agent_registry[agent_id] = {
            **agent_info,
            "capabilities": capabilities  # Keep as list in memory
        }
        print(f"Agent {agent_id} registered with type {agent_type}")

    def send_task(self, from_agent: str, to_agent: str, task_data: dict[str, Any]):
        """Send a task to another agent."""
        message = TaskMessage(
            id=str(uuid.uuid4()),
            type=MessageType.TASK_ASSIGNMENT,
            from_agent=from_agent,
            to_agent=to_agent,
            timestamp=datetime.now().isoformat(),
            payload=task_data,
        )

        # Add to agent's task queue
        self.redis_client.lpush(f"queue:{to_agent}", json.dumps(asdict(message)))
        print(f"Task sent from {from_agent} to {to_agent}")

    def get_task(self, agent_id: str) -> TaskMessage | None:
        """Get a task for an agent."""
        task_data = self.redis_client.rpop(f"queue:{agent_id}")
        if task_data:
            task_dict = json.loads(task_data)
            return TaskMessage(**task_dict)
        return None

    def send_result(self, from_agent: str, to_agent: str, result_data: dict[str, Any]):
        """Send task result back to requesting agent."""
        message = TaskMessage(
            id=str(uuid.uuid4()),
            type=MessageType.TASK_RESULT,
            from_agent=from_agent,
            to_agent=to_agent,
            timestamp=datetime.now().isoformat(),
            payload=result_data,
        )

        self.redis_client.lpush(f"queue:{to_agent}", json.dumps(asdict(message)))
        print(f"Result sent from {from_agent} to {to_agent}")

    def heartbeat(self, agent_id: str):
        """Send heartbeat for an agent."""
        self.redis_client.hset(
            f"agent:{agent_id}", "last_heartbeat", datetime.now().isoformat()
        )

    def get_active_agents(self) -> list[str]:
        """Get list of active agents."""
        agents = []
        for key in self.redis_client.scan_iter("agent:*"):
            agent_id = key.split(":", 1)[1]
            agent_info = self.redis_client.hgetall(key)
            if agent_info.get("status") == "active":
                agents.append(agent_id)
        return agents

    def cleanup_stale_agents(self, timeout_seconds: int = 300):
        """Remove agents that haven't sent heartbeat recently."""
        current_time = datetime.now()
        for agent_id in list(self.agent_registry.keys()):
            last_heartbeat = self.redis_client.hget(
                f"agent:{agent_id}", "last_heartbeat"
            )
            if last_heartbeat:
                heartbeat_time = datetime.fromisoformat(last_heartbeat)
                if (current_time - heartbeat_time).seconds > timeout_seconds:
                    self.redis_client.delete(f"agent:{agent_id}")
                    self.redis_client.delete(f"queue:{agent_id}")
                    del self.agent_registry[agent_id]
                    print(f"Cleaned up stale agent: {agent_id}")
