#!/usr/bin/env python3
"""Debug worker to test message flow"""

# Allow direct script execution - add parent directory to sys.path
import os
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import json
import time
import traceback
from dataclasses import asdict
from datetime import datetime

# Use absolute imports with package name for __main__ compatibility
from orchestration.message_broker import MessageBroker, MessageType, TaskMessage

try:
    print("✅ Imports successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)


def main():
    agent_id = sys.argv[1] if len(sys.argv) > 1 else "debug-worker"
    print(f"\n=== Debug Worker {agent_id} Starting ===\n")

    try:
        broker = MessageBroker()
        print("✅ Connected to Redis")

        # Register agent
        broker.register_agent(agent_id, "debug", ["testing"])
        print(f"✅ Registered as {agent_id}")

        print("\n📥 Listening for tasks...\n")

        while True:
            # Check for tasks
            msg_data = broker.redis_client.brpop(f"queue:{agent_id}", timeout=2)

            if msg_data:
                _, raw_msg = msg_data
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Got message!")
                print(f"Raw: {raw_msg[:100]}...")

                try:
                    # Parse message
                    msg_dict = json.loads(raw_msg)
                    print(f"Type: {msg_dict.get('type')}")
                    print(f"From: {msg_dict.get('from_agent')}")
                    print(f"Task ID: {msg_dict.get('id')}")

                    # Process if it's a task
                    if msg_dict.get("type") in [
                        "task_assignment",
                        MessageType.TASK_ASSIGNMENT.value,
                    ]:
                        payload = msg_dict.get("payload", {})
                        task_desc = payload.get("description", "unknown")
                        task_id = msg_dict.get("id", "no-id")
                        print(f"Processing task '{task_desc}' (ID: {task_id}) from queue:queue:{agent_id}")

                        # Create result
                        result = {
                            "task_id": msg_dict.get("id"),
                            "original_task_id": payload.get("task_id", msg_dict.get("id")),
                            "status": "completed",
                            "result": f"Processed by {agent_id}: {payload.get('description')}",
                            "processed_by": agent_id,
                            "timestamp": datetime.now().isoformat(),
                        }

                        # Send result back
                        result_msg = TaskMessage(
                            id=f"result_{int(time.time())}",
                            type=MessageType.TASK_RESULT,
                            from_agent=agent_id,
                            to_agent=msg_dict.get("from_agent"),
                            timestamp=datetime.now().isoformat(),
                            payload=result,
                        )

                        result_dict = asdict(result_msg)
                        result_dict["type"] = result_msg.type.value

                        broker.redis_client.lpush(
                            f"queue:{msg_dict.get('from_agent')}",
                            json.dumps(result_dict),
                        )

                        print(f"✅ Sent result back to {msg_dict.get('from_agent')}")
                        print(f"   Result: {json.dumps(result, indent=2)}")

                except Exception as e:
                    print(f"❌ Error processing message: {e}")

                    traceback.print_exc()

            # Heartbeat
            broker.heartbeat(agent_id)
            print(".", end="", flush=True)

    except KeyboardInterrupt:
        print("\n\n👋 Worker shutting down...")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")

        traceback.print_exc()


if __name__ == "__main__":
    main()
