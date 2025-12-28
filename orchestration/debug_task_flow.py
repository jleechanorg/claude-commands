#!/usr/bin/env python3
"""Debug task flow between A2A bridge and worker"""

# Allow direct script execution - add parent directory to sys.path
import os
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import json

# Use absolute imports with package name for __main__ compatibility
from orchestration.message_broker import MessageBroker


def debug_queue_contents():
    broker = MessageBroker()

    # Check what's in the queues
    print("=== Queue Analysis ===")

    # Check test-worker-1 queue
    queue_contents = broker.redis_client.lrange("queue:test-worker-1", 0, -1)
    print(f"\nqueue:test-worker-1 has {len(queue_contents)} messages")

    for i, msg in enumerate(queue_contents):
        try:
            data = json.loads(msg)
            print(f"\nMessage {i}:")
            print(f"  Type: {data.get('type')}")
            print(f"  From: {data.get('from_agent')}")
            print(f"  To: {data.get('to_agent')}")
            print(f"  ID: {data.get('id')}")
            print(f"  Payload: {data.get('payload')}")
        except Exception as e:
            print(f"  Error parsing message {i}: {e}")

    # Check a2a_bridge queue
    bridge_queue = broker.redis_client.lrange("queue:a2a_bridge", 0, -1)
    print(f"\nqueue:a2a_bridge has {len(bridge_queue)} messages")

    for i, msg in enumerate(bridge_queue):
        try:
            data = json.loads(msg)
            print(f"\nMessage {i}:")
            print(f"  Type: {data.get('type')}")
            print(f"  From: {data.get('from_agent')}")
            print(f"  Result: {data.get('payload')}")
        except Exception as e:
            print(f"  Error parsing message {i}: {e}")


if __name__ == "__main__":
    debug_queue_contents()
