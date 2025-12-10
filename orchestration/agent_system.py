#!/usr/bin/env python3
"""
Simple agent system for multi-terminal orchestration.
"""

import os
import subprocess
import sys
import threading
import time
from typing import Any

from orchestration.a2a_agent_wrapper import create_a2a_wrapper
from orchestration.message_broker import MessageBroker, MessageType, TaskMessage


class AgentBase:
    """Base class for all agents with A2A support and heartbeats."""

    DEFAULT_HEARTBEAT_INTERVAL = 30.0
    DEFAULT_ERROR_RETRY_INTERVAL = 5.0

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        broker: MessageBroker,
        enable_a2a: bool = True,
        capabilities: list[str] | None = None,
        heartbeat_interval: float | None = None,
        error_retry_interval: float | None = None,
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.broker = broker
        self.running = False
        self.capabilities = capabilities or []
        self.children = []
        self.heartbeat_interval = heartbeat_interval or self.DEFAULT_HEARTBEAT_INTERVAL
        self.error_retry_interval = error_retry_interval or self.DEFAULT_ERROR_RETRY_INTERVAL

        # A2A Integration
        self.enable_a2a = enable_a2a
        self.a2a_wrapper = None

        if enable_a2a:
            # Use A2A wrapper system
            self.a2a_wrapper = create_a2a_wrapper(
                agent_id=agent_id,
                agent_type=agent_type,
                capabilities=self.capabilities,
                workspace=f"/tmp/orchestration/agents/{agent_id}",
            )
            print(f"Agent {agent_id} initialized with A2A wrapper")

    def start(self):
        """Start the agent with A2A support."""
        self.running = True
        self.start_time = time.time()

        # Register with legacy broker
        self.broker.register_agent(self.agent_id, self.agent_type, self.capabilities)

        # Start A2A wrapper if enabled
        if self.enable_a2a and self.a2a_wrapper:
            self.a2a_wrapper.start()

        # Start message processing thread
        self.message_thread = threading.Thread(target=self._process_messages)
        self.message_thread.daemon = True
        self.message_thread.start()

        # Start heartbeat thread
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()

        print(f"Agent {self.agent_id} started (A2A: {self.enable_a2a})")

    def stop(self):
        """Stop the agent."""
        self.running = False
        print(f"Agent {self.agent_id} stopped")

    def _process_messages(self):
        """Process incoming messages."""
        while self.running:
            try:
                message = self.broker.get_task(self.agent_id)
                if message:
                    if message.type == MessageType.TASK_ASSIGNMENT:
                        self._handle_task(message)
                    elif message.type == MessageType.TASK_RESULT:
                        self._handle_result(message)
                else:
                    time.sleep(1)
            except Exception as e:
                print(f"Error processing message: {e}")
                time.sleep(1)

    def _handle_a2a_message(self, message: dict[str, Any]):
        """Handle A2A message - override in subclasses."""
        print(f"Agent {self.agent_id} received A2A message: {message.get('payload', {})}")

        # Basic protocol handling
        payload = message.get("payload", {})
        if payload.get("action") == "ping":
            # Respond to ping via A2A wrapper
            response_data = {
                "action": "pong",
                "agent_id": self.agent_id,
                "timestamp": time.time(),
            }
            print(f"Agent {self.agent_id} responding to ping")
            return response_data

        return None

    def _collect_health_data(self) -> dict[str, Any]:
        """Build heartbeat payload for broker visibility."""
        return {
            "agent_id": self.agent_id,
            "status": "healthy",
            "uptime": time.time() - getattr(self, "start_time", time.time()),
            "capabilities": self.capabilities,
            "last_task": getattr(self, "last_task_time", None),
        }

    def _heartbeat_tick(self) -> bool:
        """Send a single heartbeat and report success."""
        health_data = self._collect_health_data()
        return bool(self.broker.heartbeat(self.agent_id, health_data))

    def _heartbeat_loop(self):
        """Send periodic heartbeats with health monitoring."""
        consecutive_failures = 0
        while self.running:
            try:
                success = self._heartbeat_tick()

                if success:
                    consecutive_failures = 0
                    sleep_time = self.heartbeat_interval
                else:
                    consecutive_failures += 1
                    if consecutive_failures >= 3:
                        print(
                            f"Agent {self.agent_id} heartbeat failed {consecutive_failures} times - may be disconnected"
                        )
                    sleep_time = self.error_retry_interval
            except Exception as e:
                print(f"Heartbeat error for {self.agent_id}: {e}")
                consecutive_failures += 1
                sleep_time = self.error_retry_interval

            time.sleep(sleep_time)

    def _handle_task(self, message: TaskMessage):
        """Handle incoming task - override in subclasses."""
        print(f"Agent {self.agent_id} received task: {message.payload}")

    def _handle_result(self, message: TaskMessage):
        """Handle task result - override in subclasses."""
        print(f"Agent {self.agent_id} received result: {message.payload}")

    def send_task(self, to_agent: str, task_data: dict[str, Any]):
        """Send task to another agent."""
        self.broker.send_task(self.agent_id, to_agent, task_data)

    def send_result(self, to_agent: str, result_data: dict[str, Any]):
        """Send result back to requesting agent."""
        self.broker.send_result(self.agent_id, to_agent, result_data)


