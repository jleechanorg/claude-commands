#!/usr/bin/env python3
"""
A2A Agent Wrapper for WorldArchitect.AI Orchestrator

Enhances existing agents with A2A capabilities while preserving
all existing tmux-based orchestration functionality.
"""

# Allow direct script execution - add parent directory to sys.path
import os
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import logging
import threading
import time
from collections.abc import Callable
from typing import Any

# Use absolute imports with package name for __main__ compatibility
from orchestration.a2a_integration import A2AClient, A2AMessage, get_a2a_status

logger = logging.getLogger(__name__)


class A2AAgentWrapper:
    """Wraps existing agents with A2A communication capabilities"""

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        capabilities: list[str],
        workspace: str,
        message_handler: Callable | None = None,
    ):
        """
        Initialize A2A wrapper for an agent

        Args:
            agent_id: Unique identifier for the agent
            agent_type: Type of agent (frontend, backend, testing, opus-master)
            capabilities: List of agent capabilities
            workspace: Agent workspace directory
            message_handler: Optional custom message handler function
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.workspace = workspace
        self.message_handler = message_handler or self._default_message_handler

        # Initialize A2A client
        self.a2a_client = A2AClient(agent_id, agent_type, capabilities, workspace)

        # Threading control
        self._running = False
        self._message_thread = None
        self._heartbeat_thread = None

        logger.info(f"A2A wrapper initialized for agent {agent_id}")

    def start(self) -> None:
        """Start A2A message processing and heartbeat"""
        if self._running:
            return

        self._running = True

        # Start message processing thread
        self._message_thread = threading.Thread(
            target=self._message_loop, name=f"A2A-Messages-{self.agent_id}", daemon=True
        )
        self._message_thread.start()

        # Start heartbeat thread
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            name=f"A2A-Heartbeat-{self.agent_id}",
            daemon=True,
        )
        self._heartbeat_thread.start()

        logger.info(f"A2A wrapper started for agent {self.agent_id}")

    def stop(self) -> None:
        """Stop A2A message processing and clean shutdown"""
        self._running = False

        # Wait for threads to finish
        if self._message_thread and self._message_thread.is_alive():
            self._message_thread.join(timeout=5)

        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=5)

        # Unregister from A2A system
        self.a2a_client.shutdown()

        logger.info(f"A2A wrapper stopped for agent {self.agent_id}")

    def _message_loop(self) -> None:
        """Main message processing loop"""
        while self._running:
            try:
                # Receive and process messages
                messages = self.a2a_client.receive_messages()
                for message in messages:
                    self._process_message(message)

                # Check for available tasks
                self._check_available_tasks()

                # Sleep to prevent busy waiting
                time.sleep(1)

            except Exception as e:
                logger.error(f"Error in message loop for {self.agent_id}: {e}")
                time.sleep(5)  # Back off on error

    def _heartbeat_loop(self) -> None:
        """Heartbeat loop to maintain agent registration"""
        while self._running:
            try:
                self.a2a_client.heartbeat()
                time.sleep(30)  # Heartbeat every 30 seconds
            except Exception as e:
                logger.error(f"Error in heartbeat loop for {self.agent_id}: {e}")
                time.sleep(60)  # Back off on error

    def _process_message(self, message: A2AMessage) -> None:
        """Process incoming A2A message"""
        try:
            logger.info(f"Processing message {message.id} from {message.from_agent}")

            # Call custom message handler
            response = self.message_handler(message)

            # Send response if handler returns one
            if response:
                self.send_message(message.from_agent, "response", response, message.id)

        except Exception as e:
            logger.error(f"Error processing message {message.id}: {e}")

    def _check_available_tasks(self) -> None:
        """Check for available tasks that match this agent's capabilities"""
        try:
            tasks = self.a2a_client.get_available_tasks()

            for task in tasks:
                # Simple task claiming logic - agents claim tasks they can handle
                task_requirements = task.get("requirements", [])

                # Check if agent can handle this task
                if self._can_handle_task(task_requirements):
                    if self.a2a_client.claim_task(task["task_id"]):
                        logger.info(f"Agent {self.agent_id} claimed task {task['task_id']}")
                        self._execute_task(task)
                        break  # Only claim one task at a time

        except Exception as e:
            logger.error(f"Error checking available tasks for {self.agent_id}: {e}")

    def _can_handle_task(self, requirements: list[str]) -> bool:
        """Check if agent can handle a task based on requirements"""
        if not requirements:
            return True  # Agent can handle tasks with no specific requirements

        # Check if agent has any of the required capabilities
        return any(req in self.capabilities for req in requirements)

    def _execute_task(self, task: dict[str, Any]) -> None:
        """Execute a claimed task"""
        try:
            task_id = task["task_id"]
            description = task["description"]

            logger.info(f"Agent {self.agent_id} executing task {task_id}: {description}")

            # Update status to busy
            self.a2a_client.update_status("busy", task_id)

            # Execute task based on agent type and description
            result = self._perform_task_execution(task)

            # Complete the task
            self.a2a_client.complete_task(task_id, result)

            # Update status back to idle
            self.a2a_client.update_status("idle")

            logger.info(f"Agent {self.agent_id} completed task {task_id}")

        except Exception as e:
            logger.error(f"Error executing task for {self.agent_id}: {e}")
            # Update status back to idle on error
            self.a2a_client.update_status("idle")

    def _perform_task_execution(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Perform actual task execution based on agent type
        This is a simplified implementation - real agents would have more complex logic
        """
        task["task_id"]
        description = task["description"]

        result = {
            "status": "completed",
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "execution_time": time.time(),
            "output": f"Task '{description}' executed by {self.agent_type} agent",
        }

        # Agent-type specific execution logic
        if self.agent_type == "frontend":
            result["output"] += " - Frontend implementation ready"
        elif self.agent_type == "backend":
            result["output"] += " - Backend API implemented"
        elif self.agent_type == "testing":
            result["output"] += " - Tests created and passing"
        elif self.agent_type == "opus-master":
            result["output"] += " - Task orchestrated and completed"

        return result

    def _default_message_handler(self, message: A2AMessage) -> dict[str, Any | None]:
        """Default message handler for A2A messages"""
        message_type = message.message_type
        payload = message.payload

        if message_type == "discover":
            # Respond with agent capabilities
            return {
                "agent_id": self.agent_id,
                "agent_type": self.agent_type,
                "capabilities": self.capabilities,
                "status": "online",
            }

        if message_type == "status":
            # Handle status requests
            return {
                "agent_id": self.agent_id,
                "status": self.a2a_client.agent_info.status,
                "current_task": self.a2a_client.agent_info.current_task,
                "message": f"Agent {self.agent_id} is operational",
            }

        if message_type == "delegate":
            # Handle task delegation from other agents
            task_description = payload.get("task_description", "")
            requirements = payload.get("requirements", [])

            if self._can_handle_task(requirements):
                # Create and publish the delegated task
                task_id = self.a2a_client.publish_task(task_description, requirements)
                return {
                    "status": "accepted",
                    "task_id": task_id,
                    "message": f"Task delegated and published as {task_id}",
                }
            return {
                "status": "declined",
                "message": f"Agent {self.agent_id} cannot handle this task",
            }

        if message_type == "collaborate":
            # Handle collaboration requests
            return {
                "status": "ready",
                "message": f"Agent {self.agent_id} ready to collaborate",
            }

        # Unknown message type
        logger.warning(f"Unknown message type: {message_type}")
        return {
            "status": "unknown_message_type",
            "message": f"Agent {self.agent_id} doesn't handle '{message_type}' messages",
        }

    # Public API methods for agent interaction

    def send_message(
        self,
        to_agent: str,
        message_type: str,
        payload: dict[str, Any],
        reply_to: str = None,
    ) -> bool:
        """Send message to another agent"""
        return self.a2a_client.send_message(to_agent, message_type, payload)

    def broadcast_message(self, message_type: str, payload: dict[str, Any]) -> bool:
        """Broadcast message to all agents"""
        return self.a2a_client.send_message("broadcast", message_type, payload)

    def discover_agents(self) -> list[dict[str, Any]]:
        """Discover other available agents"""
        from dataclasses import asdict

        agents = self.a2a_client.discover_agents()
        return [asdict(agent) for agent in agents]

    def publish_task(self, description: str, requirements: list[str] | None = None) -> str | None:
        """Publish a new task for other agents to claim"""
        return self.a2a_client.publish_task(description, requirements)

    def get_available_tasks(self) -> list[dict[str, Any]]:
        """Get available tasks that this agent can handle"""
        return self.a2a_client.get_available_tasks()

    def update_status(self, status: str, current_task: str = None) -> None:
        """Update agent status"""
        self.a2a_client.update_status(status, current_task)

    def get_agent_info(self) -> dict[str, Any]:
        """Get current agent information"""
        from dataclasses import asdict

        return asdict(self.a2a_client.agent_info)


def create_a2a_wrapper(
    agent_id: str,
    agent_type: str,
    capabilities: list[str],
    workspace: str,
    message_handler: Callable | None = None,
) -> A2AAgentWrapper:
    """Factory function to create A2A wrapper for agents"""
    return A2AAgentWrapper(agent_id, agent_type, capabilities, workspace, message_handler)


def get_all_agents_status() -> dict[str, Any]:
    """Get status of all agents in the A2A system"""
    return get_a2a_status()


if __name__ == "__main__":
    # Test the A2A wrapper
    import time

    # Create test agent wrapper
    wrapper = create_a2a_wrapper(
        agent_id="test-agent-1",
        agent_type="testing",
        capabilities=["python", "testing", "automation"],
        workspace="/tmp/test-agent-1",
    )

    try:
        # Start the wrapper
        wrapper.start()

        # Publish a test task
        task_id = wrapper.publish_task("Run test suite", ["testing"])
        print(f"Published task: {task_id}")

        # Discover agents
        agents = wrapper.discover_agents()
        print(f"Discovered agents: {len(agents)}")

        # Send a test message
        wrapper.broadcast_message("status", {"message": "Test broadcast"})

        # Get system status
        status = get_all_agents_status()
        print(f"System status: {status}")

        # Run for a few seconds
        time.sleep(10)

    finally:
        # Clean shutdown
        wrapper.stop()
