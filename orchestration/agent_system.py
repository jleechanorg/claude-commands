#!/usr/bin/env python3
"""
Simple agent system for multi-terminal orchestration.
"""

import os
import subprocess
import threading
import time
import json
from typing import Dict, List, Optional, Any
from message_broker import MessageBroker, TaskMessage, MessageType


class AgentBase:
    """Base class for all agents."""
    
    def __init__(self, agent_id: str, agent_type: str, broker: MessageBroker):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.broker = broker
        self.running = False
        self.capabilities = []
        self.children = []
        
    def start(self):
        """Start the agent."""
        self.running = True
        self.broker.register_agent(self.agent_id, self.agent_type, self.capabilities)
        
        # Start message processing thread
        self.message_thread = threading.Thread(target=self._process_messages)
        self.message_thread.daemon = True
        self.message_thread.start()
        
        # Start heartbeat thread
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()
        
        print(f"Agent {self.agent_id} started")
        
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
                
    def _heartbeat_loop(self):
        """Send periodic heartbeats."""
        while self.running:
            self.broker.heartbeat(self.agent_id)
            time.sleep(30)
            
    def _handle_task(self, message: TaskMessage):
        """Handle incoming task - override in subclasses."""
        print(f"Agent {self.agent_id} received task: {message.payload}")
        
    def _handle_result(self, message: TaskMessage):
        """Handle task result - override in subclasses."""
        print(f"Agent {self.agent_id} received result: {message.payload}")
        
    def send_task(self, to_agent: str, task_data: Dict[str, Any]):
        """Send task to another agent."""
        self.broker.send_task(self.agent_id, to_agent, task_data)
        
    def send_result(self, to_agent: str, result_data: Dict[str, Any]):
        """Send result back to requesting agent."""
        self.broker.send_result(self.agent_id, to_agent, result_data)


class OpusAgent(AgentBase):
    """Opus master coordinator agent."""
    
    def __init__(self, broker: MessageBroker):
        super().__init__("opus-master", "opus", broker)
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
                "deadline": None
            }
            self.send_task(sonnet_agent, task_data)
            print(f"Opus delegated task to {sonnet_agent}: {task_description}")
        else:
            print("No Sonnet agents available - spawning new one")
            self.spawn_sonnet_agent()
            
    def spawn_sonnet_agent(self):
        """Spawn a new Sonnet agent in tmux session."""
        agent_id = f"sonnet-{len(self.subordinates) + 1}"
        
        # Create tmux session for the agent
        cmd = [
            "tmux", "new-session", "-d", "-s", agent_id,
            "python3", "-c", f"""
import sys
sys.path.append('.')
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
"""
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
        
        # Simulate task processing
        if self._is_complex_task(task_description):
            print(f"Complex task detected - spawning subagents")
            self.spawn_subagent(task_description)
        else:
            print(f"Simple task - processing directly")
            self._process_simple_task(task_description, message.from_agent)
            
    def _is_complex_task(self, description: str) -> bool:
        """Determine if task is complex enough to require subagents."""
        complex_keywords = ["system", "complete", "full", "entire", "comprehensive"]
        return any(keyword in description.lower() for keyword in complex_keywords)
        
    def spawn_subagent(self, task_description: str):
        """Spawn a subagent for complex tasks."""
        subagent_id = f"{self.agent_id}-sub-{len(self.subagents) + 1}"
        
        cmd = [
            "tmux", "new-session", "-d", "-s", subagent_id,
            "python3", "-c", f"""
import sys
sys.path.append('.')
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
"""
        ]
        
        try:
            subprocess.run(cmd, check=True)
            self.subagents.append(subagent_id)
            
            # Send task to subagent
            task_data = {
                "description": task_description,
                "parent": self.agent_id
            }
            self.send_task(subagent_id, task_data)
            print(f"Spawned subagent: {subagent_id}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to spawn subagent: {e}")
            
    def _process_simple_task(self, description: str, requester: str):
        """Process simple task directly."""
        # Simulate work
        time.sleep(2)
        
        result = {
            "status": "completed",
            "description": description,
            "output": f"Task completed by {self.agent_id}",
            "timestamp": time.time()
        }
        
        self.send_result(requester, result)


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
        
        # Simulate specialized work
        time.sleep(3)
        
        result = {
            "status": "completed", 
            "description": task_description,
            "output": f"Specialized task completed by {self.agent_id}",
            "timestamp": time.time()
        }
        
        self.send_result(parent_agent, result)
        print(f"SubAgent {self.agent_id} completed task")


def create_tmux_session(session_name: str, command: str):
    """Create a new tmux session with specified command."""
    cmd = ["tmux", "new-session", "-d", "-s", session_name, command]
    subprocess.run(cmd, check=True)
    return session_name


def list_tmux_sessions():
    """List all tmux sessions."""
    try:
        result = subprocess.run(["tmux", "list-sessions"], capture_output=True, text=True)
        return result.stdout.strip().split('\n') if result.stdout else []
    except subprocess.CalledProcessError:
        return []


if __name__ == "__main__":
    import sys
    
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