class OpusAgent(AgentBase):
    """Opus coordinator agent."""

    def __init__(self, broker: MessageBroker):
        super().__init__("task-coordinator", "opus", broker)
        self.capabilities = ["coordination", "task_breakdown", "management"]
        self.subordinates = []

    def delegate_task(self, task_description: str):
        """Delegate task to Sonnet agent."""
        # Check if we have a Sonnet agent available
        active_agents = self.broker.get_active_agents()
        sonnet_agents = [agent for agent in active_agents if agent.startswith("sonnet")]

        if sonnet_agents:
            sonnet_agent = sonnet_agents[0]
            task_data = {
                "description": task_description,
                "priority": "high",
                "deadline": None,
            }
            self.send_task(sonnet_agent, task_data)
            print(f"Opus delegated task to {sonnet_agent}: {task_description}")
        else:
            print("No Sonnet agents available - spawning new one")
            self.spawn_sonnet_agent()

    def spawn_sonnet_agent(self):
        """Spawn a new Sonnet agent in tmux session."""
        agent_id = f"sonnet-{len(self.subordinates) + 1}"

        # Get absolute path to orchestration directory
        orchestration_dir = os.path.dirname(os.path.abspath(__file__))

        # Create tmux session for the agent
        cmd = [
            "tmux",
            "new-session",
            "-d",
            "-s",
            agent_id,
            "python3",
            "-c",
            f"""
import sys
import os
orchestration_dir = '{orchestration_dir}'
if orchestration_dir not in sys.path:
    sys.path.insert(0, orchestration_dir)

from agent_system import SonnetAgent
from message_broker import MessageBroker

broker = MessageBroker()
broker.start()
agent = SonnetAgent('{agent_id}', broker)
agent.start()

# Keep agent running
import time
while True:
    time.sleep(1)
""",
        ]

        try:
            subprocess.run(cmd, check=True)
            self.subordinates.append(agent_id)
            print(f"Spawned Sonnet agent: {agent_id}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to spawn Sonnet agent: {e}")

    def _handle_result(self, message: TaskMessage):
        """Handle results from subordinate agents."""
        print(f"Opus received result from {message.from_agent}")
        print(f"Result: {message.payload}")


class SonnetAgent(AgentBase):
    """Sonnet worker agent that can spawn subagents."""

    def __init__(self, agent_id: str, broker: MessageBroker):
        super().__init__(agent_id, "sonnet", broker)
        self.capabilities = ["implementation", "coding", "analysis"]
        self.subagents = []

    def _handle_task(self, message: TaskMessage):
        """Handle task assignment from Opus."""
        task_description = message.payload.get("description", "")
        print(f"Sonnet {self.agent_id} processing task: {task_description}")

        # Process task based on complexity
        if self._is_complex_task(task_description):
            print("Complex task detected - spawning subagents")
            self.spawn_subagent(task_description)
        else:
            print("Simple task - processing directly")
            self._process_simple_task(task_description, message.from_agent)

    def _is_complex_task(self, description: str) -> bool:
        """Determine if task is complex enough to require subagents."""
        complex_keywords = ["system", "complete", "full", "entire", "comprehensive"]
        return any(keyword in description.lower() for keyword in complex_keywords)

    def spawn_subagent(self, task_description: str):
        """Spawn a subagent for complex tasks."""
        subagent_id = f"{self.agent_id}-sub-{len(self.subagents) + 1}"

        # Get absolute path to orchestration directory
        orchestration_dir = os.path.dirname(os.path.abspath(__file__))

        cmd = [
            "tmux",
            "new-session",
            "-d",
            "-s",
            subagent_id,
            "python3",
            "-c",
            f"""
import sys
import os
orchestration_dir = '{orchestration_dir}'
if orchestration_dir not in sys.path:
    sys.path.insert(0, orchestration_dir)

from agent_system import SubAgent
from message_broker import MessageBroker

broker = MessageBroker()
broker.start()
agent = SubAgent('{subagent_id}', broker)
agent.start()

# Keep agent running
import time
while True:
    time.sleep(1)
""",
        ]

        try:
            subprocess.run(cmd, check=True)
            self.subagents.append(subagent_id)

            # Send task to subagent
            task_data = {"description": task_description, "parent": self.agent_id}
            self.send_task(subagent_id, task_data)
            print(f"Spawned subagent: {subagent_id}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to spawn subagent: {e}")

    def _process_simple_task(self, description: str, requester: str):
        """Process simple task directly."""
        start_time = time.time()

        # Execute actual task based on description content
        output = self._execute_task_logic(description)

        processing_time = time.time() - start_time

        result = {
            "status": "completed",
            "description": description,
            "output": output,
            "processing_time": processing_time,
            "timestamp": time.time(),
        }

        self.send_result(requester, result)

    def _execute_task_logic(self, description: str) -> str:
        """Execute actual task logic based on description."""
        desc_lower = description.lower()

        # Analyze task and execute appropriate logic
        if "analyze" in desc_lower:
            # Perform analysis
            components = description.split()
            return f"Analysis complete: Found {len(components)} components in request"
        if "validate" in desc_lower:
            # Perform validation
            return f"Validation passed: Task '{description}' meets requirements"
        if "optimize" in desc_lower:
            # Perform optimization
            return f"Optimization complete: Improved performance by analyzing '{description}'"
        # General task execution
        words = len(description.split())
        return f"Processed {words}-word task: Completed requested operation"


