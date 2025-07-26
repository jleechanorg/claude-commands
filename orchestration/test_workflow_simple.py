#!/usr/bin/env python3
"""Simple workflow test with one worker"""

import asyncio
import subprocess
import time
import sys
import os

import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from redis_a2a_bridge import RedisA2ABridge


async def test_simple_workflow():
    """Test workflow with a single debug worker"""
    print("=== Testing Simple Workflow ===\n")

    # Start one debug worker
    print("1. Starting debug worker...")
    worker_proc = subprocess.Popen(
        ["python3", "debug_worker.py", "workflow-test-worker"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    time.sleep(2)

    try:
        bridge = RedisA2ABridge()
        bridge.task_timeout = 5.0

        # Simple workflow
        print("\n2. Creating simple workflow...")
        result = await bridge.orchestrate_workflow_real(
            workflow_description="Test the system",  # Will create one "test" step
            context_id="simple-workflow-test"
        )

        print(f"\n✅ Workflow result:")
        print(f"   ID: {result['workflow_id']}")
        print(f"   Status: {result['status']}")
        print(f"   Steps: {result['steps_completed']}/{result['total_steps']}")

        # Show results
        for step_id, step_result in result['results'].items():
            print(f"\n   {step_id}:")
            print(f"     Status: {step_result.get('status')}")
            if step_result.get('status') == 'completed':
                print(f"     Result: {step_result.get('result')}")
            else:
                print(f"     Error: {step_result.get('error')}")

        return result['status'] == 'completed'

    except Exception as e:
        print(f"\n❌ Error: {e}")

        traceback.print_exc()

        # Show worker output
        print("\nWorker output:")
        while True:
            line = worker_proc.stdout.readline()
            if not line:
                break
            print(f"  {line.strip()}")

        return False

    finally:
        worker_proc.terminate()
        worker_proc.wait()


if __name__ == "__main__":
    success = asyncio.run(test_simple_workflow())
    print(f"\n{'✅ Success!' if success else '❌ Failed'}")
    sys.exit(0 if success else 1)
