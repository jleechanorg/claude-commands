#!/usr/bin/env python3
"""Test A2A bridge with debug worker"""

import asyncio
import subprocess
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from redis_a2a_bridge import RedisA2ABridge


async def test_with_debug_worker():
    """Test A2A with a debug worker"""
    print("=== Testing A2A Bridge with Debug Worker ===\n")

    # Start debug worker
    print("1. Starting debug worker...")
    worker_proc = subprocess.Popen(
        ["python3", "debug_worker.py", "test-worker-debug"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    # Give it time to start
    time.sleep(2)

    try:
        # Initialize bridge
        bridge = RedisA2ABridge()
        bridge.task_timeout = 5.0  # Short timeout for testing

        # Check agents
        print("\n2. Discovering agents...")
        agents = await bridge.discover_agents_real()
        print(f"   Found {len(agents)} agents")

        debug_agent = None
        for agent in agents:
            print(f"   - {agent['id']} (type: {agent['type']})")
            if agent['id'] == 'test-worker-debug':
                debug_agent = agent

        if not debug_agent:
            print("❌ Debug worker not found in agent list!")
            return False

        # Send task
        print("\n3. Sending task via A2A bridge...")

        try:
            result = await bridge.execute_task_real(
                task_description="Test task via A2A bridge",
                context_id="a2a-test-123",
                target_agent="test-worker-debug"
            )

            print(f"\n✅ Task completed successfully!")
            print(f"   Status: {result.get('status')}")
            print(f"   Result: {result.get('result')}")
            print(f"   Processed by: {result.get('processed_by')}")

            return result.get('status') == 'completed'

        except asyncio.TimeoutError:
            print(f"\n❌ Task timed out!")

            # Get worker output
            print("\n4. Worker output:")
            worker_output = []
            while True:
                line = worker_proc.stdout.readline()
                if not line:
                    break
                worker_output.append(line.strip())
                print(f"   {line.strip()}")

            return False

    finally:
        # Kill worker
        worker_proc.terminate()
        worker_proc.wait()
        print("\n✅ Cleaned up worker process")


async def main():
    success = await test_with_debug_worker()

    if success:
        print("\n🎉 A2A Bridge is working correctly!")
    else:
        print("\n❌ A2A Bridge test failed")

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
