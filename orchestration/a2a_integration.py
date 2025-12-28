#!/usr/bin/env python3
"""
Simplified A2A Integration for WorldArchitect.AI Orchestrator

Lightweight file-based Agent-to-Agent protocol wrapper that enables
direct agent communication while preserving existing tmux orchestration.
"""

import fcntl
import json
import logging
import os
import tempfile
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# Use project logging utility
try:
    import logging_util

    logger = logging_util.getLogger(__name__)
except ImportError:
    # Fallback to basic logging if logging_util not available
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# A2A Communication Directory - configurable for production
A2A_BASE_DIR = os.environ.get("A2A_BASE_DIR", "/tmp/orchestration/a2a")


@dataclass
class A2AMessage:
    """Simple A2A message format for file-based communication"""

    id: str
    from_agent: str
    to_agent: str  # or "broadcast" for all agents
    message_type: str  # discover, claim, delegate, status, result
    payload: dict[str, Any]
    timestamp: float
    reply_to: str | None = None

    def to_json(self) -> str:
        """Serialize to JSON string"""
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "A2AMessage":
        """Deserialize from JSON string"""
        data = json.loads(json_str)
        return cls(**data)


@dataclass
class AgentInfo:
    """Agent capabilities and status information"""

    agent_id: str
    agent_type: str  # frontend, backend, testing, opus-master
    capabilities: list[str]
    status: str  # idle, busy, offline
    current_task: str | None
    created_at: float
    last_heartbeat: float
    workspace: str

    def to_json(self) -> str:
        """Serialize to JSON string"""
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "AgentInfo":
        """Deserialize from JSON string"""
        data = json.loads(json_str)
        return cls(**data)


class FileBasedMessaging:
    """Handles file-based inbox/outbox messaging between agents"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.agent_dir = Path(A2A_BASE_DIR) / "agents" / agent_id
        self.inbox_dir = self.agent_dir / "inbox"
        self.outbox_dir = self.agent_dir / "outbox"

        # Ensure directories exist
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        self.outbox_dir.mkdir(parents=True, exist_ok=True)

    def send_message(self, message: A2AMessage) -> bool:
        """Send message to another agent's inbox"""
        try:
            if message.to_agent == "broadcast":
                return self._broadcast_message(message)
            return self._send_direct_message(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    def _send_direct_message(self, message: A2AMessage) -> bool:
        """Send direct message to specific agent"""
        target_inbox = Path(A2A_BASE_DIR) / "agents" / message.to_agent / "inbox"
        target_inbox.mkdir(parents=True, exist_ok=True)

        filename = f"{message.timestamp}_{message.from_agent}_{message.id}.json"
        filepath = target_inbox / filename

        with open(filepath, "w") as f:
            f.write(message.to_json())

        logger.info(f"Sent message {message.id} to {message.to_agent}")
        return True

    def _broadcast_message(self, message: A2AMessage) -> bool:
        """Broadcast message to all registered agents"""
        agents_dir = Path(A2A_BASE_DIR) / "agents"
        if not agents_dir.exists():
            return False

        success_count = 0
        for agent_dir in agents_dir.iterdir():
            if agent_dir.is_dir() and agent_dir.name != self.agent_id:
                target_message = A2AMessage(
                    id=message.id,
                    from_agent=message.from_agent,
                    to_agent=agent_dir.name,
                    message_type=message.message_type,
                    payload=message.payload,
                    timestamp=message.timestamp,
                    reply_to=message.reply_to,
                )
                if self._send_direct_message(target_message):
                    success_count += 1

        logger.info(f"Broadcast message {message.id} to {success_count} agents")
        return success_count > 0

    def receive_messages(self) -> list[A2AMessage]:
        """Retrieve all messages from inbox"""
        messages = []

        if not self.inbox_dir.exists():
            return messages

        for message_file in self.inbox_dir.glob("*.json"):
            try:
                with open(message_file) as f:
                    message = A2AMessage.from_json(f.read())
                    messages.append(message)

                # Move processed message to prevent re-processing
                processed_dir = self.inbox_dir / "processed"
                processed_dir.mkdir(exist_ok=True)
                message_file.rename(processed_dir / message_file.name)

            except Exception as e:
                logger.error(f"Failed to process message {message_file}: {e}")

        return messages


class AgentRegistry:
    """Manages agent discovery and registration"""

    def __init__(self):
        self.registry_file = Path(A2A_BASE_DIR) / "registry.json"
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)

    def register_agent(self, agent_info: AgentInfo) -> bool:
        """Register an agent in the registry"""
        try:
            registry = self._load_registry()
            registry[agent_info.agent_id] = asdict(agent_info)
            self._save_registry(registry)

            # Also save agent info to its directory
            agent_dir = Path(A2A_BASE_DIR) / "agents" / agent_info.agent_id
            agent_dir.mkdir(parents=True, exist_ok=True)

            with open(agent_dir / "info.json", "w") as f:
                f.write(agent_info.to_json())

            logger.info(f"Registered agent {agent_info.agent_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to register agent: {e}")
            return False

    def unregister_agent(self, agent_id: str) -> bool:
        """Remove agent from registry"""
        try:
            registry = self._load_registry()
            if agent_id in registry:
                del registry[agent_id]
                self._save_registry(registry)
                logger.info(f"Unregistered agent {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to unregister agent: {e}")
            return False

    def discover_agents(self, capability_filter: list[str] | None = None) -> list[AgentInfo]:
        """Discover available agents, optionally filtered by capabilities"""
        try:
            registry = self._load_registry()
            agents = []

            for agent_data in registry.values():
                agent_info = AgentInfo(**agent_data)

                # Filter by capabilities if specified
                if capability_filter and not any(cap in agent_info.capabilities for cap in capability_filter):
                    continue

                # Check if agent is still alive (heartbeat within last 60 seconds)
                if time.time() - agent_info.last_heartbeat < 60:
                    agents.append(agent_info)

            return agents

        except Exception as e:
            logger.error(f"Failed to discover agents: {e}")
            return []

    def update_heartbeat(self, agent_id: str) -> bool:
        """Update agent heartbeat timestamp"""
        try:
            registry = self._load_registry()
            if agent_id in registry:
                registry[agent_id]["last_heartbeat"] = time.time()
                self._save_registry(registry)

                # Also update heartbeat file
                agent_dir = Path(A2A_BASE_DIR) / "agents" / agent_id
                heartbeat_file = agent_dir / "heartbeat.json"
                with open(heartbeat_file, "w") as f:
                    json.dump({"last_heartbeat": time.time()}, f)

            return True
        except Exception as e:
            logger.error(f"Failed to update heartbeat: {e}")
            return False

    def _load_registry(self) -> dict[str, Any]:
        """Load registry from file"""
        if self.registry_file.exists():
            with open(self.registry_file) as f:
                return json.load(f)
        return {}

    def _save_registry(self, registry: dict[str, Any]) -> None:
        """Save registry to file"""
        with open(self.registry_file, "w") as f:
            json.dump(registry, f, indent=2)


