#!/usr/bin/env python3
"""
Simple test agent that processes tasks and returns results.
Used to verify A2A integration functionality.
"""

import time
import json
from message_broker import MessageBroker, MessageType

import sys

class TestWorkerAgent:
    """Test agent that processes tasks and returns results"""
    
    def __init__(self, agent_id="test-worker"):
        self.agent_id = agent_id
        self.broker = MessageBroker()
        self.running = False
        
    def start(self):
        """Start the test agent"""
        # Register with broker
        self.broker.register_agent(
            self.agent_id, 
            "test", 
            ["task_execution", "testing"]
        )
        
        print(f"Test worker {self.agent_id} started")
        self.running = True
        
        # Process messages
        while self.running:
            try:
                # Get task from queue
                message = self.broker.get_task(self.agent_id)
                
                if message:
                    print(f"Test worker received task: {message.payload}")
                    print(f"Message type: {message.type} (type: {type(message.type)})")
                    
                    # Handle both enum and string types
                    if (message.type == MessageType.TASK_ASSIGNMENT or 
                        message.type == MessageType.TASK_ASSIGNMENT.value):
                        # Process the task
                        result = self._process_task(message)
                        
                        # Send result back with proper task correlation
                        self.broker.send_result(
                            self.agent_id,
                            message.from_agent,
                            result
                        )
                        print(f"Test worker sent result back to {message.from_agent}: {result}")
                
                # Send heartbeat
                self.broker.heartbeat(self.agent_id)
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Test worker error: {e}")
                time.sleep(1)
                
        print(f"Test worker {self.agent_id} stopped")
        
    def _process_task(self, message):
        """Process a task and return result"""
        task_data = message.payload
        
        # Simulate some work
        time.sleep(0.5)
        
        # Return result with task_id for correlation
        return {
            "task_id": message.id,
            "original_task_id": message.id,
            "status": "completed",
            "result": f"Processed: {task_data.get('description', 'Unknown task')}",
            "processed_by": self.agent_id,
            "timestamp": time.time()
        }

if __name__ == "__main__":

    
    agent_id = sys.argv[1] if len(sys.argv) > 1 else "test-worker"
    agent = TestWorkerAgent(agent_id)
    
    try:
        agent.start()
    except KeyboardInterrupt:
        print("\nStopping test worker...")
        agent.running = False