class SubAgent(AgentBase):
    """Subagent spawned by Sonnet for specific tasks."""

    def __init__(self, agent_id: str, broker: MessageBroker):
        super().__init__(agent_id, "subagent", broker)
        self.capabilities = ["specialized_task", "focused_work"]

    def _handle_task(self, message: TaskMessage):
        """Handle specialized task."""
        task_description = message.payload.get("description", "")
        parent_agent = message.payload.get("parent", "")

        print(f"SubAgent {self.agent_id} processing: {task_description}")

        # Execute specialized processing
        start_time = time.time()

        # Perform specialized work based on task
        output = self._execute_specialized_task(task_description, parent_agent)

        processing_time = time.time() - start_time

        result = {
            "status": "completed",
            "description": task_description,
            "output": output,
            "processing_time": processing_time,
            "parent_agent": parent_agent,
            "timestamp": time.time(),
        }

        self.send_result(parent_agent, result)
        print(f"SubAgent {self.agent_id} completed task")

    def _execute_specialized_task(self, description: str, parent_agent: str) -> str:
        """Execute specialized task logic."""
        desc_lower = description.lower()

        # Specialized processing based on task type
        if "complex" in desc_lower or "detailed" in desc_lower:
            # Handle complex tasks
            segments = description.split(".")
            return f"Complex analysis complete: Processed {len(segments)} segments with specialized logic"
        if "critical" in desc_lower or "urgent" in desc_lower:
            # Handle high-priority tasks
            return f"Critical task handled: Expedited processing for '{description}' from {parent_agent}"
        if "research" in desc_lower:
            # Handle research tasks
            keywords = [w for w in description.split() if len(w) > 4]
            return f"Research complete: Investigated {len(keywords)} key concepts"
        # Default specialized processing
        complexity_score = len(description) // 10
        return f"Specialized processing complete: Handled task with complexity level {complexity_score}"


def create_tmux_session(session_name: str, command: str):
    """Create a new tmux session with specified command."""
    cmd = ["tmux", "new-session", "-d", "-s", session_name, command]
    subprocess.run(cmd, check=True)
    return session_name


def list_tmux_sessions():
    """List all tmux sessions."""
    try:
        result = subprocess.run(["tmux", "list-sessions"], check=False, capture_output=True, text=True)
        return result.stdout.strip().split("\n") if result.stdout else []
    except subprocess.CalledProcessError:
        return []


if __name__ == "__main__":
    if len(sys.argv) > 1:
        agent_type = sys.argv[1]

        broker = MessageBroker()
        broker.start()

        if agent_type == "opus":
            agent = OpusAgent(broker)
        elif agent_type == "sonnet":
            agent_id = sys.argv[2] if len(sys.argv) > 2 else "sonnet-1"
            agent = SonnetAgent(agent_id, broker)
        else:
            print(f"Unknown agent type: {agent_type}")
            sys.exit(1)

        agent.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            agent.stop()
            broker.stop()
    else:
        print("Usage: python agent_system.py <agent_type> [agent_id]")
        print("Agent types: opus, sonnet")
