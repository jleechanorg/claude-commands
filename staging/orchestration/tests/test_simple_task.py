#!/usr/bin/env python3
"""Simple test to verify task sending works"""

import json
import os
import sys
import time
from dataclasses import asdict
from datetime import datetime

from orchestration.message_broker import MessageBroker, MessageType, TaskMessage

# Ensure imports work for direct execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def test_simple_flow():
    """Test basic task flow"""
    broker = MessageBroker()

    # Check if Redis is available
    try:
        if not hasattr(broker, "redis_client") or broker.redis_client is None:
            print("⚠️  Redis client not available - skipping Redis-specific test")
            print("✅ Test skipped gracefully (file-based broker in use)")
            return True  # Return True for graceful skip
        # Test Redis connectivity
        broker.redis_client.ping()
    except Exception as e:
        print(f"⚠️  Redis not available: {e}")
        print("✅ Test skipped gracefully (Redis not accessible)")
        return True  # Return True for graceful skip

    print("=== Simple Task Flow Test ===\n")

    # 1. Send a task to test-worker-1
    print("1. Sending task to test-worker-1...")

    task_id = f"simple_test_{int(time.time())}"
    task_message = TaskMessage(
        id=task_id,
        type=MessageType.TASK_ASSIGNMENT,
        from_agent="test_sender",
        to_agent="test-worker-1",
        timestamp=datetime.now().isoformat(),
        payload={"description": "Simple test task", "task_id": task_id},
    )

    # Send directly
    task_dict = asdict(task_message)
    task_dict["type"] = task_message.type.value  # Convert enum

    broker.redis_client.lpush("queue:test-worker-1", json.dumps(task_dict))
    print(f"   Task {task_id} sent to queue:test-worker-1")

    # 2. Wait a bit and check for response
    print("\n2. Waiting for response...")

    for i in range(10):
        # Check test_sender queue for response
        response = broker.redis_client.brpop("queue:test_sender", timeout=1)

        if response:
            _, msg_data = response
            msg = json.loads(msg_data)
            print("\n✅ Got response!")
            print(f"   Type: {msg.get('type')}")
            print(f"   From: {msg.get('from_agent')}")
            print(f"   Payload: {json.dumps(msg.get('payload'), indent=2)}")
            return True

        print(f"   Waiting... ({i + 1}/10)")

    print("\n❌ No response received after 10 seconds")

    # Debug
    print("\n3. Checking queues...")

    # Check if task is still in queue
    worker_queue = broker.redis_client.lrange("queue:test-worker-1", 0, -1)
    print(f"   queue:test-worker-1 has {len(worker_queue)} messages")

    # Check test_sender queue
    sender_queue = broker.redis_client.lrange("queue:test_sender", 0, -1)
    print(f"   queue:test_sender has {len(sender_queue)} messages")

    return False


if __name__ == "__main__":
    success = test_simple_flow()
    sys.exit(0 if success else 1)