class TaskPool:
    """Manages task distribution and claiming"""

    def __init__(self):
        self.tasks_dir = Path(A2A_BASE_DIR) / "tasks"
        self.available_dir = self.tasks_dir / "available"
        self.claimed_dir = self.tasks_dir / "claimed"
        self.completed_dir = self.tasks_dir / "completed"

        # Ensure directories exist
        for dir_path in [self.available_dir, self.claimed_dir, self.completed_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def publish_task(
        self,
        task_id: str,
        task_description: str,
        requirements: list[str] | None = None,
        constraints: dict[str, Any] | None = None,
    ) -> bool:
        """Publish a task to the available pool with optional constraints

        Args:
            task_id: Unique identifier for the task
            task_description: Description of the task to be performed
            requirements: List of capability requirements for agents
            constraints: Optional constraint information for task execution
                        Can include: resource limits, timing constraints,
                        validation rules, execution preferences, etc.
        """
        try:
            task_data = {
                "task_id": task_id,
                "description": task_description,
                "requirements": requirements or [],
                "constraints": constraints or {},
                "constraint_enforcement": {
                    "enabled": bool(constraints),
                    "validation_required": bool(constraints and constraints.get("validation_rules")),
                    "created_at": time.time(),
                },
                "created_at": time.time(),
                "status": "available",
            }

            task_file = self.available_dir / f"{task_id}.json"
            with open(task_file, "w") as f:
                json.dump(task_data, f, indent=2)

            logger.info(f"Published task {task_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish task: {e}")
            return False

    def claim_task(self, task_id: str, agent_id: str, timeout: float = 10.0) -> dict[str, Any]:
        """Claim a task from the available pool and return task data with constraints

        Uses atomic file locking to prevent race conditions when multiple agents
        attempt to claim the same task simultaneously.

        Args:
            task_id: ID of the task to claim
            agent_id: ID of the agent claiming the task
            timeout: Timeout in seconds for lock acquisition (default: 10.0)

        Returns:
            Dict containing task data including constraints, or empty dict if claim failed
        """
        lock_file = None
        lock_fd = None

        try:
            available_file = self.available_dir / f"{task_id}.json"
            if not available_file.exists():
                return {}

            # Create lock file for atomic task claiming
            lock_file = self.available_dir / f"{task_id}.lock"
            lock_fd = os.open(lock_file, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)

            # Attempt to acquire exclusive lock with timeout
            start_time = time.time()
            while True:
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break  # Lock acquired successfully
                except BlockingIOError:
                    if time.time() - start_time >= timeout:
                        logger.warning(f"Lock acquisition timeout for task {task_id} by agent {agent_id}")
                        return {}
                    time.sleep(0.01)  # Short sleep before retry

            # Double-check file still exists after acquiring lock
            if not available_file.exists():
                logger.info(f"Task {task_id} no longer available (claimed by another agent)")
                return {}

            # Load and validate task data
            with open(available_file) as f:
                task_data = json.load(f)

            # Add claiming timestamp for conflict detection
            claim_timestamp = time.time()

            # Check if task was recently claimed (additional safety check)
            if task_data.get("status") == "claimed":
                logger.warning(f"Task {task_id} already claimed by {task_data.get('claimed_by')}")
                return {}

            # Update task status and claimer with atomic timestamp
            task_data["status"] = "claimed"
            task_data["claimed_by"] = agent_id
            task_data["claimed_at"] = claim_timestamp
            task_data["claim_lock_acquired_at"] = claim_timestamp

            # Update constraint enforcement metadata
            if "constraint_enforcement" in task_data:
                task_data["constraint_enforcement"]["claimed_at"] = claim_timestamp
                task_data["constraint_enforcement"]["claimed_by"] = agent_id

            # Atomic move operation: write to temp file first, then move
            claimed_file = self.claimed_dir / f"{task_id}_{agent_id}.json"

            # Use atomic write with temp file
            with tempfile.NamedTemporaryFile(mode="w", dir=self.claimed_dir, suffix=".tmp", delete=False) as temp_file:
                json.dump(task_data, temp_file, indent=2)
                temp_file.flush()
                os.fsync(temp_file.fileno())  # Force write to disk
                temp_path = temp_file.name

            # Atomic move to final location
            os.rename(temp_path, claimed_file)

            # Remove from available directory (atomic operation)
            available_file.unlink()

            logger.info(f"Task {task_id} claimed by {agent_id} with atomic locking")
            if task_data.get("constraints"):
                logger.info(f"Task {task_id} includes constraints: {list(task_data['constraints'].keys())}")

            return task_data

        except OSError as e:
            logger.error(f"File operation failed during task claim for {task_id}: {e}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in task file {task_id}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Failed to claim task {task_id}: {e}")
            return {}
        finally:
            # Always release lock and cleanup
            if lock_fd is not None:
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
                    os.close(lock_fd)
                except OSError:
                    pass  # Ignore cleanup errors

            if lock_file and lock_file.exists():
                try:
                    lock_file.unlink()
                except OSError:
                    pass  # Ignore cleanup errors

    def complete_task(self, task_id: str, agent_id: str, result: dict[str, Any]) -> bool:
        """Mark a task as completed"""
        try:
            claimed_file = self.claimed_dir / f"{task_id}_{agent_id}.json"
            if not claimed_file.exists():
                return False

            # Load task data
            with open(claimed_file) as f:
                task_data = json.load(f)

            # Update task status and result
            task_data["status"] = "completed"
            task_data["completed_at"] = time.time()
            task_data["result"] = result

            # Move to completed directory
            completed_file = self.completed_dir / f"{task_id}_complete.json"
            with open(completed_file, "w") as f:
                json.dump(task_data, f, indent=2)

            # Remove from claimed
            claimed_file.unlink()

            logger.info(f"Task {task_id} completed by {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to complete task: {e}")
            return False

    def get_available_tasks(self, capability_filter: list[str] | None = None) -> list[dict[str, Any]]:
        """Get list of available tasks, optionally filtered by requirements"""
        tasks = []

        for task_file in self.available_dir.glob("*.json"):
            try:
                with open(task_file) as f:
                    task_data = json.load(f)

                # Filter by capabilities if specified
                if capability_filter and task_data.get("requirements"):
                    if not any(req in capability_filter for req in task_data["requirements"]):
                        continue

                tasks.append(task_data)

            except Exception as e:
                logger.error(f"Failed to load task {task_file}: {e}")

        return tasks

    def validate_task_constraints(self, task_data: dict[str, Any], agent_capabilities: list[str]) -> bool:
        """Validate if an agent can handle task constraints

        Args:
            task_data: Complete task data including constraints
            agent_capabilities: List of agent capabilities

        Returns:
            True if agent can handle constraints, False otherwise
        """
        constraints = task_data.get("constraints", {})
        if not constraints:
            return True

        # Check resource constraints
        if "resource_limits" in constraints:
            # Could be extended to check actual resource availability
            pass

        # Check capability constraints
        if "required_capabilities" in constraints:
            required = constraints["required_capabilities"]
            if not all(cap in agent_capabilities for cap in required):
                return False

        # Check timing constraints
        if "deadline" in constraints:
            deadline = constraints["deadline"]
            if isinstance(deadline, int | float) and deadline < time.time():
                return False

        # Check validation rules
        if "validation_rules" in constraints:
            # Could be extended with specific validation logic
            # For now, assume agent can handle if it has validation capability
            if "validation" not in agent_capabilities:
                logger.warning("Task requires validation but agent lacks validation capability")

        return True


class A2AClient:
    """Main A2A client for agent integration"""

    def __init__(self, agent_id: str, agent_type: str, capabilities: list[str], workspace: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.workspace = workspace

        # Initialize components
        self.messaging = FileBasedMessaging(agent_id)
        self.registry = AgentRegistry()
        self.task_pool = TaskPool()

        # Register this agent
        self.agent_info = AgentInfo(
            agent_id=agent_id,
            agent_type=agent_type,
            capabilities=capabilities,
            status="idle",
            current_task=None,
            created_at=time.time(),
            last_heartbeat=time.time(),
            workspace=workspace,
        )
        self.registry.register_agent(self.agent_info)

    def send_message(self, to_agent: str, message_type: str, payload: dict[str, Any]) -> bool:
        """Send message to another agent"""
        message = A2AMessage(
            id=str(uuid.uuid4()),
            from_agent=self.agent_id,
            to_agent=to_agent,
            message_type=message_type,
            payload=payload,
            timestamp=time.time(),
        )
        return self.messaging.send_message(message)

    def receive_messages(self) -> list[A2AMessage]:
        """Receive all pending messages"""
        return self.messaging.receive_messages()

    def discover_agents(self) -> list[AgentInfo]:
        """Discover other available agents"""
        return self.registry.discover_agents()

    def publish_task(
        self,
        task_description: str,
        requirements: list[str] | None = None,
        constraints: dict[str, Any] | None = None,
    ) -> str:
        """Publish a new task with optional constraints

        Args:
            task_description: Description of the task
            requirements: List of capability requirements
            constraints: Optional constraint information for task execution
        """
        task_id = str(uuid.uuid4())
        if self.task_pool.publish_task(task_id, task_description, requirements, constraints):
            return task_id
        return None

    def claim_task(self, task_id: str, timeout: float = 10.0) -> dict[str, Any]:
        """Claim an available task and return task data with constraints

        Args:
            task_id: ID of the task to claim
            timeout: Timeout in seconds for lock acquisition (default: 10.0)

        Returns:
            Dict containing complete task data including constraints,
            or empty dict if claim failed
        """
        return self.task_pool.claim_task(task_id, self.agent_id, timeout)

    def complete_task(self, task_id: str, result: dict[str, Any]) -> bool:
        """Complete a claimed task"""
        return self.task_pool.complete_task(task_id, self.agent_id, result)

    def get_available_tasks(self) -> list[dict[str, Any]]:
        """Get available tasks matching this agent's capabilities"""
        return self.task_pool.get_available_tasks(self.capabilities)

    def get_compatible_tasks(self) -> list[dict[str, Any]]:
        """Get available tasks that are compatible with agent capabilities and constraints

        Returns:
            List of tasks that this agent can handle, including constraint validation
        """
        all_tasks = self.task_pool.get_available_tasks(self.capabilities)
        compatible_tasks = []

        for task in all_tasks:
            if self.task_pool.validate_task_constraints(task, self.capabilities):
                compatible_tasks.append(task)
            else:
                logger.info(f"Task {task.get('task_id')} filtered out due to constraint mismatch")

        return compatible_tasks

    def can_handle_task(self, task_data: dict[str, Any]) -> bool:
        """Check if this agent can handle a specific task including constraints

        Args:
            task_data: Complete task data including constraints

        Returns:
            True if agent can handle the task, False otherwise
        """
        return self.task_pool.validate_task_constraints(task_data, self.capabilities)

    def update_status(self, status: str, current_task: str = None) -> None:
        """Update agent status"""
        self.agent_info.status = status
        self.agent_info.current_task = current_task
        self.agent_info.last_heartbeat = time.time()
        self.registry.register_agent(self.agent_info)

    def heartbeat(self) -> None:
        """Send heartbeat to maintain registration"""
        self.registry.update_heartbeat(self.agent_id)

    def shutdown(self) -> None:
        """Clean shutdown - unregister agent"""
        self.registry.unregister_agent(self.agent_id)


# Utility functions for orchestration integration
def create_a2a_client(agent_id: str, agent_type: str, capabilities: list[str], workspace: str) -> A2AClient:
    """Factory function to create A2A client for agents"""
    return A2AClient(agent_id, agent_type, capabilities, workspace)


def get_a2a_status() -> dict[str, Any]:
    """Get overall A2A system status"""
    registry = AgentRegistry()
    task_pool = TaskPool()

    agents = registry.discover_agents()
    available_tasks = task_pool.get_available_tasks()

    return {
        "agents_online": len(agents),
        "available_tasks": len(available_tasks),
        "a2a_directory": A2A_BASE_DIR,
        "agents": [asdict(agent) for agent in agents],
        "tasks": available_tasks,
    }


if __name__ == "__main__":
    # Test the A2A system
    import shutil
    import tempfile

    # Use temp directory for testing
    test_dir = tempfile.mkdtemp()
    A2A_BASE_DIR = test_dir + "/a2a"

    try:
        # Create secure temporary directories for test agents
        agent1_workspace = tempfile.mkdtemp(prefix="agent1_")
        agent2_workspace = tempfile.mkdtemp(prefix="agent2_")

        # Create test agents with secure temporary workspaces
        agent1 = create_a2a_client(
            "agent-1",
            "frontend",
            ["javascript", "react", "validation"],
            agent1_workspace,
        )
        agent2 = create_a2a_client("agent-2", "backend", ["python", "api"], agent2_workspace)

        # Test task publishing with constraints
        constraints = {
            "resource_limits": {"memory_mb": 512, "timeout_seconds": 300},
            "required_capabilities": ["javascript"],
            "deadline": time.time() + 3600,  # 1 hour from now
            "validation_rules": {"code_review": True, "testing": True},
        }
        task_id = agent1.publish_task("Build login form with constraints", ["javascript"], constraints)
        print(f"Published task with constraints: {task_id}")

        # Test basic task publishing (backward compatibility)
        simple_task_id = agent1.publish_task("Simple task", ["python"])
        print(f"Published simple task: {simple_task_id}")

        # Agent 2 discovers tasks
        tasks = agent2.get_available_tasks()
        print(f"Available tasks: {len(tasks)}")

        # Test constraint compatibility
        compatible_tasks = agent2.get_compatible_tasks()
        print(f"Compatible tasks for agent2: {len(compatible_tasks)}")

        # Test task claiming with constraint information
        if compatible_tasks:
            claimed_task = agent2.claim_task(compatible_tasks[0]["task_id"])
            if claimed_task:
                print(f"Claimed task: {claimed_task.get('task_id')}")
                print(f"Task constraints: {claimed_task.get('constraints', {})}")
                print(f"Constraint enforcement: {claimed_task.get('constraint_enforcement', {})}")

        # Test messaging
        agent1.send_message("agent-2", "status", {"message": "Hello from agent 1"})
        messages = agent2.receive_messages()
        print(f"Agent 2 received {len(messages)} messages")

        # Get system status
        status = get_a2a_status()
        print(f"System status: {status}")
        print(f"Tasks with constraints: {sum(1 for task in status['tasks'] if task.get('constraints'))}")

    finally:
        # Cleanup test directories and agent workspaces
        shutil.rmtree(test_dir, ignore_errors=True)
        # Clean up agent workspaces if they exist
        try:
            shutil.rmtree(agent1_workspace, ignore_errors=True)
            shutil.rmtree(agent2_workspace, ignore_errors=True)
        except NameError:
            # Variables not defined if creation failed
            pass
